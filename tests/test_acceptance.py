import subprocess
import sys
import unittest
from pathlib import Path

from system_maps import from_json, summary, to_json

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "examples" / "ecosystem.json"
RUNNER = ROOT / "examples" / "analyze.py"


class AcceptanceContracts(unittest.TestCase):
    def test_example_is_canonical_and_reproducible(self):
        system = from_json(FIXTURE.read_text(encoding="utf-8"))
        canonical = to_json(system)
        self.assertEqual(canonical, to_json(from_json(canonical)))
        self.assertEqual(summary(system), summary(system))

    def test_offline_runner_is_byte_stable_and_reports_structural_risk(self):
        def run():
            return subprocess.run(
                [sys.executable, str(RUNNER)],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            ).stdout

        first = run()
        second = run()
        self.assertEqual(first, second)
        self.assertIn("dependency_ranking=", first)
        self.assertIn("cycles=", first)
        self.assertIn("single_points_of_failure=", first)
        self.assertIn("single_points_of_failure=gateway", first)


if __name__ == "__main__":
    unittest.main()
