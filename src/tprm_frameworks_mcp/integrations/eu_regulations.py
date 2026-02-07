"""
Integration layer for eu-regulations-mcp

Provides:
- Fetch DORA/NIS2 articles and requirements
- Generate dynamic questionnaires from regulations
- Map questions to regulatory articles
- Track compliance deadlines
"""

import asyncio
import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from ..logging_config import get_logger
from ..models import Question, RiskLevel

logger = get_logger("integrations.eu_regulations")


def _to_risk_level(risk_str: str) -> RiskLevel:
    """Convert string to RiskLevel enum."""
    risk_map = {
        "critical": RiskLevel.CRITICAL,
        "high": RiskLevel.HIGH,
        "medium": RiskLevel.MEDIUM,
        "low": RiskLevel.LOW,
        "informational": RiskLevel.INFORMATIONAL,
    }
    return risk_map.get(risk_str.lower(), RiskLevel.MEDIUM)


@dataclass
class RegulatoryRequirement:
    """A regulatory requirement from DORA or NIS2."""

    regulation: str  # "DORA" or "NIS2"
    article: str  # e.g., "Article 28"
    paragraph: Optional[str] = None  # e.g., "1(a)"
    requirement_text: str = ""
    deadline: Optional[str] = None
    category: str = "General"
    scf_controls: List[str] = field(default_factory=list)
    question_templates: List[str] = field(default_factory=list)
    required_evidence: List[str] = field(default_factory=list)


@dataclass
class RegulatoryArticle:
    """A full regulatory article with metadata."""

    regulation: str
    article_number: str
    title: str
    full_text: str
    requirements: List[RegulatoryRequirement] = field(default_factory=list)
    related_articles: List[str] = field(default_factory=list)


