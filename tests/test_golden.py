"""Golden contract tests — validates data accuracy against fixtures/golden-tests.json."""

import hashlib
import json
import re
from pathlib import Path

import pytest

GOLDEN_TESTS_PATH = Path(__file__).parent.parent / "fixtures" / "golden-tests.json"
GOLDEN_HASHES_PATH = Path(__file__).parent.parent / "fixtures" / "golden-hashes.json"
DATA_DIR = Path(__file__).parent.parent / "src" / "tprm_frameworks_mcp" / "data"


class TestGoldenHashes:
    """Test data files haven't drifted from known-good state."""

    def test_golden_hashes_file_exists(self):
        assert GOLDEN_HASHES_PATH.exists(), "fixtures/golden-hashes.json missing — run scripts/generate_golden_hashes.py"

    def test_data_files_match_golden_hashes(self):
        hashes = json.loads(GOLDEN_HASHES_PATH.read_text())
        for filename, expected in hashes.items():
            filepath = DATA_DIR / filename
            assert filepath.exists(), f"Data file {filename} missing"
            actual_hash = hashlib.sha256(filepath.read_bytes()).hexdigest()
            assert actual_hash == expected["sha256"], (
                f"Data drift detected in {filename}! "
                f"Expected SHA256: {expected['sha256']}, Got: {actual_hash}. "
                f"If intentional, re-run scripts/generate_golden_hashes.py"
            )

    def test_no_unexpected_data_files(self):
        """Ensure no new data files added without updating golden hashes."""
        hashes = json.loads(GOLDEN_HASHES_PATH.read_text())
        actual_files = {f.name for f in DATA_DIR.glob("*.json")}
        expected_files = set(hashes.keys())
        unexpected = actual_files - expected_files
        assert not unexpected, (
            f"New data files found without golden hashes: {unexpected}. "
            f"Run scripts/generate_golden_hashes.py to update."
        )


class TestGoldenTests:
    """Validate golden contract tests exist and are well-formed."""

    def test_golden_tests_file_exists(self):
        assert GOLDEN_TESTS_PATH.exists(), "fixtures/golden-tests.json missing"

    def test_golden_tests_minimum_count(self):
        tests = json.loads(GOLDEN_TESTS_PATH.read_text())
        assert len(tests["tests"]) >= 10, (
            f"Need at least 10 golden tests, found {len(tests['tests'])}"
        )

    def test_golden_tests_have_required_fields(self):
        tests = json.loads(GOLDEN_TESTS_PATH.read_text())
        for test in tests["tests"]:
            assert "id" in test, "Test missing 'id'"
            assert "tool" in test, f"Test {test.get('id')} missing 'tool'"
            assert "input" in test, f"Test {test.get('id')} missing 'input'"
            assert "expected" in test, f"Test {test.get('id')} missing 'expected'"


class TestDataIntegrity:
    """Validate data file content integrity."""

    def test_caiq_v4_full_question_count(self):
        data = json.loads((DATA_DIR / "caiq_v4_full.json").read_text())
        questions = data.get("questions", [])
        assert len(questions) == 283, f"CAIQ v4 should have 283 questions, found {len(questions)}"

    def test_sig_lite_question_count(self):
        data = json.loads((DATA_DIR / "sig_lite.json").read_text())
        questions = data.get("questions", [])
        assert len(questions) == 10, f"SIG Lite should have 10 questions, found {len(questions)}"

    def test_dora_question_count(self):
        data = json.loads((DATA_DIR / "dora_ict_tpp.json").read_text())
        questions = data.get("questions", [])
        assert len(questions) == 72, f"DORA should have 72 questions, found {len(questions)}"

    def test_nis2_question_count(self):
        data = json.loads((DATA_DIR / "nis2_supply_chain.json").read_text())
        questions = data.get("questions", [])
        assert len(questions) == 70, f"NIS2 should have 70 questions, found {len(questions)}"

    def test_all_questions_have_required_fields(self):
        required_fields = ["id", "question_text", "category", "expected_answer_type"]
        for json_file in DATA_DIR.glob("*.json"):
            if json_file.name in ("questionnaire-to-scf.json", "eu-regulations-mapping.json", "dora-nis2-overlap.json"):
                continue
            data = json.loads(json_file.read_text())
            for q in data.get("questions", []):
                for field in required_fields:
                    assert field in q, f"{json_file.name}: question {q.get('id', '?')} missing '{field}'"

    def test_all_questions_have_unique_ids(self):
        for json_file in DATA_DIR.glob("*.json"):
            if json_file.name in ("questionnaire-to-scf.json", "eu-regulations-mapping.json", "dora-nis2-overlap.json"):
                continue
            data = json.loads(json_file.read_text())
            ids = [q["id"] for q in data.get("questions", []) if "id" in q]
            assert len(ids) == len(set(ids)), f"{json_file.name}: duplicate question IDs found"

    def test_scf_mappings_file_valid(self):
        data = json.loads((DATA_DIR / "questionnaire-to-scf.json").read_text())
        assert isinstance(data, (dict, list)), "SCF mappings should be dict or list"

    def test_evaluation_rubrics_have_valid_regex(self):
        """Verify all regex patterns in rubrics are valid."""
        for json_file in DATA_DIR.glob("*.json"):
            if json_file.name in ("questionnaire-to-scf.json", "eu-regulations-mapping.json", "dora-nis2-overlap.json"):
                continue
            data = json.loads(json_file.read_text())
            for q in data.get("questions", []):
                rubric = q.get("evaluation_rubric", {})
                for key in ("acceptable", "partially_acceptable", "unacceptable"):
                    for pattern in rubric.get(key, []):
                        try:
                            re.compile(pattern, re.IGNORECASE)
                        except re.error as e:
                            pytest.fail(f"{json_file.name}: question {q['id']} has invalid regex '{pattern}' in {key}: {e}")
