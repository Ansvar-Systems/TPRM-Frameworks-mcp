"""Evidence document storage and management."""
from pathlib import Path
import hashlib
import json
from dataclasses import dataclass, asdict
from datetime import datetime, UTC
from typing import Optional

@dataclass
class EvidenceDocument:
    """Evidence document metadata."""
    document_id: str
    question_id: str
    assessment_id: str
    vendor_name: str
    filename: str
    file_path: str
    mime_type: str
    size_bytes: int
    sha256_hash: str
    uploaded_at: str
    validated: bool = False
    validated_by: Optional[str] = None
    validated_at: Optional[str] = None

class EvidenceStorage:
    """Manage evidence documents on filesystem."""
    
    def __init__(self, base_path: Path = None):
        if base_path is None:
            base_path = Path.home() / ".tprm-mcp" / "evidence"
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.max_file_size = 50 * 1024 * 1024  # 50MB
        self.allowed_mime_types = [
            "application/pdf",
            "image/png",
            "image/jpeg",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "text/plain"
        ]
    
    def store_document(
        self,
        vendor_name: str,
        assessment_id: str,
        question_id: str,
        file_content: bytes,
        filename: str,
        mime_type: str
    ) -> EvidenceDocument:
        """Store evidence document with metadata."""
        # Validate size
        if len(file_content) > self.max_file_size:
            raise ValueError(f"File too large: {len(file_content)} bytes (max {self.max_file_size})")
        
        # Validate MIME type
        if mime_type not in self.allowed_mime_types:
            raise ValueError(f"Unsupported file type: {mime_type}")
        
        # Create directory structure: evidence/{vendor}/{assessment_id}/{question_id}/
        safe_vendor = self._sanitize_path(vendor_name)
        doc_dir = self.base_path / safe_vendor / assessment_id / question_id
        doc_dir.mkdir(parents=True, exist_ok=True)
        
        # Save file
        safe_filename = self._sanitize_path(filename)
        file_path = doc_dir / safe_filename
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        # Create metadata
        sha256 = hashlib.sha256(file_content).hexdigest()
        metadata = EvidenceDocument(
            document_id=f"{question_id}_{sha256[:8]}",
            question_id=question_id,
            assessment_id=assessment_id,
            vendor_name=vendor_name,
            filename=safe_filename,
            file_path=str(file_path),
            mime_type=mime_type,
            size_bytes=len(file_content),
            sha256_hash=sha256,
            uploaded_at=datetime.now(UTC).isoformat()
        )
        
        # Save metadata JSON
        metadata_path = doc_dir / f"{safe_filename}.metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(asdict(metadata), f, indent=2)
        
        return metadata
    
    def list_documents(
        self,
        vendor_name: Optional[str] = None,
        assessment_id: Optional[str] = None,
        question_id: Optional[str] = None
    ) -> list[EvidenceDocument]:
        """List evidence documents with optional filtering."""
        documents = []
        
        search_path = self.base_path
        if vendor_name:
            search_path = search_path / self._sanitize_path(vendor_name)
        if assessment_id:
            search_path = search_path / assessment_id
        if question_id:
            search_path = search_path / question_id
        
        if not search_path.exists():
            return []
        
        # Find all metadata.json files
        for metadata_file in search_path.rglob("*.metadata.json"):
            with open(metadata_file, 'r') as f:
                metadata_dict = json.load(f)
                documents.append(EvidenceDocument(**metadata_dict))
        
        return documents
    
    def validate_document(
        self,
        document_id: str,
        validated_by: str
    ) -> Optional[EvidenceDocument]:
        """Mark document as validated."""
        # Find document by ID
        for metadata_file in self.base_path.rglob("*.metadata.json"):
            with open(metadata_file, 'r') as f:
                metadata_dict = json.load(f)
                if metadata_dict.get("document_id") == document_id:
                    # Update metadata
                    metadata_dict["validated"] = True
                    metadata_dict["validated_by"] = validated_by
                    metadata_dict["validated_at"] = datetime.now(UTC).isoformat()
                    
                    # Save updated metadata
                    with open(metadata_file, 'w') as f_out:
                        json.dump(metadata_dict, f_out, indent=2)
                    
                    return EvidenceDocument(**metadata_dict)
        
        return None
    
    def _sanitize_path(self, name: str) -> str:
        """Sanitize filename for safe filesystem use."""
        safe = "".join(c for c in name if c.isalnum() or c in "._- ")
        return safe.strip().replace(" ", "_")[:255]
