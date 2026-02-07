"""Evaluation rubric system for assessing vendor responses."""

import re
from typing import Any

from ..config import config
from ..models import AnswerStatus, Question, QuestionResponse, RiskLevel


class EvaluationRubric:
    """Evaluates vendor responses against predefined rubrics."""

    def __init__(self):
        self.keyword_weights = {
            "yes": 1.0,
            "no": 0.0,
            "implemented": 1.0,
            "not implemented": 0.0,
            "partial": 0.5,
            "in progress": 0.4,
            "planned": 0.3,
            "not applicable": None,  # Special case
            "n/a": None,
        }

    def evaluate_response(
        self,
        question: Question,
        response: QuestionResponse,
        strictness: str = "moderate",
    ) -> tuple[AnswerStatus, float, list[str], RiskLevel]:
        """
        Evaluate a single response.

        Returns:
            (status, score, findings, risk_level)
        """
        if not response.answer or response.answer.strip() == "":
            return (
                AnswerStatus.UNANSWERED,
                0.0,
                ["Question left unanswered"],
                question.risk_if_inadequate,
            )

        answer_lower = response.answer.lower().strip()

        # Check for N/A
        if answer_lower in ["n/a", "not applicable", "does not apply"]:
            return (
                AnswerStatus.NOT_APPLICABLE,
                100.0,
                ["Marked as not applicable"],
                RiskLevel.INFORMATIONAL,
            )

        # Get evaluation rubric for this question
        rubric = question.evaluation_rubric

        # Use question-specific rubric if available
        if rubric:
            return self._evaluate_with_rubric(question, response, rubric, strictness)

        # Fallback to generic evaluation
        return self._evaluate_generic(question, response, strictness)

    def _evaluate_with_rubric(
        self,
        question: Question,
        response: QuestionResponse,
        rubric: dict[str, Any],
        strictness: str,
    ) -> tuple[AnswerStatus, float, list[str], RiskLevel]:
        """Evaluate using question-specific rubric."""
        answer_lower = response.answer.lower()
        findings = []

        # Check acceptable answers
        acceptable_patterns = rubric.get("acceptable", [])
        for pattern in acceptable_patterns:
            if isinstance(pattern, str):
                if re.search(pattern.lower(), answer_lower):
                    return (
                        AnswerStatus.ACCEPTABLE,
                        100.0,
                        ["Response meets acceptance criteria"],
                        RiskLevel.LOW,
                    )
            elif isinstance(pattern, dict):
                # More complex pattern matching
                if self._matches_complex_pattern(answer_lower, pattern):
                    return (
                        AnswerStatus.ACCEPTABLE,
                        100.0,
                        ["Response meets acceptance criteria"],
                        RiskLevel.LOW,
                    )

        # Check partially acceptable
        partial_patterns = rubric.get("partially_acceptable", [])
        for pattern in partial_patterns:
            if isinstance(pattern, str) and re.search(pattern.lower(), answer_lower):
                score = 60.0 if strictness == "strict" else 70.0
                findings.append("Response partially meets requirements")
                return (
                    AnswerStatus.PARTIALLY_ACCEPTABLE,
                    score,
                    findings,
                    RiskLevel.MEDIUM,
                )

        # Check required keywords
        required_keywords = rubric.get("required_keywords", [])
        missing_keywords = []
        for keyword in required_keywords:
            if keyword.lower() not in answer_lower:
                missing_keywords.append(keyword)

        if missing_keywords:
            findings.append(f"Missing key information: {', '.join(missing_keywords)}")

        # Check unacceptable patterns
        unacceptable_patterns = rubric.get("unacceptable", [])
        for pattern in unacceptable_patterns:
            if isinstance(pattern, str) and re.search(pattern.lower(), answer_lower):
                findings.append(f"Response indicates inadequate controls")
                return (
                    AnswerStatus.UNACCEPTABLE,
                    20.0,
                    findings,
                    question.risk_if_inadequate,
                )

        # If we get here, it's not clearly acceptable or unacceptable
        # Score based on completeness and missing keywords
        completeness_score = self._calculate_completeness(response.answer)
        keyword_penalty = len(missing_keywords) * 10

        final_score = max(0, completeness_score - keyword_penalty)

        if final_score >= 70:
            status = AnswerStatus.PARTIALLY_ACCEPTABLE
            risk = RiskLevel.MEDIUM
        else:
            status = AnswerStatus.UNACCEPTABLE
            risk = question.risk_if_inadequate

        findings.append(f"Response completeness: {completeness_score:.0f}%")
        if missing_keywords:
            findings.append(f"Missing key elements: {', '.join(missing_keywords)}")

        return (status, final_score, findings, risk)

    def _evaluate_generic(
        self,
        question: Question,
        response: QuestionResponse,
        strictness: str,
    ) -> tuple[AnswerStatus, float, list[str], RiskLevel]:
        """Generic evaluation when no specific rubric exists."""
        answer_lower = response.answer.lower()
        findings = []

        # For yes/no questions
        if question.expected_answer_type == "yes_no":
            if "yes" in answer_lower and "no" not in answer_lower:
                return (AnswerStatus.ACCEPTABLE, 100.0, ["Affirmative response"], RiskLevel.LOW)
            elif "no" in answer_lower:
                findings.append("Negative response indicates potential gap")
                return (
                    AnswerStatus.UNACCEPTABLE,
                    20.0,
                    findings,
                    question.risk_if_inadequate,
                )

        # Check for positive indicators
        positive_indicators = [
            "implemented",
            "compliant",
            "certified",
            "documented",
            "automated",
            "regularly",
            "continuous",
        ]
        positive_count = sum(1 for word in positive_indicators if word in answer_lower)

        # Check for negative indicators
        negative_indicators = [
            "not implemented",
            "no",
            "manual",
            "ad hoc",
            "planned",
            "in progress",
            "none",
        ]
        negative_count = sum(1 for word in negative_indicators if word in answer_lower)

        # Calculate completeness
        completeness_score = self._calculate_completeness(response.answer)

        # Combine scores
        indicator_score = min(100, (positive_count * 20) - (negative_count * 15))
        final_score = (completeness_score * 0.6) + (indicator_score * 0.4)

        # Adjust for strictness
        if strictness == "strict":
            final_score *= 0.9
        elif strictness == "lenient":
            final_score *= 1.1

        final_score = max(0, min(100, final_score))

        # Determine status using configurable thresholds
        if final_score >= config.evaluation.risk_low_threshold:
            status = AnswerStatus.ACCEPTABLE
            risk = RiskLevel.LOW
        elif final_score >= config.evaluation.risk_medium_threshold:
            status = AnswerStatus.PARTIALLY_ACCEPTABLE
            risk = RiskLevel.MEDIUM
        else:
            status = AnswerStatus.UNACCEPTABLE
            risk = question.risk_if_inadequate

        findings.append(f"Response completeness: {completeness_score:.0f}%")
        findings.append(f"Positive indicators: {positive_count}, Negative: {negative_count}")

        return (status, final_score, findings, risk)

    def _calculate_completeness(self, answer: str) -> float:
        """Calculate response completeness based on length and structure."""
        if not answer:
            return 0.0

        # Basic heuristics
        word_count = len(answer.split())
        has_details = len(answer) > 50
        has_structure = "," in answer or "." in answer or "\n" in answer

        score = 0.0

        # Word count scoring
        if word_count >= 30:
            score += 50
        elif word_count >= 15:
            score += 35
        elif word_count >= 5:
            score += 20

        # Detail scoring
        if has_details:
            score += 30

        # Structure scoring
        if has_structure:
            score += 20

        return min(100, score)

    def _matches_complex_pattern(self, answer: str, pattern: dict[str, Any]) -> bool:
        """Match complex pattern with multiple conditions."""
        if "all_of" in pattern:
            return all(keyword.lower() in answer for keyword in pattern["all_of"])

        if "any_of" in pattern:
            return any(keyword.lower() in answer for keyword in pattern["any_of"])

        if "regex" in pattern:
            return bool(re.search(pattern["regex"], answer, re.IGNORECASE))

        return False
