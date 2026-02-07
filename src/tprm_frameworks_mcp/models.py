"""Data models for TPRM questionnaires and assessments."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class QuestionnaireFramework(str, Enum):
    """Supported questionnaire frameworks."""

    SIG_FULL = "sig_full"
    SIG_LITE = "sig_lite"
    CAIQ_V4 = "caiq_v4"
    CAIQ_V4_FULL = "caiq_v4_full"
    VSA = "vsa"
    DORA_ICT_TPP = "dora_ict_tpp"
    NIS2_SUPPLY_CHAIN = "nis2_supply_chain"


class EntityType(str, Enum):
    """Types of entities being assessed."""

    SAAS_PROVIDER = "saas_provider"
    CLOUD_PROVIDER = "cloud_provider"
    DATA_PROCESSOR = "data_processor"
    ICT_PROVIDER = "ict_provider"
    FINANCIAL_INSTITUTION = "financial_institution"
    HEALTHCARE_PROVIDER = "healthcare_provider"
    GENERIC_VENDOR = "generic_vendor"


class ResponseStrictness(str, Enum):
    """Evaluation strictness levels."""

    LENIENT = "lenient"  # Accept partial answers
    MODERATE = "moderate"  # Standard evaluation
    STRICT = "strict"  # Require comprehensive answers


class RiskLevel(str, Enum):
    """Risk assessment levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


class AnswerStatus(str, Enum):
    """Status of a question response."""

    ACCEPTABLE = "acceptable"
    PARTIALLY_ACCEPTABLE = "partially_acceptable"
    UNACCEPTABLE = "unacceptable"
    NOT_APPLICABLE = "not_applicable"
    UNANSWERED = "unanswered"


@dataclass
class Question:
    """A single questionnaire question."""

    id: str
    category: str
    subcategory: str | None
    question_text: str
    description: str | None
    expected_answer_type: str  # text, yes_no, multiple_choice, file_upload
    is_required: bool
    weight: int  # 1-10, importance of this question
    regulatory_mappings: list[str] = field(default_factory=list)
    scf_control_mappings: list[str] = field(default_factory=list)
    risk_if_inadequate: RiskLevel = RiskLevel.MEDIUM
    evaluation_rubric: dict[str, Any] = field(default_factory=dict)
    ccm_control_id: str | None = None  # Cloud Controls Matrix control ID (for CAIQ)
    regulatory_source: dict[str, Any] | None = None  # Structured regulatory traceability (DORA/NIS2)
    required_evidence: list[str] = field(default_factory=list)  # Evidence requirements (DORA only)  # Cloud Controls Matrix control ID (for CAIQ)
    nis2_crossreference: str | None = None  # Cross-reference to NIS2 articles


@dataclass
class QuestionnaireMetadata:
    """Metadata about a questionnaire."""

    framework: QuestionnaireFramework
    version: str
    total_questions: int
    categories: list[str]
    estimated_completion_time: str
    scope: str | None = None
    entity_type: EntityType | None = None
    applicable_regulations: list[str] = field(default_factory=list)


@dataclass
class Questionnaire:
    """A complete questionnaire."""

    id: str
    metadata: QuestionnaireMetadata
    questions: list[Question]
    generation_timestamp: str
    custom_parameters: dict[str, Any] = field(default_factory=dict)


@dataclass
class QuestionResponse:
    """Response to a single question."""

    question_id: str
    answer: str | None
    supporting_documents: list[str] = field(default_factory=list)
    notes: str | None = None


@dataclass
class EvaluationResult:
    """Evaluation result for a single question."""

    question_id: str
    status: AnswerStatus
    score: float  # 0-100
    risk_level: RiskLevel
    findings: list[str]
    recommendations: list[str]
    scf_controls_addressed: list[str] = field(default_factory=list)


@dataclass
class AssessmentResult:
    """Complete assessment result."""

    questionnaire_id: str
    vendor_name: str
    evaluation_results: list[EvaluationResult]
    overall_score: float
    overall_risk_level: RiskLevel
    critical_findings: list[str]
    compliance_gaps: dict[str, list[str]]  # regulation -> list of gaps
    timestamp: str
    strictness_level: ResponseStrictness


@dataclass
class ControlMapping:
    """Mapping between questionnaire questions and SCF controls."""

    question_id: str
    scf_control_id: str
    mapping_strength: float  # 0-1, how strongly they relate
    rationale: str
