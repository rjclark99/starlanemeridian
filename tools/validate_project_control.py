"""Validate the repository-native Starlane Project Control system."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
CONTROL = ROOT / "docs" / "project-control"

FILE_BUDGETS = {
    ROOT / "AGENTS.md": 16_000,
    CONTROL / "README.md": 14_000,
    CONTROL / "roles.json": 24_000,
}
TASK_FILE_BUDGET = 10_000
RESULT_FILE_BUDGET = 7_000

STATUSES = {"proposed", "ready", "active", "blocked", "review", "complete"}
TRANSITIONS = {
    "proposed": {"ready", "blocked"},
    "ready": {"active", "blocked"},
    "active": {"blocked", "review"},
    "blocked": {"ready", "active"},
    "review": {"active", "complete", "blocked"},
    "complete": set(),
}
READ_ONLY_POLICIES = {"read-only"}
EXTERNAL_CLASSES = {"deploy", "publish"}


class ValidationFailure(RuntimeError):
    """Raised for a malformed control file that cannot be inspected further."""


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationFailure(f"{path.relative_to(ROOT)}: {exc}") from exc


def knowledge_ids(root: Path = ROOT) -> set[str]:
    index = (root / "docs" / "agent-knowledge" / "index.yaml").read_text(encoding="utf-8")
    return set(re.findall(r"^\s*- id:\s*([^\s#]+)", index, flags=re.MULTILINE))


def word_count(value: Any) -> int:
    return len(re.findall(r"\b[\w.-]+\b", json.dumps(value, ensure_ascii=False)))


def validate_history(history: Any, current: Any, label: str = "history") -> list[str]:
    errors: list[str] = []
    if not isinstance(history, list) or not history:
        return [f"{label}: history must be a non-empty list"]
    if any(state not in STATUSES for state in history):
        errors.append(f"{label}: history contains an invalid status")
    for previous, following in zip(history, history[1:]):
        if following not in TRANSITIONS.get(previous, set()):
            errors.append(f"{label}: invalid transition {previous!r} -> {following!r}")
    if history[-1] != current:
        errors.append(f"{label}: current status {current!r} does not match final history entry")
    return errors


def path_root(pattern: str) -> str:
    normalized = pattern.replace("\\", "/").strip("/")
    wildcard = min((normalized.find(char) for char in "*?[" if char in normalized), default=len(normalized))
    return normalized[:wildcard].rstrip("/")


def paths_overlap(left: str, right: str) -> bool:
    left_root = path_root(left).casefold()
    right_root = path_root(right).casefold()
    if not left_root or not right_root:
        return True
    return (
        left_root == right_root
        or left_root.startswith(right_root + "/")
        or right_root.startswith(left_root + "/")
    )


def validate_packet(
    packet: dict[str, Any],
    roles: dict[str, dict[str, Any]],
    known_ids: set[str],
    schema: dict[str, Any],
    label: str = "task packet",
) -> list[str]:
    errors = [f"{label}: {error.message}" for error in Draft202012Validator(schema).iter_errors(packet)]
    if errors:
        return errors

    role_id = packet["specialist_role"]
    role = roles.get(role_id)
    if role is None:
        errors.append(f"{label}: unknown specialist role {role_id!r}")
        return errors

    task_class = packet["task_class"]
    if task_class not in role["task_classes"]:
        errors.append(f"{label}: role {role_id!r} does not accept task class {task_class!r}")
    if role["mutation_policy"] in READ_ONLY_POLICIES and task_class == "implement":
        errors.append(f"{label}: read-only role {role_id!r} cannot implement")

    missing_refs = sorted(set(packet["knowledge_references"]) - known_ids)
    if missing_refs:
        errors.append(f"{label}: unknown knowledge references: {', '.join(missing_refs)}")

    budget = packet["context_budget"]
    if word_count(packet) > budget["max_packet_words"]:
        errors.append(f"{label}: packet exceeds its {budget['max_packet_words']}-word budget")
    if len(packet["knowledge_references"]) > budget["max_topic_records"]:
        errors.append(f"{label}: knowledge references exceed the packet context budget")

    unsafe_paths = [
        path for path in packet["allowed_paths"]
        if Path(path).is_absolute() or path.startswith("..") or ".secrets" in path.split("/")
    ]
    if unsafe_paths:
        errors.append(f"{label}: unsafe or secret allowed paths: {', '.join(unsafe_paths)}")

    approval = packet["owner_approval"]
    if packet["owner_approval_required"]:
        if approval["status"] not in {"pending", "approved"}:
            errors.append(f"{label}: required owner approval must be pending or approved")
    elif approval["status"] != "not-required":
        errors.append(f"{label}: non-required approval must use status 'not-required'")

    if approval["status"] == "approved" and (not approval["scope"].strip() or not approval["evidence"].strip()):
        errors.append(f"{label}: approved authority requires non-empty scope and evidence")

    if task_class in EXTERNAL_CLASSES:
        if not packet["owner_approval_required"] or approval["status"] != "approved":
            errors.append(f"{label}: {task_class} requires explicit approved owner authority")
        if role_id != "publication_executor":
            errors.append(f"{label}: {task_class} must use the publication_executor role")

    if role_id == "publication_executor" and task_class not in EXTERNAL_CLASSES:
        errors.append(f"{label}: publication_executor is reserved for deploy or publish")

    return errors


def validate_roles(data: Any) -> tuple[dict[str, dict[str, Any]], list[str]]:
    errors: list[str] = []
    if not isinstance(data, dict) or not isinstance(data.get("roles"), list):
        return {}, ["roles.json: roles must be a list"]
    if data.get("default_specialists") != 1:
        errors.append("roles.json: default_specialists must be 1")
    maximum = data.get("maximum_specialists")
    if not isinstance(maximum, int) or not 1 <= maximum <= 3:
        errors.append("roles.json: maximum_specialists must be between 1 and 3")
    roles: dict[str, dict[str, Any]] = {}
    required = {"id", "title", "model_policy", "mutation_policy", "task_classes", "purpose", "prohibited"}
    for index, role in enumerate(data["roles"]):
        label = f"roles.json role {index}"
        if not isinstance(role, dict) or not required.issubset(role):
            errors.append(f"{label}: missing required fields")
            continue
        role_id = role["id"]
        if role_id in roles:
            errors.append(f"{label}: duplicate role id {role_id!r}")
        if role["model_policy"] not in {"balanced", "frontier"}:
            errors.append(f"{label}: invalid model policy")
        roles[role_id] = role
    for required_role in {"feature_implementer", "security_reviewer", "release_steward", "publication_executor"}:
        if required_role not in roles:
            errors.append(f"roles.json: missing required role {required_role!r}")
    return roles, errors


def validate_board(data: Any, roles: dict[str, dict[str, Any]], root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict) or not isinstance(data.get("items"), list):
        return ["board.json: items must be a list"]
    seen: set[str] = set()
    active_writers: list[tuple[str, str]] = []
    for item in data["items"]:
        item_id = item.get("id", "<missing>") if isinstance(item, dict) else "<invalid>"
        label = f"board item {item_id}"
        if not isinstance(item, dict):
            errors.append(f"{label}: item must be an object")
            continue
        required = {"id", "title", "priority", "status", "task_class", "affected_state", "role", "packet", "writer_paths", "history", "summary"}
        if not required.issubset(item):
            errors.append(f"{label}: missing required fields")
            continue
        if item_id in seen:
            errors.append(f"{label}: duplicate id")
        seen.add(item_id)
        if item["priority"] not in {"critical", "high", "normal", "low"}:
            errors.append(f"{label}: invalid priority {item['priority']!r}")
        if item["role"] not in roles:
            errors.append(f"{label}: unknown role {item['role']!r}")
        errors.extend(validate_history(item["history"], item["status"], label))
        packet_path = item["packet"]
        if packet_path is not None and not (root / packet_path).is_file():
            errors.append(f"{label}: packet path does not exist: {packet_path}")
        if item["status"] in {"active", "review"}:
            role = roles.get(item["role"], {})
            if role.get("mutation_policy") not in READ_ONLY_POLICIES:
                active_writers.extend((item_id, path) for path in item["writer_paths"])
    for index, (left_id, left_path) in enumerate(active_writers):
        for right_id, right_path in active_writers[index + 1:]:
            if left_id != right_id and paths_overlap(left_path, right_path):
                errors.append(
                    f"board.json: active writers {left_id!r} and {right_id!r} overlap at {left_path!r}/{right_path!r}"
                )
    return errors


def validate(root: Path = ROOT) -> list[str]:
    control = root / "docs" / "project-control"
    errors: list[str] = []

    for original_path, budget in FILE_BUDGETS.items():
        path = root / original_path.relative_to(ROOT)
        if not path.is_file():
            errors.append(f"missing required file: {path.relative_to(root)}")
        elif path.stat().st_size > budget:
            errors.append(f"{path.relative_to(root)} exceeds {budget} bytes")

    required_paths = [
        control / "roles.json", control / "board.json", control / "task-packet.schema.json",
        control / "result.schema.json", control / "active" / "README.md", control / "archive" / "README.md",
        control / "TASK_PACKET_TEMPLATE.md", control / "RESULT_TEMPLATE.md", control / "EVIDENCE_LEDGER_TEMPLATE.md",
        control / "efficiency-baseline.json",
    ]
    for path in required_paths:
        if not path.is_file():
            errors.append(f"missing required file: {path.relative_to(root)}")
    if errors:
        return errors

    try:
        role_data = load_json(control / "roles.json")
        board_data = load_json(control / "board.json")
        task_schema = load_json(control / "task-packet.schema.json")
        result_schema = load_json(control / "result.schema.json")
        efficiency = load_json(control / "efficiency-baseline.json")
        known_ids = knowledge_ids(root)
    except ValidationFailure as exc:
        return [str(exc)]

    roles, role_errors = validate_roles(role_data)
    errors.extend(role_errors)
    errors.extend(validate_board(board_data, roles, root))

    try:
        legacy_total = efficiency["legacy_workflow"]["total_bytes"]
        new_total = efficiency["new_sample_workflow"]["total_bytes"]
        measured_reduction = efficiency["reduction_percent"]
        calculated_reduction = round((1 - (new_total / legacy_total)) * 100, 1)
        if measured_reduction != calculated_reduction:
            errors.append("efficiency-baseline.json: reduction_percent does not match totals")
        if measured_reduction < 50:
            errors.append("efficiency-baseline.json: startup byte reduction is below 50 percent")
    except (KeyError, TypeError, ZeroDivisionError):
        errors.append("efficiency-baseline.json: malformed measurement")

    task_ids: set[str] = set()
    result_ids: set[str] = set()
    for path in sorted(control.glob("**/*-task.json")):
        if path.stat().st_size > TASK_FILE_BUDGET:
            errors.append(f"{path.relative_to(root)} exceeds {TASK_FILE_BUDGET} bytes")
            continue
        try:
            packet = load_json(path)
        except ValidationFailure as exc:
            errors.append(str(exc))
            continue
        label = str(path.relative_to(root))
        errors.extend(validate_packet(packet, roles, known_ids, task_schema, label))
        task_id = packet.get("task_id") if isinstance(packet, dict) else None
        if task_id in task_ids:
            errors.append(f"{label}: duplicate task id {task_id!r}")
        if isinstance(task_id, str):
            task_ids.add(task_id)

    validator = Draft202012Validator(result_schema)
    for path in sorted(control.glob("**/*-result.json")):
        if path.stat().st_size > RESULT_FILE_BUDGET:
            errors.append(f"{path.relative_to(root)} exceeds {RESULT_FILE_BUDGET} bytes")
            continue
        try:
            result = load_json(path)
        except ValidationFailure as exc:
            errors.append(str(exc))
            continue
        label = str(path.relative_to(root))
        errors.extend(f"{label}: {error.message}" for error in validator.iter_errors(result))
        task_id = result.get("task_id") if isinstance(result, dict) else None
        if task_id in result_ids:
            errors.append(f"{label}: duplicate result for task {task_id!r}")
        if isinstance(task_id, str):
            result_ids.add(task_id)

    for result_id in sorted(result_ids - task_ids):
        errors.append(f"result {result_id!r} has no matching task packet")
    for example_task in sorted(task_ids):
        if example_task.startswith("pilot.") and example_task not in result_ids:
            errors.append(f"pilot task {example_task!r} has no result")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    errors = validate()
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("Project control validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
