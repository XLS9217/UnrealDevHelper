from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from unreal_dev_helper.application import RESULT_MARKER, UnrealApplication


class FakeBackend:
    def __init__(self) -> None:
        self.commands: list[tuple[str, str | None]] = []

    def discover(self, wait_seconds: float = 1.5):
        return [{"node_id": "editor-1", "project_name": "Example"}]

    def execute(self, command: str, *, node_id=None, wait_seconds: float = 2.0):
        self.commands.append((command, node_id))
        payload = json.dumps({"answer": 42})
        return {
            "success": True,
            "command": f'MARKER = "{RESULT_MARKER}"',
            "output": [f"LogPython: {RESULT_MARKER}{payload}"],
        }


class UnrealApplicationTests(unittest.TestCase):
    def test_status_wraps_discovered_nodes(self):
        app = UnrealApplication(FakeBackend())

        result = app.status()

        self.assertTrue(result["connected"])
        self.assertEqual(result["nodes"][0]["node_id"], "editor-1")

    def test_blueprint_info_loads_reviewed_script_and_injects_variables(self):
        backend = FakeBackend()
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            scripts_dir = Path(directory)
            script = scripts_dir / "blueprint_info.py"
            script.write_text("unreal.log('query')", encoding="utf-8")
            app = UnrealApplication(backend, scripts_dir=scripts_dir)

            result = app.blueprint_info(
                "/Game/BP_Test",
                node_id="editor-1",
            )

        self.assertEqual(result, {"answer": 42})
        self.assertIn("BLUEPRINT_PATH = '/Game/BP_Test'", backend.commands[0][0])
        self.assertIn("unreal.log('query')", backend.commands[0][0])
        self.assertEqual(backend.commands[0][1], "editor-1")

    def test_execute_python_supports_read_only_agent_queries(self):
        backend = FakeBackend()
        app = UnrealApplication(backend)

        app.execute_python("import unreal; unreal.log('inspect')", node_id="editor-1")

        self.assertIn("unreal.log('inspect')", backend.commands[0][0])
        self.assertEqual(backend.commands[0][1], "editor-1")
        self.assertFalse(hasattr(app, "run_script"))


if __name__ == "__main__":
    unittest.main()
