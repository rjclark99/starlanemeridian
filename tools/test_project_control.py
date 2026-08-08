import copy
import unittest

from tools import validate_project_control as control


class ProjectControlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.control_dir = control.ROOT / "docs" / "project-control"
        role_data = control.load_json(cls.control_dir / "roles.json")
        cls.roles, role_errors = control.validate_roles(role_data)
        if role_errors:
            raise AssertionError(role_errors)
        cls.known_ids = control.knowledge_ids()
        cls.schema = control.load_json(cls.control_dir / "task-packet.schema.json")
        cls.release_packet = control.load_json(
            cls.control_dir / "examples" / "pilot-release-readiness-task.json"
        )

    def test_repository_control_files_validate(self):
        self.assertEqual([], control.validate())

    def test_publication_requires_scoped_owner_approval(self):
        packet = copy.deepcopy(self.release_packet)
        packet["task_id"] = "test.publish"
        packet["task_class"] = "publish"
        packet["affected_state"] = "public-release"
        packet["specialist_role"] = "publication_executor"
        packet["owner_approval_required"] = True
        packet["owner_approval"] = {"status": "pending", "scope": "", "evidence": ""}
        errors = control.validate_packet(packet, self.roles, self.known_ids, self.schema)
        self.assertTrue(any("requires explicit approved owner authority" in error for error in errors))

        packet["owner_approval"] = {
            "status": "approved",
            "scope": "Publish only the named verified draft assets.",
            "evidence": "Owner approval recorded in the initiating task.",
        }
        errors = control.validate_packet(packet, self.roles, self.known_ids, self.schema)
        self.assertEqual([], errors)

    def test_read_only_security_role_cannot_implement(self):
        packet = copy.deepcopy(self.release_packet)
        packet["task_id"] = "test.security-write"
        packet["task_class"] = "implement"
        packet["specialist_role"] = "security_reviewer"
        errors = control.validate_packet(packet, self.roles, self.known_ids, self.schema)
        self.assertTrue(any("does not accept task class" in error for error in errors))
        self.assertTrue(any("read-only role" in error for error in errors))

    def test_invalid_board_transition_is_rejected(self):
        errors = control.validate_history(["proposed", "active"], "active", "test")
        self.assertTrue(any("invalid transition" in error for error in errors))

    def test_path_overlap_is_conservative(self):
        self.assertTrue(control.paths_overlap("kodi/skin.starlane.movies", "kodi/skin.starlane.movies/xml"))
        self.assertFalse(control.paths_overlap("android-app", "control-api"))


if __name__ == "__main__":
    unittest.main()
