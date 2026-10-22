import ast
import unittest
from pathlib import Path


class ReportSourceOwnershipTest(unittest.TestCase):
    def test_report_sources_are_owned_by_ai_rag_directory(self) -> None:
        root = Path(__file__).resolve().parents[1]
        source = (root / "docs/ai-rag/reports/build_system_briefing.py").read_text()
        module = ast.parse(source)
        docs = next(
            ast.literal_eval(node.value)
            for node in module.body
            if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "DOCS" for target in node.targets)
        )

        external_sources = [entry[0] for entry in docs if entry[0].startswith("../")]
        self.assertEqual(
            [],
            external_sources,
            "the report must not bundle backend-owned docs by relative filesystem path",
        )


if __name__ == "__main__":
    unittest.main()
