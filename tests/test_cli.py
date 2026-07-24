from __future__ import annotations

import contextlib
import io
import json
import unittest
from unittest.mock import patch

from unreal_dev_helper.cli import main


class CliTests(unittest.TestCase):
    def test_status_calls_allowlisted_backend_operation(self):
        output = io.StringIO()

        with patch(
            "unreal_dev_helper.cli._request",
            return_value={"connected": True, "nodes": []},
        ) as request:
            with contextlib.redirect_stdout(output):
                exit_code = main(["status"])

        self.assertEqual(exit_code, 0)
        self.assertEqual(request.call_args.args[0], "status")
        self.assertTrue(json.loads(output.getvalue())["ok"])

    def test_execute_python_calls_backend_operation(self):
        output = io.StringIO()

        with patch(
            "unreal_dev_helper.cli._request",
            return_value={"success": True},
        ) as request:
            with contextlib.redirect_stdout(output):
                exit_code = main(
                    ["execute-python", "--code", "import unreal; unreal.log('inspect')"]
                )

        self.assertEqual(exit_code, 0)
        self.assertEqual(request.call_args.args[0], "execute_python")


if __name__ == "__main__":
    unittest.main()
