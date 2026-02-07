#!/usr/bin/env python3
"""
Validation script for regulatory_mappings and regulatory_source fields.
Run this script to verify data structure correctness in questionnaire JSON files.

Usage:
    python3 scripts/validate_regulatory_fields.py
    python3 scripts/validate_regulatory_fields.py path/to/questionnaire.json
"""

import json
import sys
from pathlib import Path
from typing import List, Tuple


def validate_question(question: dict, question_num: int) -> List[str]:
    """Validate a single question's regulatory fields.

    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    q_id = question.get('id', f'Question #{question_num}')

    # Check 1: regulatory_mappings exists
    if 'regulatory_mappings' not in question:
        errors.append(f"{q_id}: Missing 'regulatory_mappings' field")
        return errors

    # Check 2: regulatory_mappings is a list
    mappings = question['regulatory_mappings']
    if not isinstance(mappings, list):
        errors.append(f"{q_id}: 'regulatory_mappings' must be a list, not {type(mappings).__name__}")
        return errors

    # Check 3: regulatory_mappings is non-empty
    if len(mappings) == 0:
        errors.append(f"{q_id}: 'regulatory_mappings' is empty")

    # Check 4: All items in regulatory_mappings are strings
    non_strings = [i for i, item in enumerate(mappings) if not isinstance(item, str)]
    if non_strings:
        errors.append(f"{q_id}: 'regulatory_mappings' contains non-string items at indices: {non_strings}")

    # Check 5: regulatory_source exists
    if 'regulatory_source' not in question:
        errors.append(f"{q_id}: Missing 'regulatory_source' field")
        return errors

    # Check 6: regulatory_source is a dict
    source = question['regulatory_source']
    if not isinstance(source, dict):
        errors.append(f"{q_id}: 'regulatory_source' must be a dict, not {type(source).__name__}")
        return errors

    # Check 7: regulatory_source has required fields
    required_fields = ['regulation', 'article', 'requirement']
    missing = [f for f in required_fields if f not in source]
    if missing:
        errors.append(f"{q_id}: 'regulatory_source' missing required fields: {missing}")

    return errors


def validate_file(filepath: Path) -> Tuple[int, int, List[str]]:
    """Validate all questions in a questionnaire file.

    Returns:
        (total_questions, valid_questions, errors)
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return 0, 0, [f"JSON parse error: {e}"]
    except Exception as e:
        return 0, 0, [f"Error reading file: {e}"]

    questions = data.get('questions', [])
    if not questions:
        return 0, 0, ["No questions found in file"]

    all_errors = []
    valid_count = 0

    for i, question in enumerate(questions, 1):
        errors = validate_question(question, i)
        if errors:
            all_errors.extend(errors)
        else:
            valid_count += 1

    return len(questions), valid_count, all_errors


def main():
    """Main validation routine."""
    print("=" * 80)
    print("REGULATORY FIELDS VALIDATION")
    print("=" * 80)
    print()

    # Determine which files to validate
    if len(sys.argv) > 1:
        # Validate specific files provided as arguments
        files = [Path(arg) for arg in sys.argv[1:]]
    else:
        # Validate all questionnaire files in data directory
        data_dir = Path(__file__).parent.parent / "src" / "tprm_frameworks_mcp" / "data"
        files = list(data_dir.glob("*.json"))
        files = [f for f in files if f.name != "questionnaire-to-scf.json"]

    if not files:
        print("No questionnaire files found to validate.")
        return 1

    total_files = len(files)
    total_questions = 0
    total_valid = 0
    total_errors = 0

    for filepath in sorted(files):
        if not filepath.exists():
            print(f"✗ {filepath}: File not found")
            continue

        print(f"Validating: {filepath.name}")
        print("-" * 80)

        questions, valid, errors = validate_file(filepath)
        total_questions += questions
        total_valid += valid

        if errors:
            total_errors += len(errors)
            print(f"  Total questions: {questions}")
            print(f"  Valid questions: {valid}")
            print(f"  Errors found: {len(errors)}")
            print()
            for error in errors[:10]:  # Show first 10 errors
                print(f"    ✗ {error}")
            if len(errors) > 10:
                print(f"    ... and {len(errors) - 10} more errors")
        else:
            print(f"  ✓ All {questions} questions validated successfully")

        print()

    # Summary
    print("=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    print(f"Files validated: {total_files}")
    print(f"Total questions: {total_questions}")
    print(f"Valid questions: {total_valid}")
    print(f"Invalid questions: {total_questions - total_valid}")
    print(f"Total errors: {total_errors}")
    print()

    if total_errors == 0:
        print("✓ ALL VALIDATIONS PASSED")
        return 0
    else:
        print("✗ VALIDATION FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
