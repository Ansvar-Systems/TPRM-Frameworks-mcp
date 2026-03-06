"""MCP server for TPRM frameworks and vendor assessments."""

import asyncio
import json
import time
import uuid
from datetime import datetime, UTC
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from .config import config
from .data_loader import TPRMDataLoader
from .evaluation.rubric import EvaluationRubric
from .exceptions import (
    DataLoadError,
    EURegulationsError,
    EvaluationError,
    FrameworkNotFoundError,
    IntegrationError,
    TPRMError,
    ValidationError,
)
from .logging_config import setup_logging
from .integrations.eu_regulations import (
    check_regulatory_compliance,
    generate_questions_from_articles,
    get_compliance_timeline,
    get_dora_requirements,
    get_nis2_requirements,
    map_questions_to_articles,
)
from .models import (
    AnswerStatus,
    AssessmentResult,
    EntityType,
    EvaluationResult,
    Question,
    Questionnaire,
    QuestionnaireFramework,
    QuestionnaireMetadata,
    QuestionResponse,
    ResponseStrictness,
    RiskLevel,
)
from .storage import (
    AssessmentNotFoundError,
    QuestionnaireNotFoundError,
    StorageError,
    TPRMStorage,
)
from .storage_evidence import EvidenceStorage

# Setup logging
logger = setup_logging()

# Initialize data loader, evaluator, and persistent storage
data_loader = TPRMDataLoader()
evaluator = EvaluationRubric()
storage = TPRMStorage()
evidence_storage = EvidenceStorage()

SERVER_VERSION = config.server.version

# In-memory cache for backward compatibility (storage is primary source)
generated_questionnaires: dict[str, Questionnaire] = {}


