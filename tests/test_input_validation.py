"""Test input validation and security hardening."""

import pytest
from tprm_frameworks_mcp.data_loader import TPRMDataLoader


class TestInputValidation:
    """Verify malformed input is handled gracefully."""

    def test_empty_string_search(self):
        loader = TPRMDataLoader()
        results = loader.search_questions("")
        assert isinstance(results, list)

    def test_very_long_search(self):
        loader = TPRMDataLoader()
        results = loader.search_questions("a" * 10000)
        assert isinstance(results, list)

    def test_sql_injection_search(self):
        loader = TPRMDataLoader()
        results = loader.search_questions("'; DROP TABLE questions; --")
        assert isinstance(results, list)

    def test_special_chars_search(self):
        loader = TPRMDataLoader()
        results = loader.search_questions("(test) [brackets] {braces}")
        assert isinstance(results, list)

    def test_unicode_search(self):
        loader = TPRMDataLoader()
        results = loader.search_questions("Datenschutz ö ü ä ß")
        assert isinstance(results, list)

    def test_null_bytes_search(self):
        loader = TPRMDataLoader()
        results = loader.search_questions("test\x00injection")
        assert isinstance(results, list)
