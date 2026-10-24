"""The setup must diagnose the running embedder, not just downloaded files."""

import contextlib
import io
import json
from pathlib import Path
import runpy
import subprocess
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/check-embeddings.py"


class EmbeddingTests(unittest.TestCase):
    def checker(self):
        self.assertTrue(SCRIPT.is_file(), "Falta o diagnóstico dos embeddings no serviço")
        return runpy.run_path(str(SCRIPT))

    def report(self, **overrides):
        embedding = {"provider": "local", "model": "all-MiniLM-L6-v2",
                     "dim": 384, "status": "ok"}
        embedding.update(overrides)
        return {"providers": {"embedding": embedding}, "derived": {
            "embedding_rows": 0, "latest_pages_missing_embeddings": 0}}

    def test_accepts_active_local_model_without_requiring_existing_pages(self):
        result = self.checker()["check_status"](self.report())
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["embedding_rows"], 0)

    def test_reports_no_calls_yet_as_pending_instead_of_success(self):
        result = self.checker()["check_status"](self.report(status="unknown"))
        self.assertEqual(result["status"], "pending")

    def test_rejects_disabled_failed_and_unexpected_providers(self):
        check = self.checker()["check_status"]
        for changes in ({"status": "disabled"}, {"status": "error"},
                        {"status": "unexpected"}, {"provider": "openai"},
                        {"model": "other"}, {"dim": 768}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                check(self.report(**changes))

    def test_missing_diagnostics_cannot_pass(self):
        check = self.checker()["check_status"]
        for report in ({}, {"providers": {}}, {"providers": {"embedding": {}}}):
            with self.subTest(report=report), self.assertRaises((KeyError, ValueError)):
                check(report)

    def test_reads_only_status_and_does_not_print_provider_errors(self):
        main = self.checker()["main"]
        report = self.report(last_error_message="PRIVATE_PROVIDER_RESPONSE")
        output = io.StringIO()
        with patch("subprocess.run", return_value=subprocess.CompletedProcess(
                [], 0, stdout=json.dumps(report))) as command, contextlib.redirect_stdout(output):
            main()
        self.assertEqual(command.call_args.args[0], ["ai-memory", "status", "--json"])
        self.assertNotIn("PRIVATE_PROVIDER_RESPONSE", output.getvalue())

    def test_failed_command_and_invalid_json_do_not_pass_or_expose_output(self):
        main = self.checker()["main"]
        with patch("subprocess.run", side_effect=subprocess.CalledProcessError(
                1, ["ai-memory"], stderr="PRIVATE_ERROR")):
            with self.assertRaises(SystemExit) as error:
                main()
        self.assertNotIn("PRIVATE_ERROR", str(error.exception))
        with patch("subprocess.run", return_value=subprocess.CompletedProcess(
                [], 0, stdout="not JSON")):
            with self.assertRaises(SystemExit):
                main()


if __name__ == "__main__":
    unittest.main()