async def _get_tool_definitions() -> list[Tool]:
    """List available TPRM tools."""
    return [
        Tool(
            name="list_frameworks",
            description=(
                "List all available TPRM questionnaire frameworks with metadata. "
                "Use this FIRST to discover available frameworks (SIG, CAIQ, DORA, NIS2) "
                "before generating questionnaires. Returns framework names, question counts, "
                "categories, and implementation status. No parameters required."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        ),
        Tool(
            name="generate_questionnaire",
            description=(
                "Generate a tailored vendor assessment questionnaire. Returns a complete "
                "questionnaire in JSON with all questions, evaluation rubrics, and a unique "
                "questionnaire_id needed for evaluate_response. Use list_frameworks first "
                "to see available frameworks. For DORA/NIS2-specific dynamic generation, "
                "use generate_dora_questionnaire or generate_nis2_questionnaire instead."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "framework": {
                        "type": "string",
                        "description": "Base framework to use for the questionnaire",
                        "enum": [
                            "sig_full",
                            "sig_lite",
                            "caiq_v4",

                            "dora_ict_tpp",
                            "nis2_supply_chain",
                        ],
                    },
                    "scope": {
                        "type": "string",
                        "description": (
                            "Assessment scope: 'full' (all questions), 'lite' (critical controls only), "
                            "'focused' (specific categories — requires 'categories' param)"
                        ),
                        "enum": ["full", "lite", "focused"],
                        "default": "full",
                    },
                    "entity_type": {
                        "type": "string",
                        "description": "Type of vendor being assessed. Affects question prioritization.",
                        "enum": [
                            "saas_provider",
                            "cloud_provider",
                            "data_processor",
                            "ict_provider",
                            "financial_institution",
                            "healthcare_provider",
                            "generic_vendor",
                        ],
                        "default": "generic_vendor",
                    },
                    "regulations": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "Applicable regulations to overlay (e.g., ['gdpr', 'dora', 'nis2']). "
                            "Questions will be filtered/prioritized based on regulatory requirements."
                        ),
                    },
                    "categories": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "Specific categories to include (only when scope='focused'). "
                            "Use list_frameworks to see available categories per framework."
                        ),
                    },
                },
                "required": ["framework"],
                "additionalProperties": False,
            },
        ),
        Tool(
            name="evaluate_response",
            description=(
                "Score and evaluate vendor responses against a generated questionnaire. "
                "Uses rubric-based evaluation (regex patterns + keyword matching) to produce "
                "per-question scores, gap findings, and an overall risk level (LOW/MEDIUM/HIGH/CRITICAL). "
                "Requires a questionnaire_id from generate_questionnaire. Results are persisted "
                "and can be used with compare_assessments and check_regulatory_compliance."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "questionnaire_id": {
                        "type": "string",
                        "description": "ID from generate_questionnaire output",
                        "minLength": 1,
                    },
                    "vendor_name": {
                        "type": "string",
                        "description": "Name of the vendor being assessed",
                        "minLength": 1,
                    },
                    "responses": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "question_id": {"type": "string", "minLength": 1},
                                "answer": {"type": "string", "maxLength": 10000},
                                "supporting_documents": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                                "notes": {"type": "string", "maxLength": 5000},
                            },
                            "required": ["question_id", "answer"],
                        },
                        "description": "Array of vendor responses. Each must have question_id and answer.",
                        "minItems": 1,
                    },
                    "strictness": {
                        "type": "string",
                        "description": (
                            "Evaluation strictness: 'lenient' (accept partial answers), "
                            "'moderate' (balanced), 'strict' (require comprehensive answers)"
                        ),
                        "enum": ["lenient", "moderate", "strict"],
                        "default": "moderate",
                    },
                },
                "required": ["questionnaire_id", "responses"],
                "additionalProperties": False,
            },
        ),
        Tool(
            name="map_questionnaire_to_controls",
            description=(
                "Map questionnaire questions to SCF (Secure Controls Framework) controls. "
                "Bridges TPRM questionnaires to security-controls-mcp for gap analysis. "
                "Provide EITHER questionnaire_id (from generate_questionnaire) OR framework "
                "(to map all questions in a framework). Output includes SCF control IDs "
                "that can be passed to security-controls-mcp.get_control() for details."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "questionnaire_id": {
                        "type": "string",
                        "description": "Generated questionnaire ID to map (provide this OR framework)",
                    },
                    "framework": {
                        "type": "string",
                        "description": "Framework to map all questions for (provide this OR questionnaire_id)",
                        "enum": [
                            "sig_full",
                            "sig_lite",
                            "caiq_v4",

                            "dora_ict_tpp",
                            "nis2_supply_chain",
                        ],
                    },
                    "question_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional: map only these specific question IDs (subset filtering)",
                    },
                    "control_framework": {
                        "type": "string",
                        "description": (
                            "Target control framework for mapping. Defaults to SCF."
                        ),
                        "default": "scf",
                    },
                },
                "additionalProperties": False,
            },
        ),
        Tool(
            name="generate_tprm_report",
            description=(
                "Generate a comprehensive TPRM report synthesizing questionnaire evaluations, "
                "vendor intelligence, and security posture data. This is the final output tool — "
                "call it AFTER evaluate_response. Optionally enrich with vendor_intel_data from "
                "vendor-intel-mcp and posture_data from external scans."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "vendor_name": {
                        "type": "string",
                        "description": "Name of the vendor being assessed",
                        "minLength": 1,
                    },
                    "questionnaire_results": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Evaluation result IDs from evaluate_response calls",
                    },
                    "vendor_intel_data": {
                        "type": "object",
                        "description": (
                            "Optional: Vendor intelligence from vendor-intel-mcp "
                            "(company_profile, breach_history, certifications)"
                        ),
                    },
                    "posture_data": {
                        "type": "object",
                        "description": (
                            "Optional: External security posture data "
                            "(DNS security, SSL/TLS config, exposed services)"
                        ),
                    },
                    "include_recommendations": {
                        "type": "boolean",
                        "description": "Include remediation recommendations in the report",
                        "default": True,
                    },
                },
                "required": ["vendor_name"],
                "additionalProperties": False,
            },
        ),
        Tool(
            name="get_questionnaire",
            description=(
                "Retrieve a previously generated questionnaire by its ID. "
                "Returns the full questionnaire structure with all questions, rubrics, and metadata. "
                "The questionnaire must have been generated in the current session or persisted in storage."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "questionnaire_id": {
                        "type": "string",
                        "description": "ID of the questionnaire (from generate_questionnaire output)",
                        "minLength": 1,
                    },
                },
                "required": ["questionnaire_id"],
                "additionalProperties": False,
            },
        ),
        Tool(
            name="search_questions",
            description=(
                "Search for questions across all frameworks by keyword or phrase. "
                "Returns matching questions with their framework, category, rubric, and SCF mappings. "
                "Use this to find questions on specific topics (e.g., 'encryption', 'MFA', 'incident response') "
                "without generating a full questionnaire. Returns empty array (not error) if no matches."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search keyword or phrase (e.g., 'encryption', 'access control')",
                        "minLength": 1,
                        "maxLength": 500,
                    },
                    "framework": {
                        "type": "string",
                        "description": "Optional: limit search to a specific framework",
                        "enum": [
                            "sig_full",
                            "sig_lite",
                            "caiq_v4",

                            "dora_ict_tpp",
                            "nis2_supply_chain",
                        ],
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum results to return (default: 20)",
                        "default": 20,
                        "minimum": 1,
                        "maximum": 100,
                    },
                },
                "required": ["query"],
                "additionalProperties": False,
            },
        ),
        Tool(
            name="get_vendor_history",
            description=(
                "Get assessment history for a vendor showing improvement trends over time. "
                "Returns past assessments with scores, dates, risk levels, and trend direction. "
                "Requires the vendor to have been assessed at least once via evaluate_response."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "vendor_name": {
                        "type": "string",
                        "description": "Exact name of the vendor (as used in evaluate_response)",
                        "minLength": 1,
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum assessments to return (default: 10)",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 100,
                    },
                },
                "required": ["vendor_name"],
                "additionalProperties": False,
            },
        ),
        Tool(
            name="compare_assessments",
            description=(
                "Compare two assessments for the same vendor to identify improvements or degradations. "
                "Shows score delta, risk level changes, and per-category changes. "
                "If assessment IDs are omitted, compares the two most recent assessments. "
                "Requires at least 2 assessments to exist for the vendor."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "vendor_name": {
                        "type": "string",
                        "description": "Name of the vendor",
                        "minLength": 1,
                    },
                    "assessment_id_1": {
                        "type": "integer",
                        "description": "Optional: ID of first (earlier) assessment",
                    },
                    "assessment_id_2": {
                        "type": "integer",
                        "description": "Optional: ID of second (later) assessment",
                    },
                },
                "required": ["vendor_name"],
                "additionalProperties": False,
            },
        ),
        Tool(
            name="generate_dora_questionnaire",
            description=(
                "Generate a DORA (EU Regulation 2022/2554) questionnaire dynamically. "
                "Uses EU regulations data to create assessment questions for ICT third-party "
                "provider evaluation. For static DORA questionnaires, use generate_questionnaire "
                "with framework='dora_ict_tpp' instead. Requires eu-regulations-mcp to be available "
                "for full dynamic generation; falls back to static data if unavailable."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "DORA requirement category to focus on",
                        "enum": [
                            "ICT_third_party",
                            "ICT_risk",
                            "business_continuity",
                            "incident_management",
                            "testing",
                        ],
                        "default": "ICT_third_party",
                    },
                    "scope": {
                        "type": "string",
                        "description": "Assessment scope",
                        "enum": ["full", "focused"],
                        "default": "full",
                    },
                },
                "additionalProperties": False,
            },
        ),
        Tool(
            name="generate_nis2_questionnaire",
            description=(
                "Generate a NIS2 (EU Directive 2022/2555) supply chain questionnaire dynamically. "
                "Uses EU regulations data to create assessment questions. For static NIS2 questionnaires, "
                "use generate_questionnaire with framework='nis2_supply_chain' instead. "
                "Requires eu-regulations-mcp for full dynamic generation."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "NIS2 requirement category to focus on",
                        "enum": [
                            "supply_chain",
                            "risk_management",
                            "governance",
                            "incident_response",
                        ],
                        "default": "supply_chain",
                    },
                    "scope": {
                        "type": "string",
                        "description": "Assessment scope",
                        "enum": ["full", "focused"],
                        "default": "full",
                    },
                },
                "additionalProperties": False,
            },
        ),
        Tool(
            name="check_regulatory_compliance",
            description=(
                "Check DORA or NIS2 compliance gaps based on a completed assessment. "
                "Analyzes evaluation results to identify which regulatory requirements are met "
                "and which have gaps. Returns compliance coverage percentage and detailed gap list. "
                "Requires a completed assessment from evaluate_response."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "assessment_id": {
                        "type": "integer",
                        "description": "Assessment ID from evaluate_response results",
                    },
                    "regulation": {
                        "type": "string",
                        "description": "Regulation to check compliance against",
                        "enum": ["DORA", "NIS2"],
                    },
                },
                "required": ["assessment_id", "regulation"],
                "additionalProperties": False,
            },
        ),
        Tool(
            name="get_regulatory_timeline",
            description=(
                "Get DORA or NIS2 compliance deadlines and milestones. Returns key dates, "
                "implementation milestones, and days until deadline. Use for compliance "
                "planning and reporting. Does NOT require a prior assessment."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "regulation": {
                        "type": "string",
                        "description": "Regulation to get timeline for",
                        "enum": ["DORA", "NIS2"],
                    },
                },
                "required": ["regulation"],
                "additionalProperties": False,
            },
        ),
        Tool(
            name="upload_evidence_document",
            description=(
                "Upload an evidence document supporting a vendor's questionnaire response. "
                "Stores with SHA256 hash for integrity verification. Organizes by vendor/assessment/question. "
                "Max 50MB. Use list_evidence_documents to retrieve uploaded documents."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "vendor_name": {
                        "type": "string",
                        "description": "Name of the vendor",
                        "minLength": 1,
                    },
                    "assessment_id": {
                        "type": "string",
                        "description": "Assessment ID this evidence belongs to",
                        "minLength": 1,
                    },
                    "question_id": {
                        "type": "string",
                        "description": "Question ID this evidence supports",
                        "minLength": 1,
                    },
                    "file_content_base64": {
                        "type": "string",
                        "description": "Base64-encoded file content (max ~67MB encoded for 50MB file)",
                        "minLength": 1,
                    },
                    "filename": {
                        "type": "string",
                        "description": "Original filename with extension",
                        "minLength": 1,
                    },
                    "mime_type": {
                        "type": "string",
                        "description": "MIME type of the file",
                        "enum": [
                            "application/pdf",
                            "image/png",
                            "image/jpeg",
                            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            "text/plain",
                        ],
                    },
                },
                "required": ["vendor_name", "assessment_id", "question_id", "file_content_base64", "filename", "mime_type"],
                "additionalProperties": False,
            },
        ),
        Tool(
            name="list_evidence_documents",
            description=(
                "List evidence documents with optional filtering. Returns metadata including "
                "validation status, file details, and upload timestamps. All filters are optional — "
                "call with no params to list all documents."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "vendor_name": {
                        "type": "string",
                        "description": "Filter by vendor name",
                    },
                    "assessment_id": {
                        "type": "string",
                        "description": "Filter by assessment ID",
                    },
                    "question_id": {
                        "type": "string",
                        "description": "Filter by question ID",
                    },
                },
                "additionalProperties": False,
            },
        ),
        Tool(
            name="validate_evidence_document",
            description=(
                "Mark an evidence document as validated by a reviewer. Records validator identity "
                "and timestamp. Use after reviewing an uploaded evidence document. "
                "Get the document_id from list_evidence_documents."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "document_id": {
                        "type": "string",
                        "description": "Document ID (from list_evidence_documents or upload_evidence_document)",
                        "minLength": 1,
                    },
                    "validated_by": {
                        "type": "string",
                        "description": "Name or email of the reviewer validating this document",
                        "minLength": 1,
                    },
                },
                "required": ["document_id", "validated_by"],
                "additionalProperties": False,
            },
        ),
    ]