class EURegulationsClient:
    """
    Client for eu-regulations-mcp server.

    Falls back to local data if server is unavailable.
    """

    def __init__(self, server_url: Optional[str] = None):
        """
        Initialize the EU regulations client.

        Args:
            server_url: URL to eu-regulations-mcp server (if available)
                       Format: "command:args" for stdio or "http://..." for HTTP
        """
        self.server_url = server_url or os.environ.get("EU_REGULATIONS_MCP_URL")
        self.data_dir = Path(__file__).parent.parent / "data"
        self.mapping_file = self.data_dir / "eu-regulations-mapping.json"
        self._mapping_cache: Optional[Dict] = None

    async def is_server_available(self) -> bool:
        """Check if the eu-regulations-mcp server is available."""
        if not self.server_url:
            return False
        
        try:
            async with asyncio.timeout(3):
                # Parse server URL to determine transport type
                if self.server_url.startswith(("http://", "https://")):
                    # HTTP transport - not yet implemented
                    # For now, return False and use local fallback
                    logger.debug(f"HTTP transport not yet implemented for {self.server_url}")
                    return False
                
                # Assume stdio transport (command)
                # server_url format: "command:args" or just "command"
                parts = self.server_url.split(":", 1)
                command = parts[0]
                args = parts[1].split() if len(parts) > 1 else []
                
                server_params = StdioServerParameters(
                    command=command,
                    args=args,
                    env=None
                )
                
                # Try to connect and list tools as a health check
                async with stdio_client(server_params) as (read, write):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        # If we can list tools, server is available
                        tools = await session.list_tools()
                        logger.info(f"EU regulations MCP server available with {len(tools.tools)} tools")
                        return True
                        
        except asyncio.TimeoutError:
            logger.warning("EU regulations MCP server connection timeout, using local fallback")
            return False
        except FileNotFoundError as e:
            logger.debug(f"EU regulations MCP server command not found: {e}, using local fallback")
            return False
        except Exception as e:
            logger.warning(f"EU regulations MCP server unavailable: {e}, using local fallback")
            return False

    def _load_mapping_data(self) -> Dict:
        """Load EU regulations mapping data from local JSON file."""
        if self._mapping_cache:
            return self._mapping_cache

        if not self.mapping_file.exists():
            # Return minimal default structure
            return {
                "dora": {},
                "nis2": {},
                "deadlines": {
                    "dora": "2025-01-17",
                    "nis2": "2024-10-17"
                }
            }

        with open(self.mapping_file, "r") as f:
            self._mapping_cache = json.load(f)

        return self._mapping_cache

    async def get_dora_articles(self, category: str = "ICT_third_party") -> List[RegulatoryArticle]:
        """
        Fetch DORA articles related to a specific category.

        Args:
            category: Category of requirements (ICT_third_party, ICT_risk, incident_reporting, etc.)

        Returns:
            List of regulatory articles
        """
        # Check if server is available
        if await self.is_server_available():
            return await self._fetch_from_server("dora", category)

        # Fall back to local data
        return self._fetch_from_local("dora", category)

    async def get_nis2_articles(self, category: str = "supply_chain") -> List[RegulatoryArticle]:
        """
        Fetch NIS2 articles related to a specific category.

        Args:
            category: Category of requirements (supply_chain, risk_management, incident_response, etc.)

        Returns:
            List of regulatory articles
        """
        # Check if server is available
        if await self.is_server_available():
            return await self._fetch_from_server("nis2", category)

        # Fall back to local data
        return self._fetch_from_local("nis2", category)

    async def _fetch_from_server(self, regulation: str, category: str) -> List[RegulatoryArticle]:
        """Fetch articles from eu-regulations-mcp server."""
        try:
            # Parse server URL
            parts = self.server_url.split(":", 1)
            command = parts[0]
            args = parts[1].split() if len(parts) > 1 else []
            
            server_params = StdioServerParameters(
                command=command,
                args=args,
                env=None
            )
            
            async with asyncio.timeout(10):
                async with stdio_client(server_params) as (read, write):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        
                        # Determine which tool to call based on regulation
                        if regulation.lower() == "dora":
                            tool_name = "get_dora_requirements"
                        elif regulation.lower() == "nis2":
                            tool_name = "get_nis2_requirements"
                        else:
                            logger.warning(f"Unknown regulation: {regulation}")
                            return self._fetch_from_local(regulation, category)
                        
                        # Call the MCP tool
                        result = await session.call_tool(
                            tool_name,
                            arguments={"category": category}
                        )
                        
                        # Parse response
                        # MCP tool results come back as a list of TextContent
                        if not result.content:
                            logger.warning(f"Empty response from {tool_name}")
                            return self._fetch_from_local(regulation, category)
                        
                        # Extract JSON from content
                        content_text = result.content[0].text if result.content else "{}"
                        data = json.loads(content_text)
                        
                        # Convert to RegulatoryArticle objects
                        articles = []
                        for article_data in data.get("articles", []):
                            # Convert requirements
                            requirements = []
                            for req_data in article_data.get("requirements", []):
                                req = RegulatoryRequirement(
                                    regulation=req_data.get("regulation", regulation.upper()),
                                    article=req_data.get("article", ""),
                                    paragraph=req_data.get("paragraph"),
                                    requirement_text=req_data.get("requirement_text", ""),
                                    deadline=req_data.get("deadline"),
                                    category=req_data.get("category", "General"),
                                    scf_controls=req_data.get("scf_controls", []),
                                    question_templates=req_data.get("question_templates", []),
                                    required_evidence=req_data.get("required_evidence", [])
                                )
                                requirements.append(req)
                            
                            # Create article
                            article = RegulatoryArticle(
                                regulation=article_data.get("regulation", regulation.upper()),
                                article_number=article_data.get("article_number", ""),
                                title=article_data.get("title", ""),
                                full_text=article_data.get("full_text", ""),
                                requirements=requirements,
                                related_articles=article_data.get("related_articles", [])
                            )
                            articles.append(article)
                        
                        logger.info(f"Fetched {len(articles)} articles from EU regulations MCP server")
                        return articles
                        
        except asyncio.TimeoutError:
            logger.warning(f"Timeout fetching {regulation} from MCP server, using local fallback")
            return self._fetch_from_local(regulation, category)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse response from MCP server: {e}, using local fallback")
            return self._fetch_from_local(regulation, category)
        except Exception as e:
            logger.error(f"Error fetching from MCP server: {e}, using local fallback")
            return self._fetch_from_local(regulation, category)

    def _fetch_from_local(self, regulation: str, category: str) -> List[RegulatoryArticle]:
        """Fetch articles from local mapping data."""
        mapping = self._load_mapping_data()
        reg_data = mapping.get(regulation.lower(), {})

        # Get category-specific articles if mapping exists
        category_mapping = mapping.get("category_mapping", {}).get(regulation.lower(), {})
        allowed_articles = None
        if category and category in category_mapping:
            allowed_articles = set(category_mapping[category])

        articles = []
        for article_key, article_data in reg_data.items():
            if not article_key.startswith("article_"):
                continue

            # Filter by category if specified
            if allowed_articles and article_key not in allowed_articles:
                continue

            # Get article category
            article_category = article_data.get("category", "General")

            # Create requirements from templates
            requirements = []
            for template in article_data.get("question_templates", []):
                req = RegulatoryRequirement(
                    regulation=regulation.upper(),
                    article=article_key.replace("_", " ").title(),
                    requirement_text=template,
                    category=article_category,
                    scf_controls=article_data.get("scf_controls", []),
                    question_templates=[template],
                    required_evidence=article_data.get("required_evidence", [])
                )
                requirements.append(req)

            article = RegulatoryArticle(
                regulation=regulation.upper(),
                article_number=article_key.replace("article_", ""),
                title=article_data.get("title", ""),
                full_text=article_data.get("full_text", ""),
                requirements=requirements,
                related_articles=article_data.get("related_articles", [])
            )
            articles.append(article)

        return articles

    def get_deadline(self, regulation: str) -> Optional[str]:
        """Get compliance deadline for a regulation."""
        mapping = self._load_mapping_data()
        return mapping.get("deadlines", {}).get(regulation.lower())


