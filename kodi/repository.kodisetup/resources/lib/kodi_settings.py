"""Small, testable Kodi userdata edits used by the bootstrap service."""

import os
from xml.etree import ElementTree


def disable_core_splash(path):
    """Set only advancedsettings/splash=false and preserve every other node."""
    if os.path.exists(path):
        tree = ElementTree.parse(path)
        root = tree.getroot()
        if root.tag != "advancedsettings":
            raise ValueError("advancedsettings.xml has an unexpected root")
    else:
        root = ElementTree.Element("advancedsettings")
        tree = ElementTree.ElementTree(root)
    splash = root.find("splash")
    if splash is None:
        splash = ElementTree.SubElement(root, "splash")
    if splash.text == "false":
        return False
    splash.text = "false"
    ElementTree.indent(tree)
    temporary = path + ".starlane-meridian.tmp"
    tree.write(temporary, encoding="utf-8", xml_declaration=True)
    os.replace(temporary, path)
    return True