async def _dispatch_tool_call(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    start_time = time.time()
    request_id = str(uuid.uuid4())[:8]

    logger.info(
        "Tool invocation started",
        extra={
            "tool_name": name,
            "request_id": request_id,
            "arguments": arguments
        }
    )

    try:
        result = await _handle_tool_call(name, arguments)
        duration_ms = round((time.time() - start_time) * 1000, 2)

        logger.info(
            "Tool invocation completed",
            extra={
                "tool_name": name,
                "request_id": request_id,
                "duration_ms": duration_ms,
                "status": "success"
            }
        )

        return result
    except Exception as e:
        duration_ms = round((time.time() - start_time) * 1000, 2)

        logger.error(
            "Tool invocation failed",
            extra={
                "tool_name": name,
                "request_id": request_id,
                "duration_ms": duration_ms,
                "error": str(e),
                "status": "error"
            },
            exc_info=True
        )
        raise


async def _handle_tool_call(name: str, arguments: dict) -> list[TextContent]:
    """Internal handler for tool calls."""

    if name == "list_frameworks":
        frameworks = data_loader.get_all_frameworks()

        text = f"**TPRM Frameworks MCP Server v{SERVER_VERSION}**\n\n"
        text += f"**Available Questionnaire Frameworks: {len(frameworks)}**\n\n"

        for fw in frameworks:
            text += f"### {fw['name']}\n"
            text += f"- **Key:** `{fw['key']}`\n"
            text += f"- **Version:** {fw['version']}\n"
            text += f"- **Questions:** {fw['question_count']}\n"
            text += f"- **Status:** {fw['status']}\n"
            if fw["status"] == "placeholder":
                text += "  ⚠️ *Placeholder data - replace with licensed questionnaire content*\n"
            text += "\n"

        text += "\n**Integration Notes:**\n"
        text += "- Use `generate_questionnaire` to create tailored assessments\n"
        text += "- Use `map_questionnaire_to_controls` to bridge to SCF controls\n"
        text += "- Use `evaluate_response` to score vendor responses\n"

        return [TextContent(type="text", text=text)]

    elif name == "generate_questionnaire":
        try:
            framework = arguments["framework"]
            scope = arguments.get("scope", "full")
            entity_type = arguments.get("entity_type", "generic_vendor")
            regulations = arguments.get("regulations", [])
            categories = arguments.get("categories")

            # Load framework metadata and questions
            fw_metadata = data_loader.get_framework_metadata(framework)
            if not fw_metadata:
                available = list(data_loader.frameworks.keys())
                raise FrameworkNotFoundError(framework, available)

            questions = data_loader.get_questions(framework)

            # Apply scope filters
            if scope == "lite":
                # Filter to high-weight questions only
                questions = [q for q in questions if q.weight >= 8]
            elif scope == "focused" and categories:
                # Filter to specific categories
                questions = [q for q in questions if q.category in categories]

            # Apply regulatory filters
            if regulations:
                questions = [
                    q
                    for q in questions
                    if any(reg.lower() in " ".join(q.regulatory_mappings).lower() for reg in regulations)
                ]

            # Generate questionnaire
            questionnaire_id = str(uuid.uuid4())
            metadata = QuestionnaireMetadata(
                framework=QuestionnaireFramework(framework),
                version=fw_metadata["version"],
                total_questions=len(questions),
                categories=data_loader.get_categories(framework),
                estimated_completion_time=fw_metadata.get(
                    "estimated_completion_time", "Unknown"
                ),
                scope=scope,
                entity_type=EntityType(entity_type) if entity_type != "generic_vendor" else None,
                applicable_regulations=regulations,
            )

            questionnaire = Questionnaire(
                id=questionnaire_id,
                metadata=metadata,
                questions=questions,
                generation_timestamp=datetime.now(UTC).isoformat(),
                custom_parameters={
                "scope": scope,
                "entity_type": entity_type,
                "regulations": regulations,
            },
            )

            # Store in persistent storage and cache
            storage.save_questionnaire(questionnaire)
            generated_questionnaires[questionnaire_id] = questionnaire

            # Return as JSON
            result = {
                "questionnaire_id": questionnaire_id,
                "framework": framework,
                "scope": scope,
                "entity_type": entity_type,
                "total_questions": len(questions),
                "categories": metadata.categories,
                "questions": [
                    {
                        "id": q.id,
                        "category": q.category,
                        "subcategory": q.subcategory,
                        "question_text": q.question_text,
                        "description": q.description,
                        "expected_answer_type": q.expected_answer_type,
                        "is_required": q.is_required,
                        "weight": q.weight,
                        "regulatory_mappings": q.regulatory_mappings,
                        "scf_control_mappings": q.scf_control_mappings,
                        "risk_if_inadequate": q.risk_if_inadequate.value,
                    }
                    for q in questions
                ],
            }

            return [
                TextContent(
                    type="text",
                    text=f"**Questionnaire Generated**\n\n"
                    f"**ID:** `{questionnaire_id}`\n"
                    f"**Framework:** {fw_metadata['name']}\n"
                    f"**Scope:** {scope}\n"
                    f"**Total Questions:** {len(questions)}\n"
                    f"**Entity Type:** {entity_type}\n\n"
                    f"```json\n{json.dumps(result, indent=2)}\n```",
                )
            ]
        except FrameworkNotFoundError as e:
            logger.warning("Framework not found", extra={"error": e.to_dict()})
            return [TextContent(type="text", text=f"Error: {e.message}")]
        except StorageError as e:
            logger.error("Failed to save questionnaire", extra={"error": e.to_dict()}, exc_info=True)
            return [TextContent(type="text", text=f"Error: Failed to save questionnaire - {e.message}")]
        except (ValueError, KeyError) as e:
            logger.error("Invalid questionnaire parameters", extra={"error": str(e)}, exc_info=True)
            return [TextContent(type="text", text=f"Error: Invalid parameters - {str(e)}")]
        except Exception as e:
            logger.error("Unexpected error generating questionnaire", exc_info=True)
            return [TextContent(type="text", text=f"Error: Unexpected error - {str(e)}")]

    elif name == "evaluate_response":
        try:
            questionnaire_id = arguments["questionnaire_id"]
            vendor_name = arguments.get("vendor_name", "Vendor")
            responses_data = arguments["responses"]
            strictness = arguments.get("strictness", "moderate")

            # Retrieve questionnaire from cache or storage
            questionnaire = generated_questionnaires.get(questionnaire_id)
            if not questionnaire:
                try:
                    questionnaire = storage.get_questionnaire(questionnaire_id)
                    if questionnaire:
                        # Cache for future use
                        generated_questionnaires[questionnaire_id] = questionnaire
                except QuestionnaireNotFoundError:
                    raise QuestionnaireNotFoundError(
                        f"Questionnaire '{questionnaire_id}' not found. Generate one first."
                    )

            if not questionnaire:
                raise QuestionnaireNotFoundError(
                    f"Questionnaire '{questionnaire_id}' not found. Generate one first."
                )

            # Parse responses
            # Support both array and dict formats for responses
            if isinstance(responses_data, dict):
                # Convert dict format to array format
                responses_data = [
                    {"question_id": qid, "answer": answer}
                    for qid, answer in responses_data.items()
                ]
            
            responses = [QuestionResponse(**r) for r in responses_data]
            response_map = {r.question_id: r for r in responses}

            # Evaluate each question
            evaluation_results = []
            critical_findings = []
            compliance_gaps: dict[str, list[str]] = {}

            for question in questionnaire.questions:
                response = response_map.get(question.id)

                if not response:
                    # Question not answered
                    eval_result = EvaluationResult(
                        question_id=question.id,
                        status=AnswerStatus.UNANSWERED,
                        score=0.0,
                        risk_level=question.risk_if_inadequate,
                        findings=["Question not answered"],
                        recommendations=["Provide a complete response to this question"],
                        scf_controls_addressed=[],
                    )
                else:
                    # Evaluate response
                    status, score, findings, risk = evaluator.evaluate_response(
                        question, response, strictness
                    )

                    recommendations = []
                    if status in [AnswerStatus.PARTIALLY_ACCEPTABLE, AnswerStatus.UNACCEPTABLE]:
                        recommendations.append(
                            f"Enhance {question.category.lower()} controls to meet requirements"
                        )
                        if question.scf_control_mappings:
                            recommendations.append(
                                f"Review SCF controls: {', '.join(question.scf_control_mappings)}"
                            )

                    eval_result = EvaluationResult(
                        question_id=question.id,
                        status=status,
                        score=score,
                        risk_level=risk,
                        findings=findings,
                        recommendations=recommendations,
                        scf_controls_addressed=question.scf_control_mappings,
                    )

                    # Track critical findings
                    if risk == RiskLevel.CRITICAL and status == AnswerStatus.UNACCEPTABLE:
                        critical_findings.append(
                            f"{question.id}: {question.question_text} - {', '.join(findings)}"
                        )

                    # Track compliance gaps
                    for reg in question.regulatory_mappings:
                        if status in [
                            AnswerStatus.PARTIALLY_ACCEPTABLE,
                            AnswerStatus.UNACCEPTABLE,
                        ]:
                            if reg not in compliance_gaps:
                                compliance_gaps[reg] = []
                            compliance_gaps[reg].append(question.id)

                evaluation_results.append(eval_result)

            # Calculate overall score
            scored_results = [r for r in evaluation_results if r.status != AnswerStatus.NOT_APPLICABLE]
            if scored_results:
                overall_score = sum(r.score for r in scored_results) / len(scored_results)
            else:
                overall_score = 0.0

            # Determine overall risk level
            if overall_score >= config.evaluation.risk_low_threshold:
                overall_risk = RiskLevel.LOW
            elif overall_score >= config.evaluation.risk_medium_threshold:
                overall_risk = RiskLevel.MEDIUM
            elif overall_score >= config.evaluation.risk_high_threshold:
                overall_risk = RiskLevel.HIGH
            else:
                overall_risk = RiskLevel.CRITICAL

            # Create assessment result
            assessment = AssessmentResult(
                questionnaire_id=questionnaire_id,
                vendor_name=vendor_name,
                evaluation_results=evaluation_results,
                overall_score=overall_score,
                overall_risk_level=overall_risk,
                critical_findings=critical_findings,
                compliance_gaps=compliance_gaps,
                timestamp=datetime.now(UTC).isoformat(),
                strictness_level=ResponseStrictness(strictness),
            )

            # Save to persistent storage
            assessment_id = storage.save_assessment(assessment)

            # Format output
            text = f"**Vendor Assessment Results: {vendor_name}**\n\n"
            text += f"**Assessment ID:** {assessment_id}\n"
            text += f"**Overall Score:** {overall_score:.1f}/100\n"
            text += f"**Overall Risk Level:** {overall_risk.value.upper()}\n"
            text += f"**Questionnaire:** {questionnaire_id}\n"
            text += f"**Strictness:** {strictness}\n\n"

            # Summary by status
            status_counts = {}
            for result in evaluation_results:
                status_counts[result.status] = status_counts.get(result.status, 0) + 1

            text += "**Response Summary:**\n"
            for status, count in status_counts.items():
                text += f"- {status.value}: {count}\n"

            # Critical findings
            if critical_findings:
                text += f"\n**⚠️ Critical Findings ({len(critical_findings)}):**\n"
                for finding in critical_findings[:5]:  # Show first 5
                    text += f"- {finding}\n"
                if len(critical_findings) > 5:
                    text += f"  ... and {len(critical_findings) - 5} more\n"

            # Compliance gaps
            if compliance_gaps:
                text += "\n**Compliance Gaps:**\n"
                for reg, questions in list(compliance_gaps.items())[:5]:
                    text += f"- **{reg}**: {len(questions)} questions with gaps\n"

            # Detailed results (JSON)
            result_json = {
                "assessment_id": assessment_id,
                "vendor_name": vendor_name,
                "questionnaire_id": questionnaire_id,
                "overall_score": overall_score,
                "overall_risk_level": overall_risk.value,
                "critical_findings_count": len(critical_findings),
                "compliance_gaps": {k: len(v) for k, v in compliance_gaps.items()},
                "evaluation_results": [
                    {
                        "question_id": r.question_id,
                        "status": r.status.value,
                        "score": r.score,
                        "risk_level": r.risk_level.value,
                        "findings": r.findings,
                        "recommendations": r.recommendations,
                        "scf_controls": r.scf_controls_addressed,
                    }
                    for r in evaluation_results
                ],
            }

            text += f"\n\n```json\n{json.dumps(result_json, indent=2)}\n```"

            return [TextContent(type="text", text=text)]
        except QuestionnaireNotFoundError as e:
            logger.warning("Questionnaire not found for evaluation", extra={"error": str(e)})
            return [TextContent(type="text", text=f"Error: {str(e)}")]
        except StorageError as e:
            logger.error("Storage error during evaluation", extra={"error": str(e)}, exc_info=True)
            return [TextContent(type="text", text=f"Error: Failed to save assessment - {str(e)}")]
        except (ValueError, KeyError) as e:
            logger.error("Invalid evaluation parameters", extra={"error": str(e)}, exc_info=True)
            return [TextContent(type="text", text=f"Error: Invalid parameters - {str(e)}")]
        except Exception as e:
            logger.error("Unexpected error during evaluation", exc_info=True)
            return [TextContent(type="text", text=f"Error: Unexpected error - {str(e)}")]

    elif name == "map_questionnaire_to_controls":
        # Support both questionnaire_id and framework parameters
        questionnaire_id = arguments.get("questionnaire_id")
        framework = arguments.get("framework")
        
        if questionnaire_id:
            # Look up framework from generated questionnaire
            questionnaire = generated_questionnaires.get(questionnaire_id)
            if not questionnaire:
                return [TextContent(type="text", text=f"Error: Questionnaire {questionnaire_id} not found")]
            framework = questionnaire.metadata.framework.value
        elif not framework:
            return [TextContent(type="text", text="Error: Either questionnaire_id or framework must be provided")]
        
        question_ids = arguments.get("question_ids")
        control_framework = arguments.get("control_framework", "scf")

        questions = data_loader.get_questions(framework)

        if question_ids:
            questions = [q for q in questions if q.id in question_ids]

        mappings = []
        for question in questions:
            scf_controls = data_loader.get_control_mappings(framework, question.id)
            if not scf_controls:
                scf_controls = question.scf_control_mappings

            if scf_controls:
                mappings.append(
                    {
                        "question_id": question.id,
                        "question_text": question.question_text,
                        "category": question.category,
                        "scf_controls": scf_controls,
                        "weight": question.weight,
                        "regulatory_mappings": question.regulatory_mappings,
                    }
                )

        text = f"**Questionnaire to SCF Control Mappings**\n\n"
        text += f"**Framework:** {framework}\n"
        text += f"**Control Framework:** {control_framework}\n"
        text += f"**Mapped Questions:** {len(mappings)}\n\n"

        # Group by category
        by_category: dict[str, list] = {}
        for mapping in mappings:
            cat = mapping["category"]
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(mapping)

        for category, cat_mappings in sorted(by_category.items()):
            text += f"### {category}\n"
            for mapping in cat_mappings[:10]:  # Limit per category
                text += f"- **{mapping['question_id']}**: "
                text += f"{', '.join(mapping['scf_controls'])}\n"
            if len(cat_mappings) > 10:
                text += f"  ... and {len(cat_mappings) - 10} more\n"
            text += "\n"

        text += "\n**Integration Tip:**\n"
        text += "Use the security-controls-mcp server to:\n"
        text += "- Get detailed control descriptions: `get_control(control_id)`\n"
        text += "- Map to other frameworks: `map_frameworks(source='scf', target='iso_27001_2022')`\n"

        result_json = {"framework": framework, "mappings": mappings}
        text += f"\n```json\n{json.dumps(result_json, indent=2)}\n```"

        return [TextContent(type="text", text=text)]

    elif name == "generate_tprm_report":
        vendor_name = arguments.get("vendor_name", "Vendor")
        questionnaire_results = arguments.get("questionnaire_results", [])
        vendor_intel = arguments.get("vendor_intel_data")
        posture_data = arguments.get("posture_data")
        include_recs = arguments.get("include_recommendations", True)

        try:
            # Load actual assessment results from storage
            assessments_data = []
            overall_scores = []
            all_findings = []
            all_compliance_gaps = {}
            frameworks_used = set()

            for assessment_id in questionnaire_results:
                try:
                    assessment = storage.get_assessment(assessment_id)
                    if assessment:
                        assessments_data.append({
                            "id": assessment_id,
                            "score": assessment.overall_score,
                            "risk": assessment.overall_risk_level.value,
                            "framework": assessment.questionnaire_id,
                            "timestamp": assessment.timestamp,
                            "strictness": assessment.strictness_level.value,
                        })
                        overall_scores.append(assessment.overall_score)
                        all_findings.extend(assessment.critical_findings)
                        
                        # Aggregate compliance gaps
                        for reg, gaps in assessment.compliance_gaps.items():
                            if reg not in all_compliance_gaps:
                                all_compliance_gaps[reg] = []
                            all_compliance_gaps[reg].extend(gaps)
                except AssessmentNotFoundError:
                    logger.warning(f"Assessment {assessment_id} not found", extra={"assessment_id": assessment_id})
                    continue

            # Calculate weighted average score
            aggregate_score = sum(overall_scores) / len(overall_scores) if overall_scores else 0
            
            # Process vendor intelligence data (if provided)
            intel_risk_factors = []
            intel_positive_factors = []
            
            if vendor_intel:
                breaches = vendor_intel.get("breach_history", [])
                if breaches:
                    intel_risk_factors.append(f"⚠️ {len(breaches)} security breach(es) in last 5 years")
                    aggregate_score -= min(5 * len(breaches), 20)  # Cap penalty at 20 points
                
                certifications = vendor_intel.get("certifications", [])
                if certifications:
                    for cert in certifications:
                        if "ISO 27001" in cert:
                            intel_positive_factors.append(f"✓ ISO 27001 certified")
                            aggregate_score += 5
                        elif "SOC 2" in cert:
                            intel_positive_factors.append(f"✓ SOC 2 certified")
                            aggregate_score += 3
                
                company_profile = vendor_intel.get("company_profile", {})
                if company_profile:
                    if company_profile.get("security_team_size", 0) > 10:
                        intel_positive_factors.append(f"✓ Dedicated security team (10+ members)")
                    
                    if company_profile.get("years_in_business", 0) < 2:
                        intel_risk_factors.append(f"⚠️ New company (<2 years)")
                        aggregate_score -= 5

            # Process security posture data (if provided)
            posture_findings = []
            posture_positive = []
            
            if posture_data:
                ssl_grade = posture_data.get("ssl_tls", {}).get("grade", "F")
                if ssl_grade in ["A+", "A"]:
                    posture_positive.append(f"✓ Strong SSL/TLS (Grade {ssl_grade})")
                elif ssl_grade not in ["B"]:
                    posture_findings.append(f"⚠️ Weak SSL/TLS (Grade {ssl_grade})")
                    aggregate_score -= 5
                
                security_headers = posture_data.get("security_headers", {}).get("score", 0)
                if security_headers >= 80:
                    posture_positive.append(f"✓ Good security headers (Score {security_headers}/100)")
                elif security_headers < 60:
                    posture_findings.append(f"⚠️ Missing security headers (Score {security_headers}/100)")
                    aggregate_score -= 3
                
                vulnerabilities = posture_data.get("vulnerabilities", {})
                if vulnerabilities:
                    critical_vulns = vulnerabilities.get("critical", 0)
                    high_vulns = vulnerabilities.get("high", 0)
                    if critical_vulns > 0:
                        posture_findings.append(f"🚨 {critical_vulns} critical vulnerabilities detected")
                        aggregate_score -= 15
                    elif high_vulns > 0:
                        posture_findings.append(f"⚠️ {high_vulns} high-severity vulnerabilities detected")
                        aggregate_score -= 8

            # Cap aggregate score at valid range
            aggregate_score = max(0, min(100, aggregate_score))

            # Determine overall risk level
            def _calculate_risk_level(score: float) -> str:
                if score >= 80:
                    return "LOW"
                elif score >= 60:
                    return "MEDIUM"
                elif score >= 40:
                    return "HIGH"
                else:
                    return "CRITICAL"

            overall_risk_level = _calculate_risk_level(aggregate_score)

            # Generate actionable recommendations based on findings
            recommendations = []

            # Critical findings from assessments
            if all_findings:
                unique_findings = list(set(all_findings))[:5]  # Top 5 unique
                recommendations.append({
                    "priority": "CRITICAL",
                    "category": "Assessment Gaps",
                    "items": unique_findings,
                    "action": "Address critical control gaps before vendor approval. Require remediation plan with timeline.",
                })

            # Vendor intelligence risks
            if intel_risk_factors:
                recommendations.append({
                    "priority": "HIGH",
                    "category": "Vendor Intelligence",
                    "items": intel_risk_factors,
                    "action": "Review breach incidents and remediation plans. Request third-party audit reports.",
                })

            # Security posture issues
            if posture_findings:
                recommendations.append({
                    "priority": "HIGH",
                    "category": "External Security Posture",
                    "items": posture_findings,
                    "action": "Conduct penetration test or request recent security assessment. Implement continuous monitoring.",
                })

            # Compliance gaps
            if all_compliance_gaps:
                top_gaps = [(reg, len(gaps)) for reg, gaps in sorted(
                    all_compliance_gaps.items(), 
                    key=lambda x: len(x[1]), 
                    reverse=True
                )][:3]
                
                if top_gaps:
                    recommendations.append({
                        "priority": "MEDIUM",
                        "category": "Regulatory Compliance",
                        "items": [f"{reg}: {count} gap(s)" for reg, count in top_gaps],
                        "action": "Request compliance documentation and evidence. Consider regulatory attestation requirement.",
                    })

            # Low score overall
            if aggregate_score < 60:
                recommendations.append({
                    "priority": "CRITICAL",
                    "category": "Overall Risk",
                    "items": [f"Aggregate risk score: {aggregate_score:.1f}/100 (below acceptable threshold)"],
                    "action": "DO NOT APPROVE vendor without significant risk mitigation. Consider alternative vendors.",
                })

            # Format comprehensive report
            text = f"# Third-Party Risk Management Report\n\n"
            text += f"## Vendor: {vendor_name}\n"
            text += f"**Generated:** {datetime.now(UTC).isoformat()}\n\n"

            # Executive Summary
            text += "---\n\n"
            text += "## Executive Summary\n\n"
            text += f"**Overall Risk Score:** {aggregate_score:.1f}/100\n"
            text += f"**Risk Level:** {overall_risk_level}\n"
            text += f"**Assessments Completed:** {len(assessments_data)}\n"
            
            if len(overall_scores) > 0:
                text += f"**Average Assessment Score:** {sum(overall_scores) / len(overall_scores):.1f}/100\n"
                text += f"**Score Range:** {min(overall_scores):.1f} - {max(overall_scores):.1f}\n"
            
            text += "\n"

            # Risk indicator
            if overall_risk_level == "CRITICAL":
                text += "🚨 **CRITICAL RISK**: This vendor poses significant security and compliance risks.\n\n"
            elif overall_risk_level == "HIGH":
                text += "⚠️ **HIGH RISK**: This vendor requires remediation before approval.\n\n"
            elif overall_risk_level == "MEDIUM":
                text += "⚡ **MEDIUM RISK**: This vendor is acceptable with ongoing monitoring.\n\n"
            else:
                text += "✓ **LOW RISK**: This vendor meets security and compliance requirements.\n\n"

            # Assessment Details
            if assessments_data:
                text += "### Assessment Details\n\n"
                for assessment in assessments_data:
                    text += f"- **{assessment['id']}**: {assessment['score']:.1f}/100 ({assessment['risk']}) - {assessment['strictness']} strictness\n"
                text += "\n"

            # Positive Factors
            if intel_positive_factors or posture_positive:
                text += "### Positive Factors\n\n"
                for factor in intel_positive_factors + posture_positive:
                    text += f"{factor}\n"
                text += "\n"

            # Risk Factors
            if intel_risk_factors or posture_findings:
                text += "### Risk Factors\n\n"
                for factor in intel_risk_factors + posture_findings:
                    text += f"{factor}\n"
                text += "\n"

            # Critical Findings
            if all_findings:
                text += f"### Critical Findings ({len(all_findings)} total)\n\n"
                for finding in list(set(all_findings))[:10]:  # Top 10 unique
                    text += f"- {finding}\n"
                if len(all_findings) > 10:
                    text += f"\n*... and {len(all_findings) - 10} more findings*\n"
                text += "\n"

            # Compliance Gaps Summary
            if all_compliance_gaps:
                text += "### Compliance Gaps\n\n"
                for reg, gaps in sorted(all_compliance_gaps.items(), key=lambda x: len(x[1]), reverse=True):
                    text += f"- **{reg}**: {len(gaps)} question(s) with gaps\n"
                text += "\n"

            # Recommendations
            if include_recs and recommendations:
                text += "---\n\n"
                text += "## Recommendations\n\n"
                
                for rec in recommendations:
                    text += f"### [{rec['priority']}] {rec['category']}\n\n"
                    
                    if rec['items']:
                        for item in rec['items']:
                            text += f"- {item}\n"
                        text += "\n"
                    
                    text += f"**Action:** {rec['action']}\n\n"

            # Data Sources
            text += "---\n\n"
            text += "## Data Sources\n\n"
            text += "This report aggregates data from:\n\n"
            
            if assessments_data:
                text += f"✓ **TPRM Questionnaire Assessments** ({len(assessments_data)} assessment(s))\n"
            
            if vendor_intel:
                text += "✓ **Vendor Intelligence Data** (company profile, certifications, breach history)\n"
            
            if posture_data:
                text += "✓ **External Security Posture** (SSL/TLS, security headers, vulnerabilities)\n"
            
            text += "\n"

            # Vendor Intelligence Details (optional)
            if vendor_intel:
                text += "### Vendor Intelligence Details\n\n"
                text += f"```json\n{json.dumps(vendor_intel, indent=2)}\n```\n\n"

            # Security Posture Details (optional)
            if posture_data:
                text += "### External Security Posture Details\n\n"
                text += f"```json\n{json.dumps(posture_data, indent=2)}\n```\n\n"

            return [TextContent(type="text", text=text)]

        except StorageError as e:
            logger.error("Storage error during report generation", extra={"error": str(e)}, exc_info=True)
            return [TextContent(type="text", text=f"Error: Failed to load assessment data - {str(e)}")]
        except Exception as e:
            logger.error("Unexpected error during report generation", exc_info=True)
            return [TextContent(type="text", text=f"Error: Unexpected error - {str(e)}")]


    elif name == "get_questionnaire":
        questionnaire_id = arguments["questionnaire_id"]

        # Try cache first, then storage
        questionnaire = generated_questionnaires.get(questionnaire_id)
        if not questionnaire:
            questionnaire = storage.get_questionnaire(questionnaire_id)
            if questionnaire:
                # Cache for future use
                generated_questionnaires[questionnaire_id] = questionnaire

        if not questionnaire:
            return [
                TextContent(
                    type="text",
                    text=f"Questionnaire '{questionnaire_id}' not found.",
                )
            ]

        result = {
            "questionnaire_id": questionnaire.id,
            "framework": questionnaire.metadata.framework.value,
            "version": questionnaire.metadata.version,
            "total_questions": questionnaire.metadata.total_questions,
            "categories": questionnaire.metadata.categories,
            "generated": questionnaire.generation_timestamp,
            "questions": [
                {
                    "id": q.id,
                    "category": q.category,
                    "question_text": q.question_text,
                    "weight": q.weight,
                    "scf_controls": q.scf_control_mappings,
                }
                for q in questionnaire.questions
            ],
        }

        return [
            TextContent(
                type="text",
                text=f"**Questionnaire:** {questionnaire_id}\n\n"
                f"```json\n{json.dumps(result, indent=2)}\n```",
            )
        ]

    elif name == "search_questions":
        query = arguments.get("query") or arguments.get("keyword")
        framework = arguments.get("framework")
        limit = arguments.get("limit", 20)

        results = data_loader.search_questions(query, framework)[:limit]

        if not results:
            return [TextContent(type="text", text=f"No questions found matching '{query}'.")]

        text = f"**Found {len(results)} question(s) matching '{query}'**\n\n"

        for q in results:
            text += f"### {q.id} ({q.category})\n"
            text += f"**Q:** {q.question_text}\n"
            if q.scf_control_mappings:
                text += f"**SCF Controls:** {', '.join(q.scf_control_mappings)}\n"
            text += f"**Weight:** {q.weight}/10\n\n"

        return [TextContent(type="text", text=text)]

    elif name == "get_vendor_history":
        vendor_name = arguments.get("vendor_name", "Vendor")
        limit = arguments.get("limit", 10)

        # Get assessment history
        assessments = storage.get_vendor_history(vendor_name, limit)

        if not assessments:
            return [
                TextContent(
                    type="text",
                    text=f"No assessment history found for vendor '{vendor_name}'.",
                )
            ]

        # Calculate trend
        text = f"**Assessment History: {vendor_name}**\n\n"
        text += f"**Total Assessments:** {len(assessments)}\n\n"

        # Show trend if we have multiple assessments
        if len(assessments) >= 2:
            latest = assessments[0]
            oldest = assessments[-1]
            score_delta = latest["overall_score"] - oldest["overall_score"]

            text += "**Trend Analysis:**\n"
            text += f"- Latest Score: {latest['overall_score']:.1f} ({latest['risk_level']})\n"
            text += f"- Oldest Score: {oldest['overall_score']:.1f} ({oldest['risk_level']})\n"
            text += f"- Change: {score_delta:+.1f} points\n"

            if score_delta > 5:
                text += "- **Trend:** Improving\n\n"
            elif score_delta < -5:
                text += "- **Trend:** Degrading\n\n"
            else:
                text += "- **Trend:** Stable\n\n"

        # List all assessments
        text += "**Assessment History:**\n\n"
        for i, assessment in enumerate(assessments, 1):
            text += f"{i}. **Assessment ID {assessment['assessment_id']}**\n"
            text += f"   - Date: {assessment['assessed_at']}\n"
            text += f"   - Score: {assessment['overall_score']:.1f}/100\n"
            text += f"   - Risk Level: {assessment['risk_level']}\n"
            text += f"   - Framework: {assessment['framework']}\n\n"

        # JSON output
        result_json = {
            "vendor_name": vendor_name,
            "total_assessments": len(assessments),
            "assessments": assessments,
        }

        if len(assessments) >= 2:
            result_json["trend"] = {
                "latest_score": assessments[0]["overall_score"],
                "oldest_score": assessments[-1]["overall_score"],
                "delta": score_delta,
                "direction": "improving" if score_delta > 5 else "degrading" if score_delta < -5 else "stable",
            }

        text += f"\n```json\n{json.dumps(result_json, indent=2)}\n```"

        return [TextContent(type="text", text=text)]

    elif name == "compare_assessments":
        vendor_name = arguments.get("vendor_name", "Vendor")
        assessment_id_1 = arguments.get("assessment_id_1")
        assessment_id_2 = arguments.get("assessment_id_2")

        # If IDs not provided, get the two most recent
        if not assessment_id_1 or not assessment_id_2:
            recent = storage.get_vendor_history(vendor_name, limit=2)
            if len(recent) < 2:
                return [
                    TextContent(
                        type="text",
                        text=f"Vendor '{vendor_name}' needs at least 2 assessments for comparison.",
                    )
                ]
            assessment_id_1 = recent[0]["assessment_id"]
            assessment_id_2 = recent[1]["assessment_id"]

        # Use storage's compare_assessments method
        try:
            comparison = storage.compare_assessments(vendor_name, assessment_id_1, assessment_id_2)
        except AssessmentNotFoundError as e:
            logger.warning("Assessment not found for comparison", extra={"error": str(e)})
            return [
                TextContent(
                    type="text",
                    text=f"Error: Assessment not found - {str(e)}",
                )
            ]
    elif name == "check_regulatory_compliance":
        assessment_id = arguments["assessment_id"]
        regulation = arguments["regulation"]

        # Get assessment results from storage (returns dict)
        assessment_data = storage.get_assessment_details(assessment_id)

        if not assessment_data:
            return [
                TextContent(
                    type="text",
                    text=f"Assessment ID {assessment_id} not found.",
                )
            ]

        # Get the original questionnaire to access regulatory mappings
        questionnaire_id = assessment_data.get("questionnaire_id")
        questionnaire = storage.get_questionnaire(questionnaire_id)

        if not questionnaire:
            return [
                TextContent(
                    type="text",
                    text=f"Questionnaire {questionnaire_id} not found. Cannot check compliance.",
                )
            ]

        # Enrich evaluation results with regulatory mappings from original questions
        evaluation_results = assessment_data.get("evaluation_results", [])
        enriched_results = []
        
        for result in evaluation_results:
            # Find corresponding question in questionnaire
            question = next(
                (q for q in questionnaire.questions if q.id == result.get("question_id")),
                None
            )
            
            if question:
                # Create enriched result with regulatory mappings
                enriched_result = {
                    "question_id": result.get("question_id"),
                    "status": result.get("status"),
                    "score": result.get("score", 0),
                    "risk_level": result.get("risk_level", "low"),
                    "findings": result.get("findings", []),
                    "recommendations": result.get("recommendations", []),
                    "regulatory_mappings": question.regulatory_mappings or [],
                    "regulatory_source": question.regulatory_source or "",
                    "question_text": question.question_text,
                }
                enriched_results.append(enriched_result)

        # Check compliance with enriched results
        compliance = await check_regulatory_compliance(
            enriched_results,
            regulation
        )

        # Format output
        text = f"**{regulation.upper()} Compliance Check**\n\n"
        text += f"**Assessment ID:** {assessment_id}\n"
        text += f"**Vendor:** {assessment_data.get('vendor_name', 'Unknown')}\n\n"

        text += f"**Compliance Status:** {compliance['status'].upper()}\n"
        text += f"**Coverage:** {compliance['coverage']:.1f}%\n"
        text += f"**Total Questions:** {compliance['total_questions']}\n"
        text += f"**Acceptable Responses:** {compliance.get('acceptable', 0)}\n"
        text += f"**Gaps Found:** {compliance['gaps_count']}\n\n"

        if compliance['gaps_count'] > 0:
            text += f"**Compliance Gaps ({compliance['gaps_count']}):**\n"
            for gap in compliance['gaps'][:10]:
                text += f"- {gap['question_id']}: {gap['status']}\n"
                if gap.get('findings'):
                    text += f"  Findings: {', '.join(gap['findings'][:2])}\n"
            if compliance['gaps_count'] > 10:
                text += f"  ... and {compliance['gaps_count'] - 10} more gaps\n"

        text += f"\n```json\n{json.dumps(compliance, indent=2)}\n```"

        return [TextContent(type="text", text=text)]
    elif name == "generate_dora_questionnaire":
        category = arguments.get("category", "ICT_third_party")
        scope = arguments.get("scope", "full")

        # Fetch DORA requirements from eu-regulations-mcp
        requirements = await get_dora_requirements(category)

        if not requirements:
            return [
                TextContent(
                    type="text",
                    text=f"No DORA requirements found for category '{category}'.",
                )
            ]

        # Generate questions from regulatory articles
        questions_data = await generate_questions_from_articles(requirements, "dora")

        # Convert to Question objects
        questions = [Question(**q) for q in questions_data]

        # Create questionnaire
        questionnaire_id = str(uuid.uuid4())
        metadata = QuestionnaireMetadata(
            framework=QuestionnaireFramework.DORA_ICT_TPP,
            version="DORA 2024",
            total_questions=len(questions),
            categories=list(set(q.category for q in questions)),
            estimated_completion_time=f"{len(questions) * 5} minutes",
            scope=scope,
            applicable_regulations=["DORA"],
        )

        questionnaire = Questionnaire(
            id=questionnaire_id,
            metadata=metadata,
            questions=questions,
            generation_timestamp=datetime.now(UTC).isoformat(),
            custom_parameters={
                "source": "eu-regulations-mcp",
                "category": category,
                "scope": scope,
            },
        )

        # Store questionnaire
        storage.save_questionnaire(questionnaire)
        generated_questionnaires[questionnaire_id] = questionnaire

        # Get article mapping
        article_map = await map_questions_to_articles(questions_data)

        # Format output
        text = f"**DORA Questionnaire Generated from EU Regulations**\n\n"
        text += f"**ID:** `{questionnaire_id}`\n"
        text += f"**Category:** {category}\n"
        text += f"**Total Questions:** {len(questions)}\n"
        text += f"**Scope:** {scope}\n"
        text += f"**Source:** EU Regulations (DORA Articles)\n\n"

        text += "**Regulatory Coverage:**\n"
        for article, question_ids in sorted(article_map.items())[:10]:
            text += f"- {article}: {len(question_ids)} questions\n"

        result = {
            "questionnaire_id": questionnaire_id,
            "framework": "dora_ict_tpp",
            "category": category,
            "total_questions": len(questions),
            "regulatory_coverage": {k: len(v) for k, v in article_map.items()},
            "questions": [
                {
                    "id": q.id,
                    "question_text": q.question_text,
                    "category": q.category,
                    "regulatory_mappings": q.regulatory_mappings,
                    "scf_controls": q.scf_control_mappings,
                    "weight": q.weight,
                }
                for q in questions
            ],
        }

        text += f"\n```json\n{json.dumps(result, indent=2)}\n```"

        return [TextContent(type="text", text=text)]

    elif name == "generate_nis2_questionnaire":
        category = arguments.get("category", "supply_chain")
        scope = arguments.get("scope", "full")

        # Fetch NIS2 requirements from eu-regulations-mcp
        requirements = await get_nis2_requirements(category)

        if not requirements:
            return [
                TextContent(
                    type="text",
                    text=f"No NIS2 requirements found for category '{category}'.",
                )
            ]

        # Generate questions from regulatory articles
        questions_data = await generate_questions_from_articles(requirements, "nis2")

        # Convert to Question objects
        questions = [Question(**q) for q in questions_data]

        # Create questionnaire
        questionnaire_id = str(uuid.uuid4())
        metadata = QuestionnaireMetadata(
            framework=QuestionnaireFramework.NIS2_SUPPLY_CHAIN,
            version="NIS2 2024",
            total_questions=len(questions),
            categories=list(set(q.category for q in questions)),
            estimated_completion_time=f"{len(questions) * 5} minutes",
            scope=scope,
            applicable_regulations=["NIS2"],
        )

        questionnaire = Questionnaire(
            id=questionnaire_id,
            metadata=metadata,
            questions=questions,
            generation_timestamp=datetime.now(UTC).isoformat(),
            custom_parameters={
                "source": "eu-regulations-mcp",
                "category": category,
                "scope": scope,
            },
        )

        # Store questionnaire
        storage.save_questionnaire(questionnaire)
        generated_questionnaires[questionnaire_id] = questionnaire

        # Get article mapping
        article_map = await map_questions_to_articles(questions_data)

        # Format output
        text = f"**NIS2 Questionnaire Generated from EU Regulations**\n\n"
        text += f"**ID:** `{questionnaire_id}`\n"
        text += f"**Category:** {category}\n"
        text += f"**Total Questions:** {len(questions)}\n"
        text += f"**Scope:** {scope}\n"
        text += f"**Source:** EU Regulations (NIS2 Articles)\n\n"

        text += "**Regulatory Coverage:**\n"
        for article, question_ids in sorted(article_map.items())[:10]:
            text += f"- {article}: {len(question_ids)} questions\n"

        result = {
            "questionnaire_id": questionnaire_id,
            "framework": "nis2_supply_chain",
            "category": category,
            "total_questions": len(questions),
            "regulatory_coverage": {k: len(v) for k, v in article_map.items()},
            "questions": [
                {
                    "id": q.id,
                    "question_text": q.question_text,
                    "category": q.category,
                    "regulatory_mappings": q.regulatory_mappings,
                    "scf_controls": q.scf_control_mappings,
                    "weight": q.weight,
                }
                for q in questions
            ],
        }

        text += f"\n```json\n{json.dumps(result, indent=2)}\n```"

        return [TextContent(type="text", text=text)]

    elif name == "check_regulatory_compliance":
        assessment_id = arguments["assessment_id"]
        regulation = arguments["regulation"]

        # Get assessment results from storage
        assessment_results = storage.get_assessment_details(assessment_id)

        if not assessment_results:
            return [
                TextContent(
                    type="text",
                    text=f"Assessment ID {assessment_id} not found.",
                )
            ]

        # Check compliance
        compliance = await check_regulatory_compliance(
            assessment_results.get("evaluation_results", []),
            regulation
        )

        # Format output
        text = f"**{regulation} Compliance Check**\n\n"
        text += f"**Assessment ID:** {assessment_id}\n"
        text += f"**Vendor:** {assessment_results.get('vendor_name', 'Unknown')}\n\n"

        text += f"**Compliance Status:** {compliance['status'].upper()}\n"
        text += f"**Coverage:** {compliance['coverage']:.1f}%\n"
        text += f"**Total Questions:** {compliance['total_questions']}\n"
        text += f"**Acceptable Responses:** {compliance.get('acceptable', 0)}\n"
        text += f"**Gaps Found:** {compliance['gaps_count']}\n\n"

        if compliance['gaps_count'] > 0:
            text += f"**Compliance Gaps ({compliance['gaps_count']}):**\n"
            for gap in compliance['gaps'][:10]:
                text += f"- {gap['question_id']}: {gap['status']}\n"
                if gap.get('findings'):
                    text += f"  Findings: {', '.join(gap['findings'][:2])}\n"
            if compliance['gaps_count'] > 10:
                text += f"  ... and {compliance['gaps_count'] - 10} more gaps\n"

        text += f"\n```json\n{json.dumps(compliance, indent=2)}\n```"

        return [TextContent(type="text", text=text)]

    elif name == "get_regulatory_timeline":
        regulation = arguments["regulation"]

        # Get compliance timeline
        timeline = await get_compliance_timeline(regulation)

        # Format output
        text = f"**{regulation} Compliance Timeline**\n\n"
        text += f"**Regulation:** {timeline['regulation']}\n"
        text += f"**Final Deadline:** {timeline['final_deadline']}\n"

        if timeline.get('days_until_deadline') is not None:
            days = timeline['days_until_deadline']
            if timeline.get('is_overdue'):
                text += f"**Status:** ⚠️ OVERDUE by {abs(days)} days\n\n"
            else:
                text += f"**Days Until Deadline:** {days}\n\n"

        text += "**Key Milestones:**\n"
        for milestone in timeline.get('milestones', []):
            text += f"- **{milestone['date']}**: {milestone['description']}\n"

        text += f"\n```json\n{json.dumps(timeline, indent=2)}\n```"

        return [TextContent(type="text", text=text)]

    elif name == "upload_evidence_document":
        try:
            import base64

            vendor_name = arguments.get("vendor_name", "Vendor")
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

    else:
        raise ValueError(f"Unknown tool: {name}")


async def _list_resources() -> list:
    """List available resources (health check endpoint)."""
    return []


def create_mcp_server() -> Server:
    """Create a fresh MCP Server instance with all handlers registered.

    Returns a new Server each call. The Python SDK's StreamableHTTPSessionManager
    handles concurrent sessions against a single instance, but the factory keeps
    handler registration separate from instance lifecycle.
    """
    server = Server("tprm-frameworks-mcp")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return await _get_tool_definitions()

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        return await _dispatch_tool_call(name, arguments)

    @server.list_resources()
    async def list_resources() -> list:
        return await _list_resources()

    return server


# Module-level instance for stdio mode (single transport, no concurrency issue)
app = create_mcp_server()


async def health_check() -> dict[str, Any]:
    """Enhanced health check with comprehensive metrics."""
    try:
        import psutil

        # Get process metrics
        process = psutil.Process()
        memory_info = process.memory_info()

        # Get framework info
        frameworks = data_loader.get_all_frameworks()

        # Get storage status
        storage_status = storage.verify_storage()

        # Calculate uptime (tracked at module level)
        uptime_seconds = time.time() - getattr(health_check, 'start_time', time.time())

        return {
            "status": "healthy",
            "version": SERVER_VERSION,
            "server": "tprm-frameworks-mcp",
            "uptime_seconds": round(uptime_seconds, 2),
            "frameworks": {
                "loaded": len(frameworks),
                "frameworks": [f["key"] for f in frameworks]
            },
            "storage": {
                "status": storage_status.get("status"),
                "total_questionnaires": storage_status.get("total_questionnaires", 0),
                "total_assessments": storage_status.get("total_assessments", 0),
                "total_vendors": storage_status.get("total_vendors", 0),
                "database_size_mb": round(storage_status.get("database_size_bytes", 0) / 1_048_576, 2),
                "database_path": storage_status.get("database_path")
            },
            "memory": {
                "rss_mb": round(memory_info.rss / 1_048_576, 2),
                "vms_mb": round(memory_info.vms / 1_048_576, 2)
            },
            "tools_available": 16,
            "timestamp": datetime.now(UTC).isoformat()
        }
    except DataLoadError as e:
        logger.error("Data loading error in health check", extra={"error": e.to_dict()}, exc_info=True)
        return {
            "status": "unhealthy",
            "error": f"Data loading error: {e.message}",
            "timestamp": datetime.now(UTC).isoformat()
        }
    except StorageError as e:
        logger.error("Storage error in health check", extra={"error": str(e)}, exc_info=True)
        return {
            "status": "degraded",
            "error": f"Storage error: {str(e)}",
            "timestamp": datetime.now(UTC).isoformat()
        }
    except Exception as e:
        logger.critical("Health check failed", exc_info=True)
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now(UTC).isoformat()
        }

