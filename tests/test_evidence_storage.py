"""Test evidence document storage and management."""

import base64
import hashlib
import json
import tempfile
from pathlib import Path

import pytest

from tprm_frameworks_mcp.storage_evidence import EvidenceDocument, EvidenceStorage


@pytest.fixture
def temp_storage_path():
    """Create temporary storage directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def evidence_storage(temp_storage_path):
    """Create EvidenceStorage instance with temporary path."""
    return EvidenceStorage(base_path=temp_storage_path)


@pytest.fixture
def sample_pdf_content():
    """Sample PDF content for testing."""
    return b"%PDF-1.4\n%Test PDF content\n%%EOF"


@pytest.fixture
def sample_image_content():
    """Sample image content for testing."""
    # Minimal PNG file header
    return (
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
        b'\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\x00\x01\x00\x00'
        b'\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    )


def test_store_document_pdf(evidence_storage, sample_pdf_content):
    """Test storing a PDF document."""
    document = evidence_storage.store_document(
        vendor_name="Acme Corp",
        assessment_id="assess_001",
        question_id="q_soc2_001",
        file_content=sample_pdf_content,
        filename="soc2_report.pdf",
        mime_type="application/pdf"
    )
    
    assert document.vendor_name == "Acme Corp"
    assert document.assessment_id == "assess_001"
    assert document.question_id == "q_soc2_001"
    assert document.filename == "soc2_report.pdf"
    assert document.mime_type == "application/pdf"
    assert document.size_bytes == len(sample_pdf_content)
    assert document.sha256_hash == hashlib.sha256(sample_pdf_content).hexdigest()
    assert document.validated is False
    assert document.validated_by is None
    assert document.validated_at is None
    
    # Verify file was created
    file_path = Path(document.file_path)
    assert file_path.exists()
    assert file_path.read_bytes() == sample_pdf_content
    
    # Verify metadata was created
    metadata_path = file_path.parent / f"{document.filename}.metadata.json"
    assert metadata_path.exists()


def test_store_document_image(evidence_storage, sample_image_content):
    """Test storing an image document."""
    document = evidence_storage.store_document(
        vendor_name="Beta LLC",
        assessment_id="assess_002",
        question_id="q_caiq_010",
        file_content=sample_image_content,
        filename="data_center.png",
        mime_type="image/png"
    )
    
    assert document.mime_type == "image/png"
    assert document.size_bytes == len(sample_image_content)
    
    file_path = Path(document.file_path)
    assert file_path.exists()


def test_store_document_file_size_limit(evidence_storage):
    """Test file size limit validation."""
    large_content = b"X" * (51 * 1024 * 1024)  # 51 MB, exceeds 50 MB limit
    
    with pytest.raises(ValueError, match="File too large"):
        evidence_storage.store_document(
            vendor_name="Test Vendor",
            assessment_id="assess_003",
            question_id="q_test_001",
            file_content=large_content,
            filename="large_file.pdf",
            mime_type="application/pdf"
        )


def test_store_document_invalid_mime_type(evidence_storage, sample_pdf_content):
    """Test MIME type validation."""
    with pytest.raises(ValueError, match="Unsupported file type"):
        evidence_storage.store_document(
            vendor_name="Test Vendor",
            assessment_id="assess_004",
            question_id="q_test_002",
            file_content=sample_pdf_content,
            filename="executable.exe",
            mime_type="application/x-msdownload"
        )


def test_list_documents_no_filter(evidence_storage, sample_pdf_content, sample_image_content):
    """Test listing all documents without filters."""
    # Store multiple documents
    evidence_storage.store_document(
        vendor_name="Vendor A",
        assessment_id="assess_001",
        question_id="q_001",
        file_content=sample_pdf_content,
        filename="doc1.pdf",
        mime_type="application/pdf"
    )
    
    evidence_storage.store_document(
        vendor_name="Vendor B",
        assessment_id="assess_002",
        question_id="q_002",
        file_content=sample_image_content,
        filename="doc2.png",
        mime_type="image/png"
    )
    
    documents = evidence_storage.list_documents()
    assert len(documents) == 2


def test_list_documents_filter_by_vendor(evidence_storage, sample_pdf_content):
    """Test listing documents filtered by vendor."""
    # Store documents for different vendors
    evidence_storage.store_document(
        vendor_name="Vendor A",
        assessment_id="assess_001",
        question_id="q_001",
        file_content=sample_pdf_content,
        filename="doc1.pdf",
        mime_type="application/pdf"
    )
    
    evidence_storage.store_document(
        vendor_name="Vendor B",
        assessment_id="assess_002",
        question_id="q_002",
        file_content=sample_pdf_content,
        filename="doc2.pdf",
        mime_type="application/pdf"
    )
    
    documents = evidence_storage.list_documents(vendor_name="Vendor A")
    assert len(documents) == 1
    assert documents[0].vendor_name == "Vendor A"


def test_list_documents_filter_by_assessment(evidence_storage, sample_pdf_content):
    """Test listing documents filtered by assessment ID."""
    # Store documents for different assessments
    evidence_storage.store_document(
        vendor_name="Vendor A",
        assessment_id="assess_001",
        question_id="q_001",
        file_content=sample_pdf_content,
        filename="doc1.pdf",
        mime_type="application/pdf"
    )
    
    evidence_storage.store_document(
        vendor_name="Vendor A",
        assessment_id="assess_002",
        question_id="q_002",
        file_content=sample_pdf_content,
        filename="doc2.pdf",
        mime_type="application/pdf"
    )
    
    documents = evidence_storage.list_documents(
        vendor_name="Vendor A",
        assessment_id="assess_001"
    )
    assert len(documents) == 1
    assert documents[0].assessment_id == "assess_001"


def test_list_documents_filter_by_question(evidence_storage, sample_pdf_content):
    """Test listing documents filtered by question ID."""
    # Store documents for different questions
    evidence_storage.store_document(
        vendor_name="Vendor A",
        assessment_id="assess_001",
        question_id="q_001",
        file_content=sample_pdf_content,
        filename="doc1.pdf",
        mime_type="application/pdf"
    )
    
    evidence_storage.store_document(
        vendor_name="Vendor A",
        assessment_id="assess_001",
        question_id="q_002",
        file_content=sample_pdf_content,
        filename="doc2.pdf",
        mime_type="application/pdf"
    )
    
    documents = evidence_storage.list_documents(
        vendor_name="Vendor A",
        assessment_id="assess_001",
        question_id="q_001"
    )
    assert len(documents) == 1
    assert documents[0].question_id == "q_001"


def test_list_documents_empty(evidence_storage):
    """Test listing documents when none exist."""
    documents = evidence_storage.list_documents()
    assert len(documents) == 0


def test_validate_document(evidence_storage, sample_pdf_content):
    """Test document validation workflow."""
    # Store a document
    document = evidence_storage.store_document(
        vendor_name="Vendor A",
        assessment_id="assess_001",
        question_id="q_001",
        file_content=sample_pdf_content,
        filename="doc1.pdf",
        mime_type="application/pdf"
    )
    
    assert document.validated is False
    
    # Validate the document
    validated_doc = evidence_storage.validate_document(
        document_id=document.document_id,
        validated_by="jane.smith@example.com"
    )
    
    assert validated_doc is not None
    assert validated_doc.validated is True
    assert validated_doc.validated_by == "jane.smith@example.com"
    assert validated_doc.validated_at is not None
    
    # Verify persistence
    documents = evidence_storage.list_documents()
    assert len(documents) == 1
    assert documents[0].validated is True
    assert documents[0].validated_by == "jane.smith@example.com"


def test_validate_document_not_found(evidence_storage):
    """Test validating a non-existent document."""
    result = evidence_storage.validate_document(
        document_id="nonexistent_id",
        validated_by="test@example.com"
    )
    
    assert result is None


def test_sanitize_path(evidence_storage):
    """Test path sanitization."""
    # Test with special characters
    safe_name = evidence_storage._sanitize_path("Test Vendor (2024) #1!")
    assert safe_name == "Test_Vendor_2024_1"
    
    # Test with very long name
    long_name = "A" * 300
    safe_name = evidence_storage._sanitize_path(long_name)
    assert len(safe_name) <= 255


def test_document_directory_structure(evidence_storage, sample_pdf_content, temp_storage_path):
    """Test that documents are stored in correct directory structure."""
    document = evidence_storage.store_document(
        vendor_name="Test Vendor",
        assessment_id="assess_001",
        question_id="q_001",
        file_content=sample_pdf_content,
        filename="test.pdf",
        mime_type="application/pdf"
    )
    
    # Verify directory structure: base/vendor/assessment/question/filename
    expected_path = (
        temp_storage_path / "Test_Vendor" / "assess_001" / "q_001" / "test.pdf"
    )
    
    assert Path(document.file_path) == expected_path
    assert expected_path.exists()


def test_multiple_documents_same_question(evidence_storage, sample_pdf_content, sample_image_content):
    """Test storing multiple documents for the same question."""
    # Store first document
    doc1 = evidence_storage.store_document(
        vendor_name="Vendor A",
        assessment_id="assess_001",
        question_id="q_001",
        file_content=sample_pdf_content,
        filename="policy.pdf",
        mime_type="application/pdf"
    )
    
    # Store second document
    doc2 = evidence_storage.store_document(
        vendor_name="Vendor A",
        assessment_id="assess_001",
        question_id="q_001",
        file_content=sample_image_content,
        filename="screenshot.png",
        mime_type="image/png"
    )
    
    # List documents for this question
    documents = evidence_storage.list_documents(
        vendor_name="Vendor A",
        assessment_id="assess_001",
        question_id="q_001"
    )
    
    assert len(documents) == 2
    assert doc1.document_id != doc2.document_id


def test_document_hash_consistency(evidence_storage, sample_pdf_content):
    """Test that SHA256 hash is correctly generated."""
    document = evidence_storage.store_document(
        vendor_name="Vendor A",
        assessment_id="assess_001",
        question_id="q_001",
        file_content=sample_pdf_content,
        filename="test.pdf",
        mime_type="application/pdf"
    )
    
    # Calculate expected hash
    expected_hash = hashlib.sha256(sample_pdf_content).hexdigest()
    assert document.sha256_hash == expected_hash
    
    # Verify stored file has same hash
    stored_content = Path(document.file_path).read_bytes()
    stored_hash = hashlib.sha256(stored_content).hexdigest()
    assert stored_hash == expected_hash


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
