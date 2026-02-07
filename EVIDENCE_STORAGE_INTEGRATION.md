# Evidence Storage Integration Instructions

## Summary

The evidence document storage system has been implemented in `src/tprm_frameworks_mcp/storage_evidence.py` and tested successfully.

## Files Created

1. **src/tprm_frameworks_mcp/storage_evidence.py** - Evidence storage implementation (COMPLETE)
2. **tests/test_evidence_storage.py** - Comprehensive test suite (COMPLETE)

## Integration with server.py

To integrate the evidence storage tools into server.py, make the following changes:

### 1. Add Import (after line 53, after storage imports)

```python
from .storage_evidence import EvidenceDocument, EvidenceStorage
```

### 2. Initialize Evidence Storage (after line 60, after `storage = TPRMStorage()`)

```python
evidence_storage = EvidenceStorage()
```

### 3. Add Three Tool Definitions to list_tools()

Add these three Tool definitions before the closing `]` of the list_tools() function (around line 505):

```python
        Tool(
            name="upload_evidence_document",
            description=(
                "Upload and store evidence document for a vendor assessment question. "
                "Stores file with metadata, validates size and MIME type, generates SHA256 hash. "
                "Returns document metadata including document_id for future reference."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "vendor_name": {
                        "type": "string",
                        "description": "Name of the vendor providing the evidence",
                    },
                    "assessment_id": {
                        "type": "string",
                        "description": "Assessment ID this evidence relates to",
                    },
                    "question_id": {
                        "type": "string",
                        "description": "Question ID this evidence addresses",
                    },
                    "file_content_base64": {
                        "type": "string",
                        "description": "Base64-encoded file content",
                    },
                    "filename": {
                        "type": "string",
                        "description": "Original filename with extension",
                    },
                    "mime_type": {
                        "type": "string",
                        "description": "MIME type",
                        "enum": [
                            "application/pdf",
                            "image/png",
                            "image/jpeg",
                            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            "text/plain"
                        ],
                    },
                },
                "required": ["vendor_name", "assessment_id", "question_id", "file_content_base64", "filename", "mime_type"],
            },
        ),
        Tool(
            name="list_evidence_documents",
            description=(
                "List evidence documents with optional filtering by vendor, assessment, or question. "
                "Returns metadata for all matching documents including validation status."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "vendor_name": {
                        "type": "string",
                        "description": "Filter by vendor name (optional)",
                    },
                    "assessment_id": {
                        "type": "string",
                        "description": "Filter by assessment ID (optional)",
                    },
                    "question_id": {
                        "type": "string",
                        "description": "Filter by question ID (optional)",
                    },
                },
            },
        ),
        Tool(
            name="validate_evidence_document",
            description=(
                "Mark an evidence document as validated by a reviewer."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "document_id": {
                        "type": "string",
                        "description": "Document ID to validate",
                    },
                    "validated_by": {
                        "type": "string",
                        "description": "Name or ID of person validating the document",
                    },
                },
                "required": ["document_id", "validated_by"],
            },
        ),
```

### 4. Add Three Tool Handlers to _handle_tool_call()

Add these handlers before the final `else:` clause (around line 1443):

See EVIDENCE_TOOL_HANDLERS.py for the complete handler code.

### 5. Update Tools Count

Change line with `"tools_available": 13` to `"tools_available": 16`

## Test Results

The storage_evidence.py module has been tested and verified:
- ✓ Document storage with SHA256 hashing
- ✓ File size validation (50MB limit)
- ✓ MIME type validation
- ✓ Directory structure creation
- ✓ Document listing with filters
- ✓ Document validation workflow
- ✓ Path sanitization

## Next Steps

1. Review the evidence storage implementation
2. Manually integrate the tool definitions and handlers into server.py
3. Run full integration tests
4. Update README.md to document the three new tools

## Storage Location

Evidence documents are stored in: `~/.tprm-mcp/evidence/{vendor}/{assessment_id}/{question_id}/`

Each document has an associated `.metadata.json` file with full metadata.
