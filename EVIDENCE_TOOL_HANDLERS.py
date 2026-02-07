"""
Evidence Storage Tool Handlers for server.py

Add these three handlers to the _handle_tool_call() function in server.py,
before the final 'else:' clause.
"""

# Handler 1: upload_evidence_document
elif name == "upload_evidence_document":
    try:
        import base64
        
        vendor_name = arguments["vendor_name"]
        assessment_id = arguments["assessment_id"]
        question_id = arguments["question_id"]
        file_content_base64 = arguments["file_content_base64"]
        filename = arguments["filename"]
        mime_type = arguments["mime_type"]
        
        # Decode base64 content
        try:
            file_content = base64.b64decode(file_content_base64)
        except Exception as e:
            logger.error("Failed to decode base64 content", extra={"error": str(e)})
            return [TextContent(type="text", text=f"Error: Invalid base64 encoding - {str(e)}")]
        
        # Store document
        document = evidence_storage.store_document(
            vendor_name=vendor_name,
            assessment_id=assessment_id,
            question_id=question_id,
            file_content=file_content,
            filename=filename,
            mime_type=mime_type
        )
        
        logger.info(
            "Evidence document uploaded",
            extra={
                "document_id": document.document_id,
                "vendor_name": vendor_name,
                "assessment_id": assessment_id,
                "question_id": question_id,
                "filename": filename,
                "size_bytes": document.size_bytes
            }
        )
        
        # Format output
        text = f"**Evidence Document Uploaded**\n\n"
        text += f"**Document ID:** `{document.document_id}`\n"
        text += f"**Vendor:** {document.vendor_name}\n"
        text += f"**Assessment ID:** {document.assessment_id}\n"
        text += f"**Question ID:** {document.question_id}\n"
        text += f"**Filename:** {document.filename}\n"
        text += f"**MIME Type:** {document.mime_type}\n"
        text += f"**Size:** {document.size_bytes:,} bytes\n"
        text += f"**SHA256:** {document.sha256_hash}\n"
        text += f"**Uploaded:** {document.uploaded_at}\n"
        text += f"**File Path:** {document.file_path}\n\n"
        
        doc_dict = {
            "document_id": document.document_id,
            "vendor_name": document.vendor_name,
            "assessment_id": document.assessment_id,
            "question_id": document.question_id,
            "filename": document.filename,
            "mime_type": document.mime_type,
            "size_bytes": document.size_bytes,
            "sha256_hash": document.sha256_hash,
            "uploaded_at": document.uploaded_at,
            "file_path": document.file_path
        }
        text += f"```json\n{json.dumps(doc_dict, indent=2)}\n```"
        
        return [TextContent(type="text", text=text)]
        
    except ValueError as e:
        logger.warning("Evidence upload validation failed", extra={"error": str(e)})
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.error("Failed to upload evidence document", exc_info=True)
        return [TextContent(type="text", text=f"Error: Failed to upload document - {str(e)}")]

# Handler 2: list_evidence_documents
elif name == "list_evidence_documents":
    try:
        vendor_name = arguments.get("vendor_name")
        assessment_id = arguments.get("assessment_id")
        question_id = arguments.get("question_id")
        
        # List documents with filters
        documents = evidence_storage.list_documents(
            vendor_name=vendor_name,
            assessment_id=assessment_id,
            question_id=question_id
        )
        
        logger.info(
            "Listed evidence documents",
            extra={
                "count": len(documents),
                "vendor_name": vendor_name,
                "assessment_id": assessment_id,
                "question_id": question_id
            }
        )
        
        # Format output
        text = f"**Evidence Documents**\n\n"
        text += f"**Total:** {len(documents)}\n"
        
        if vendor_name:
            text += f"**Filtered by Vendor:** {vendor_name}\n"
        if assessment_id:
            text += f"**Filtered by Assessment:** {assessment_id}\n"
        if question_id:
            text += f"**Filtered by Question:** {question_id}\n"
        
        text += "\n"
        
        if documents:
            # Group by vendor
            by_vendor = {}
            for doc in documents:
                if doc.vendor_name not in by_vendor:
                    by_vendor[doc.vendor_name] = []
                by_vendor[doc.vendor_name].append(doc)
            
            for vendor, vendor_docs in sorted(by_vendor.items()):
                text += f"### {vendor}\n"
                for doc in vendor_docs:
                    validated_marker = "✓" if doc.validated else "○"
                    text += f"{validated_marker} **{doc.document_id}** - {doc.filename}\n"
                    text += f"  - Assessment: {doc.assessment_id}, Question: {doc.question_id}\n"
                    text += f"  - Size: {doc.size_bytes:,} bytes, Type: {doc.mime_type}\n"
                    text += f"  - Uploaded: {doc.uploaded_at}\n"
                    if doc.validated:
                        text += f"  - Validated by {doc.validated_by} at {doc.validated_at}\n"
                    text += "\n"
            
            # JSON output
            docs_list = [{
                "document_id": doc.document_id,
                "vendor_name": doc.vendor_name,
                "assessment_id": doc.assessment_id,
                "question_id": doc.question_id,
                "filename": doc.filename,
                "mime_type": doc.mime_type,
                "size_bytes": doc.size_bytes,
                "sha256_hash": doc.sha256_hash,
                "uploaded_at": doc.uploaded_at,
                "validated": doc.validated,
                "validated_by": doc.validated_by,
                "validated_at": doc.validated_at
            } for doc in documents]
            text += f"\n```json\n{json.dumps(docs_list, indent=2)}\n```"
        else:
            text += "No documents found matching the specified filters.\n"
        
        return [TextContent(type="text", text=text)]
        
    except Exception as e:
        logger.error("Failed to list evidence documents", exc_info=True)
        return [TextContent(type="text", text=f"Error: Failed to list documents - {str(e)}")]

# Handler 3: validate_evidence_document
elif name == "validate_evidence_document":
    try:
        document_id = arguments["document_id"]
        validated_by = arguments["validated_by"]
        
        # Validate document
        document = evidence_storage.validate_document(
            document_id=document_id,
            validated_by=validated_by
        )
        
        if not document:
            logger.warning("Evidence document not found", extra={"document_id": document_id})
            return [TextContent(type="text", text=f"Error: Document '{document_id}' not found")]
        
        logger.info(
            "Evidence document validated",
            extra={
                "document_id": document_id,
                "validated_by": validated_by,
                "vendor_name": document.vendor_name,
                "assessment_id": document.assessment_id
            }
        )
        
        # Format output
        text = f"**Evidence Document Validated**\n\n"
        text += f"**Document ID:** `{document.document_id}`\n"
        text += f"**Vendor:** {document.vendor_name}\n"
        text += f"**Assessment ID:** {document.assessment_id}\n"
        text += f"**Question ID:** {document.question_id}\n"
        text += f"**Filename:** {document.filename}\n"
        text += f"**Validated By:** {document.validated_by}\n"
        text += f"**Validated At:** {document.validated_at}\n\n"
        
        val_dict = {
            "document_id": document.document_id,
            "vendor_name": document.vendor_name,
            "assessment_id": document.assessment_id,
            "question_id": document.question_id,
            "filename": document.filename,
            "validated": document.validated,
            "validated_by": document.validated_by,
            "validated_at": document.validated_at
        }
        text += f"```json\n{json.dumps(val_dict, indent=2)}\n```"
        
        return [TextContent(type="text", text=text)]
        
    except Exception as e:
        logger.error("Failed to validate evidence document", exc_info=True)
        return [TextContent(type="text", text=f"Error: Failed to validate document - {str(e)}")]