async def get_dora_requirements(category: str = "ICT_third_party") -> List[RegulatoryRequirement]:
    """
    Fetch DORA requirements from eu-regulations-mcp.

    Focus areas:
    - Articles 28-30: ICT third-party risk management
    - Article 11: ICT business continuity
    - Article 19: Incident reporting

    Args:
        category: Category of requirements to fetch

    Returns:
        List of regulatory requirements
    """
    client = EURegulationsClient()
    articles = await client.get_dora_articles(category)

    requirements = []
    for article in articles:
        requirements.extend(article.requirements)

    return requirements


async def get_nis2_requirements(category: str = "supply_chain") -> List[RegulatoryRequirement]:
    """
    Fetch NIS2 requirements from eu-regulations-mcp.

    Focus areas:
    - Articles 20-23: Supply chain security and third-party risk
    - Article 21: Cybersecurity risk management measures

    Args:
        category: Category of requirements to fetch

    Returns:
        List of regulatory requirements
    """
    client = EURegulationsClient()
    articles = await client.get_nis2_articles(category)

    requirements = []
    for article in articles:
        requirements.extend(article.requirements)

    return requirements


async def generate_questions_from_articles(
    requirements: List[RegulatoryRequirement],
    framework_prefix: str = "dora"
) -> List[Dict[str, Any]]:
    """
    Generate assessment questions from regulatory requirements.

    This converts regulatory articles into actionable questionnaire items
    that can be used in vendor assessments.

    Args:
        requirements: List of regulatory requirements
        framework_prefix: Prefix for question IDs (dora, nis2)

    Returns:
        List of question dictionaries
    """
    questions = []

    for i, req in enumerate(requirements, 1):
        # Use template if available, otherwise use requirement text
        question_text = req.question_templates[0] if req.question_templates else req.requirement_text

        # Determine question type
        if question_text.lower().startswith(("do you", "can you", "have you", "are you")):
            answer_type = "yes_no"
        else:
            answer_type = "text"

        # Determine weight based on SCF controls
        weight = 10 if len(req.scf_controls) >= 3 else 8

        # Build question ID
        article_num = req.article.replace("Article ", "").replace(" ", "_")
        question_id = f"{framework_prefix}_{article_num}_{i}"

        risk_level = _to_risk_level("critical" if weight == 10 else "high")

        question = {
            "id": question_id,
            "category": req.category,
            "subcategory": req.paragraph if req.paragraph else None,
            "question_text": question_text,
            "description": f"Required by {req.regulation} {req.article}",
            "expected_answer_type": answer_type,
            "is_required": True,
            "weight": weight,
            "regulatory_mappings": [f"{req.regulation} - {req.article}"],
            "scf_control_mappings": req.scf_controls,
            "risk_if_inadequate": risk_level,
            "evaluation_rubric": _generate_rubric(question_text, answer_type)
        }

        questions.append(question)

    return questions


