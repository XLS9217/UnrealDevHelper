from __future__ import annotations

import unittest

from unreal_dev_helper.server import dispatch_request


class FakeApplication:
    def status(self, wait_seconds=1.5):
        return {"connected": True, "wait_seconds": wait_seconds}

    def blueprint_info(self, asset_path, **options):
        return {"asset_path": asset_path, "options": options}


class ServerDispatchTests(unittest.TestCase):
    def test_health_reports_ready(self):
        result = dispatch_request(
            {"operation": "health"},
            FakeApplication(),
        )

        self.assertTrue(result["ready"])

    def test_dispatches_allowlisted_blueprint_operation(self):
        result = dispatch_request(
            {
                "operation": "blueprint_info",
                "params": {"asset_path": "/Game/BP_Test", "max_depth": 1},
            },
            FakeApplication(),
        )

        self.assertEqual(result["asset_path"], "/Game/BP_Test")
        self.assertEqual(result["options"]["max_depth"], 1)

    def test_dispatches_read_only_python_operation(self):
        application = FakeApplication()
        application.execute_python = lambda code, node_id=None: {
            "code": code,
            "node_id": node_id,
        }

        result = dispatch_request(
            {
                "operation": "execute_python",
                "params": {"code": "print(1)", "node_id": "editor-1"},
            },
            application,
        )

        self.assertEqual(result["code"], "print(1)")
        self.assertEqual(result["node_id"], "editor-1")


if __name__ == "__main__":
    unittest.main()