# Track start time at module level
health_check.start_time = time.time()


async def main():
    """Main entry point for the server."""
    # Perform startup health check
    health = await health_check()
    if health["status"] != "healthy":
        logger.error(
            "Server health check failed",
            extra={"error": health.get("error"), "status": "unhealthy"}
        )
        return

    logger.info(
        "TPRM Frameworks MCP Server starting",
        extra={
            "version": SERVER_VERSION,
            "status": "starting"
        }
    )

    # Framework information
    frameworks_info = health.get("frameworks", {})
    logger.info(
        "Frameworks loaded",
        extra={
            "loaded_count": frameworks_info.get('loaded', 0),
            "frameworks": frameworks_info.get('frameworks', [])
        }
    )
    logger.info(
        "Tools available",
        extra={"tools_available": health['tools_available']}
    )

    # Memory information
    memory_info = health.get("memory", {})
    logger.info(
        "Memory status",
        extra={
            "rss_mb": memory_info.get('rss_mb', 0),
            "vms_mb": memory_info.get('vms_mb', 0)
        }
    )

    # Log storage information
    storage_info = health.get("storage", {})
    if storage_info.get("status") == "healthy":
        logger.info(
            "Storage initialized successfully",
            extra={
                "database_path": storage_info.get('database_path', 'unknown'),
                "total_questionnaires": storage_info.get('total_questionnaires', 0),
                "total_assessments": storage_info.get('total_assessments', 0),
                "total_vendors": storage_info.get('total_vendors', 0),
                "database_size_mb": storage_info.get('database_size_mb', 0)
            }
        )
    else:
        logger.warning(
            "Storage initialization warning",
            extra={"error": storage_info.get('error', 'Unknown error')}
        )

    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