def _generate_rubric(question_text: str, answer_type: str) -> Dict[str, Any]:
    """Generate evaluation rubric for a question."""
    if answer_type == "yes_no":
        return {
            "acceptable": ["yes", "implemented", "in place"],
            "partially_acceptable": ["partially", "in progress"],
            "unacceptable": ["no", "not implemented"],
            "required_keywords": []
        }
    else:
        # Text questions need more sophisticated rubrics
        return {
            "acceptable": ["documented", "implemented", "policy"],
            "partially_acceptable": ["planned", "partial"],
            "unacceptable": ["no", "none"],
            "required_keywords": []
        }


async def map_questions_to_articles(
    questions: List[Dict[str, Any]]
) -> Dict[str, List[str]]:
    """
    Map assessment questions back to regulatory articles.

    This creates a reverse mapping showing which questions cover which articles,
    useful for compliance gap analysis.

    Args:
        questions: List of question dictionaries

    Returns:
        Dictionary mapping article references to question IDs
    """
    article_map: Dict[str, List[str]] = {}

    for question in questions:
        for reg_mapping in question.get("regulatory_mappings", []):
            if reg_mapping not in article_map:
                article_map[reg_mapping] = []
            article_map[reg_mapping].append(question["id"])

    return article_map


async def get_compliance_timeline(regulation: str) -> Dict[str, Any]:
    """
    Get compliance timeline and milestones for a regulation.

    Args:
        regulation: Regulation name (DORA or NIS2)

    Returns:
        Timeline information with deadlines and milestones
    """
    client = EURegulationsClient()
    deadline = client.get_deadline(regulation)

    timeline = {
        "regulation": regulation.upper(),
        "final_deadline": deadline,
        "milestones": []
    }

    if regulation.upper() == "DORA":
        timeline["milestones"] = [
            {
                "date": "2024-01-17",
                "description": "DORA entered into force"
            },
            {
                "date": "2024-07-17",
                "description": "ICT risk management framework deadline (6 months)"
            },
            {
                "date": "2025-01-17",
                "description": "Full DORA compliance deadline"
            }
        ]
    elif regulation.upper() == "NIS2":
        timeline["milestones"] = [
            {
                "date": "2023-01-16",
                "description": "NIS2 entered into force"
            },
            {
                "date": "2024-10-17",
                "description": "Member states transposition deadline"
            },
            {
                "date": "2024-10-17",
                "description": "Full NIS2 compliance deadline"
            }
        ]

    # Check if deadline has passed
    if deadline:
        try:
            deadline_date = datetime.strptime(deadline, "%Y-%m-%d")
            now = datetime.now()
            timeline["days_until_deadline"] = (deadline_date - now).days
            timeline["is_overdue"] = timeline["days_until_deadline"] < 0
        except ValueError:
            timeline["days_until_deadline"] = None
            timeline["is_overdue"] = False

    return timeline


async def check_regulatory_compliance(
    assessment_results: List[Dict[str, Any]],
    regulation: str
) -> Dict[str, Any]:
    """
    Check compliance gaps against a regulation.

    Args:
        assessment_results: List of evaluation results
        regulation: Regulation to check compliance against (DORA or NIS2)

    Returns:
        Compliance report with gaps and coverage
    """
    # Extract questions that map to this regulation
    reg_questions = []
    for result in assessment_results:
        reg_mappings = result.get("regulatory_mappings", [])
        if any(regulation.upper() in mapping for mapping in reg_mappings):
            reg_questions.append(result)

    if not reg_questions:
        return {
            "regulation": regulation.upper(),
            "coverage": 0,
            "total_questions": 0,
            "gaps": [],
            "status": "not_assessed"
        }

    # Calculate coverage
    total = len(reg_questions)
    acceptable = sum(1 for q in reg_questions if q.get("status") == "acceptable")
    gaps = [
        {
            "question_id": q.get("question_id"),
            "status": q.get("status"),
            "findings": q.get("findings", [])
        }
        for q in reg_questions
        if q.get("status") in ["unacceptable", "partially_acceptable", "unanswered"]
    ]

    coverage = (acceptable / total * 100) if total > 0 else 0

    return {
        "regulation": regulation.upper(),
        "coverage": round(coverage, 1),
        "total_questions": total,
        "acceptable": acceptable,
        "gaps_count": len(gaps),
        "gaps": gaps,
        "status": "compliant" if coverage >= 90 else "partial" if coverage >= 60 else "non_compliant"
    }
