"""Data loader for TPRM questionnaire frameworks."""

import json
from pathlib import Path
from typing import Any

from .models import Question, QuestionnaireFramework, RiskLevel


class TPRMDataLoader:
    """Loads and provides access to TPRM questionnaire data."""

    def __init__(self):
        self.frameworks: dict[str, dict[str, Any]] = {}
        self.questions_by_framework: dict[str, list[Question]] = {}
        self.control_mappings: dict[str, list[dict[str, Any]]] = {}
        self._load_data()

    def _load_data(self):
        """Load questionnaire data from JSON files."""
        data_dir = Path(__file__).parent / "data"

        # Load each framework
        for framework in QuestionnaireFramework:
            framework_file = data_dir / f"{framework.value}.json"
            if framework_file.exists():
                with open(framework_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.frameworks[framework.value] = data["metadata"]

                    # Convert questions, handling enum conversions
                    questions = []
                    for q_data in data["questions"]:
                        # Convert risk_if_inadequate string to enum
                        if isinstance(q_data.get("risk_if_inadequate"), str):
                            q_data["risk_if_inadequate"] = RiskLevel(q_data["risk_if_inadequate"])
                        questions.append(Question(**q_data))

                    self.questions_by_framework[framework.value] = questions

        # Load control mappings
        mappings_file = data_dir / "questionnaire-to-scf.json"
        if mappings_file.exists():
            with open(mappings_file, "r", encoding="utf-8") as f:
                self.control_mappings = json.load(f)

    def get_framework_metadata(self, framework: str) -> dict[str, Any] | None:
        """Get metadata for a specific framework."""
        return self.frameworks.get(framework)

    def get_questions(
        self,
        framework: str,
        category: str | None = None,
        regulatory_filter: list[str] | None = None,
    ) -> list[Question]:
        """Get questions for a framework, optionally filtered."""
        questions = self.questions_by_framework.get(framework, [])

        if category:
            questions = [q for q in questions if q.category == category]

        if regulatory_filter:
            questions = [
                q
                for q in questions
                if any(reg in q.regulatory_mappings for reg in regulatory_filter)
            ]

        return questions

    def get_control_mappings(self, framework: str, question_id: str) -> list[str]:
        """Get SCF control mappings for a specific question."""
        fw_mappings = self.control_mappings.get(framework, {})
        return fw_mappings.get(question_id, [])

    def get_all_frameworks(self) -> list[dict[str, Any]]:
        """Get list of all available frameworks."""
        return [
            {
                "key": key,
                "name": meta.get("name"),
                "version": meta.get("version"),
                "question_count": meta.get("total_questions", 0),
                "status": meta.get("status", "placeholder"),
            }
            for key, meta in self.frameworks.items()
        ]

    def get_categories(self, framework: str) -> list[str]:
        """Get all categories for a framework."""
        questions = self.questions_by_framework.get(framework, [])
        return sorted(list(set(q.category for q in questions)))

    def search_questions(self, query: str, framework: str | None = None) -> list[Question]:
        """Search questions by keyword."""
        query_lower = query.lower()
        results = []

        frameworks_to_search = (
            [framework] if framework else list(self.questions_by_framework.keys())
        )

        for fw in frameworks_to_search:
            questions = self.questions_by_framework.get(fw, [])
            for q in questions:
                if query_lower in q.question_text.lower() or (
                    q.description and query_lower in q.description.lower()
                ):
                    results.append(q)

        return results
