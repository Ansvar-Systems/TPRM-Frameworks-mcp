#!/usr/bin/env python3
"""
Rubric Enhancement Script for CAIQ v4.1

This script enhances evaluation rubrics for critical CAIQ questions based on:
1. Domain-specific patterns (Crypto, Access Control, Audit, Data Security)
2. Question weight and risk level
3. Best practices for acceptable/unacceptable patterns
4. Required keywords for technical controls

Usage:
    python scripts/enhance_caiq_rubrics.py --preview  # Preview changes
    python scripts/enhance_caiq_rubrics.py --apply    # Apply enhancements
    python scripts/enhance_caiq_rubrics.py --domain crypto --apply  # Enhance specific domain
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any


# Domain-specific rubric templates
DOMAIN_RUBRICS = {
    "audit": {
        "required_keywords": ["audit", "assessment", "independent", "compliance"],
        "acceptable_patterns": [
            r"(?:yes|conducted).*(?:annual|regularly).*(?:audit|assessment)",
            r"(?:independent|third-?party).*(?:auditor|assessment)",
            r"soc\s*2.*type\s*(?:ii|2)",
            r"iso\s*27001.*(?:certified|certification)",
            r"(?:compliance|regulatory).*(?:audit|review).*(?:annual|regular)"
        ],
        "partially_acceptable_patterns": [
            r"(?:audit|assessment).*(?:planned|scheduled)",
            r"self-?assessment.*(?:conducted|performed)",
            r"internal.*audit"
        ],
        "unacceptable_patterns": [
            r"^no\b",
            r"no.*(?:audit|assessment)",
            r"not.*(?:conducted|performed)",
            r"planned.*(?:not yet|future)"
        ],
        "weight_boost": 2,  # Increase weight by this amount for audit questions
    },
    "cryptography": {
        "required_keywords": ["encryption", "key management", "TLS", "AES"],
        "acceptable_patterns": [
            r"(?:yes|use).*aes[-\s]*(?:256|128)",
            r"tls\s*(?:1\.[23]|v1\.[23])",
            r"(?:formal|documented).*key\s*management",
            r"(?:key|cryptographic).*rotation",
            r"(?:encrypt(?:ed|ion)).*(?:rest|transit)",
            r"hsm|hardware\s*security\s*module",
            r"kms|key\s*management\s*(?:system|service)"
        ],
        "partially_acceptable_patterns": [
            r"(?:encryption|tls).*(?:partial|some)",
            r"key\s*management.*(?:informal|manual)",
            r"aes[-\s]*128",
            r"tls\s*1\.1"
        ],
        "unacceptable_patterns": [
            r"^no\b",
            r"no.*encryption",
            r"plaintext|unencrypted",
            r"md5|sha-?1\b",
            r"ssl\s*(?:v[23]|2|3)",
            r"des\b|3des\b"
        ],
        "weight_boost": 3,  # Crypto is critical
    },
    "access_control": {
        "required_keywords": ["MFA", "least privilege", "authentication", "authorization"],
        "acceptable_patterns": [
            r"(?:yes|implement).*(?:mfa|multi-?factor|2fa)",
            r"(?:rbac|role-?based).*(?:access|control)",
            r"least\s*privilege",
            r"(?:strong|secure).*(?:authentication|password)",
            r"(?:sso|single\s*sign-?on)",
            r"(?:privileged|admin).*(?:access|account).*(?:management|monitoring)"
        ],
        "partially_acceptable_patterns": [
            r"(?:mfa|multi-?factor).*(?:partial|some|admin)",
            r"access.*control.*(?:informal|basic)",
            r"password.*(?:policy|complexity)"
        ],
        "unacceptable_patterns": [
            r"^no\b",
            r"no.*(?:mfa|multi-?factor|authentication)",
            r"shared.*(?:account|credential|password)",
            r"no.*(?:access|control|restriction)"
        ],
        "weight_boost": 3,  # Access control is critical
    },
    "data_security": {
        "required_keywords": ["classification", "retention", "disposal", "protection"],
        "acceptable_patterns": [
            r"(?:yes|have|implement).*(?:data\s*)?classification",
            r"(?:classified|categorized).*(?:sensitivity|confidentiality)",
            r"(?:documented|formal).*(?:retention|disposal).*(?:policy|procedure)",
            r"(?:encrypt(?:ed|ion)).*(?:rest|storage|transit)",
            r"(?:data\s*)?protection.*(?:controls|measures)",
            r"(?:dlp|data\s*loss\s*prevention)"
        ],
        "partially_acceptable_patterns": [
            r"(?:partial|some).*classification",
            r"classification.*(?:informal|basic)",
            r"retention.*(?:policy|procedure).*(?:not\s*)?(?:documented)?"
        ],
        "unacceptable_patterns": [
            r"^no\b",
            r"no.*(?:classification|protection)",
            r"(?:not|no).*(?:classified|categorized)",
            r"(?:ad[\s-]?hoc|unstructured).*(?:retention|disposal)"
        ],
        "weight_boost": 2,
    },
    "incident_management": {
        "required_keywords": ["incident", "response", "detection", "notification"],
        "acceptable_patterns": [
            r"(?:yes|have).*incident.*(?:response|management).*(?:plan|procedure)",
            r"(?:documented|formal).*incident.*(?:response|handling)",
            r"(?:24/7|24x7|continuous).*(?:monitoring|detection)",
            r"(?:siem|security.*information.*event)",
            r"incident.*(?:notification|reporting).*(?:procedure|timeline)"
        ],
        "partially_acceptable_patterns": [
            r"incident.*response.*(?:informal|basic)",
            r"monitoring.*(?:business\s*hours|limited)",
            r"incident.*(?:planned|developing)"
        ],
        "unacceptable_patterns": [
            r"^no\b",
            r"no.*incident.*(?:response|plan|procedure)",
            r"(?:reactive|ad[\s-]?hoc).*(?:only|approach)"
        ],
        "weight_boost": 2,
    },
    "business_continuity": {
        "required_keywords": ["BCP", "disaster recovery", "backup", "testing"],
        "acceptable_patterns": [
            r"(?:yes|have).*(?:bcp|business\s*continuity).*plan",
            r"(?:documented|formal).*(?:disaster\s*recovery|dr)",
            r"(?:backup|recovery).*(?:tested|testing).*(?:regular|annual)",
            r"rto|recovery\s*time\s*objective",
            r"rpo|recovery\s*point\s*objective",
            r"(?:annual|regular).*(?:test|exercise).*(?:bcp|dr)"
        ],
        "partially_acceptable_patterns": [
            r"(?:bcp|disaster\s*recovery).*(?:exists|documented).*(?:not\s*)?tested",
            r"backup.*(?:not\s*)?(?:tested|verified)",
            r"continuity.*plan.*(?:informal|basic)"
        ],
        "unacceptable_patterns": [
            r"^no\b",
            r"no.*(?:bcp|continuity|backup|recovery)",
            r"(?:not|no).*(?:tested|documented)"
        ],
        "weight_boost": 2,
    }
}


class CAIQRubricEnhancer:
    """Enhances evaluation rubrics for CAIQ questions."""

    def __init__(self, data_path: Path, use_full: bool = True):
        self.data_path = data_path
        # Use full dataset by default
        if use_full:
            self.caiq_file = data_path / "caiq_v4_full.json"
        else:
            self.caiq_file = data_path / "caiq_v4.json"
        self.data = None
        self.load_data()

    def load_data(self):
        """Load CAIQ data file."""
        with open(self.caiq_file, 'r') as f:
            self.data = json.load(f)

    def save_data(self):
        """Save enhanced CAIQ data file."""
        with open(self.caiq_file, 'w') as f:
            json.dump(self.data, f, indent=2)

    def identify_domain(self, question: Dict[str, Any]) -> str:
        """Identify the domain of a question."""
        category = question.get("category", "").lower()
        question_text = question.get("question_text", "").lower()
        combined = category + " " + question_text

        # Check for domain keywords
        if "audit" in category or "compliance" in category or "assurance" in category:
            return "audit"
        elif "crypt" in category or "encrypt" in category or "key" in combined:
            return "cryptography"
        elif "access" in category or "identity" in category or "iam" in combined:
            return "access_control"
        elif "data" in category and ("security" in category or "privacy" in category):
            return "data_security"
        elif "incident" in category or "incident" in combined:
            return "incident_management"
        elif "continuity" in category or "resilience" in category or "bcp" in combined:
            return "business_continuity"

        return "general"

    def enhance_rubric(self, question: Dict[str, Any], domain: str) -> Dict[str, Any]:
        """Enhance or create rubric for a question."""
        if domain == "general" or domain not in DOMAIN_RUBRICS:
            return question.get("evaluation_rubric", {})

        domain_rubric = DOMAIN_RUBRICS[domain]
        current_rubric = question.get("evaluation_rubric", {})

        # Build enhanced rubric starting from current
        enhanced = {
            "acceptable": list(current_rubric.get("acceptable", [])),
            "partially_acceptable": list(current_rubric.get("partially_acceptable", [])),
            "unacceptable": list(current_rubric.get("unacceptable", [])),
            "required_keywords": list(current_rubric.get("required_keywords", []))
        }

        # Add domain-specific patterns (avoid duplicates, case-insensitive)
        current_acceptable_lower = [str(p).lower() for p in enhanced["acceptable"]]
        for pattern in domain_rubric.get("acceptable_patterns", []):
            if pattern.lower() not in current_acceptable_lower and pattern not in enhanced["acceptable"]:
                enhanced["acceptable"].append(pattern)

        current_partial_lower = [str(p).lower() for p in enhanced["partially_acceptable"]]
        for pattern in domain_rubric.get("partially_acceptable_patterns", []):
            if pattern.lower() not in current_partial_lower and pattern not in enhanced["partially_acceptable"]:
                enhanced["partially_acceptable"].append(pattern)

        current_unacceptable_lower = [str(p).lower() for p in enhanced["unacceptable"]]
        for pattern in domain_rubric.get("unacceptable_patterns", []):
            if pattern.lower() not in current_unacceptable_lower and pattern not in enhanced["unacceptable"]:
                enhanced["unacceptable"].append(pattern)

        # Add domain-specific keywords (avoid duplicates, case-insensitive)
        current_keywords_lower = [str(k).lower() for k in enhanced["required_keywords"]]
        for keyword in domain_rubric.get("required_keywords", []):
            if keyword.lower() not in current_keywords_lower and keyword not in enhanced["required_keywords"]:
                enhanced["required_keywords"].append(keyword)

        return enhanced

    def enhance_weight(self, question: Dict[str, Any], domain: str) -> int:
        """Adjust question weight based on domain."""
        current_weight = question.get("weight", 5)

        if domain in DOMAIN_RUBRICS:
            boost = DOMAIN_RUBRICS[domain].get("weight_boost", 0)
            new_weight = min(10, current_weight + boost)  # Cap at 10
            return new_weight

        return current_weight

    def enhance_risk_level(self, question: Dict[str, Any], domain: str) -> str:
        """Adjust risk level based on domain and weight."""
        current_risk = question.get("risk_if_inadequate", "medium")
        weight = question.get("weight", 5)

        # Critical domains should have higher risk
        if domain in ["cryptography", "access_control"] and weight >= 8:
            return "critical"
        elif domain in ["audit", "data_security", "incident_management"] and weight >= 8:
            return "high"
        elif weight >= 9:
            return "high"

        return current_risk

    def enhance_questions(self, domain_filter: str = None, dry_run: bool = True) -> Dict[str, int]:
        """Enhance all questions or specific domain."""
        stats = {
            "total": 0,
            "enhanced": 0,
            "weight_adjusted": 0,
            "risk_adjusted": 0,
            "by_domain": {}
        }

        questions = self.data.get("questions", [])
        stats["total"] = len(questions)

        for question in questions:
            domain = self.identify_domain(question)

            # Skip if filtering by domain
            if domain_filter and domain != domain_filter:
                continue

            # Track by domain
            stats["by_domain"][domain] = stats["by_domain"].get(domain, 0) + 1

            # Enhance rubric
            original_rubric = question.get("evaluation_rubric", {})
            enhanced_rubric = self.enhance_rubric(question, domain)

            if enhanced_rubric != original_rubric:
                if not dry_run:
                    question["evaluation_rubric"] = enhanced_rubric
                stats["enhanced"] += 1

            # Adjust weight
            original_weight = question.get("weight", 5)
            enhanced_weight = self.enhance_weight(question, domain)

            if enhanced_weight != original_weight:
                if not dry_run:
                    question["weight"] = enhanced_weight
                stats["weight_adjusted"] += 1

            # Adjust risk level
            original_risk = question.get("risk_if_inadequate", "medium")
            enhanced_risk = self.enhance_risk_level(question, domain)

            if enhanced_risk != original_risk:
                if not dry_run:
                    question["risk_if_inadequate"] = enhanced_risk
                stats["risk_adjusted"] += 1

        return stats

    def preview_enhancements(self, domain_filter: str = None, limit: int = 5):
        """Preview enhancements without applying."""
        print(f"\n{'='*60}")
        print("CAIQ Rubric Enhancement Preview")
        print(f"{'='*60}\n")

        questions = self.data.get("questions", [])
        shown = 0

        for question in questions:
            if shown >= limit:
                break

            domain = self.identify_domain(question)

            # Skip if filtering
            if domain_filter and domain != domain_filter:
                continue

            # Check if enhancement would occur
            original_rubric = question.get("evaluation_rubric", {})
            enhanced_rubric = self.enhance_rubric(question, domain)

            if enhanced_rubric != original_rubric:
                shown += 1

                print(f"Question ID: {question['id']}")
                print(f"Category: {question['category']}")
                print(f"Domain: {domain}")
                print(f"Question: {question['question_text'][:100]}...")
                print(f"\nOriginal Weight: {question.get('weight', 'N/A')}")
                print(f"Enhanced Weight: {self.enhance_weight(question, domain)}")
                print(f"\nOriginal Risk: {question.get('risk_if_inadequate', 'N/A')}")
                print(f"Enhanced Risk: {self.enhance_risk_level(question, domain)}")

                print(f"\nOriginal Rubric Patterns: {len(original_rubric.get('acceptable', []))}")
                print(f"Enhanced Rubric Patterns: {len(enhanced_rubric.get('acceptable', []))}")

                print(f"\nOriginal Keywords: {original_rubric.get('required_keywords', [])}")
                print(f"Enhanced Keywords: {enhanced_rubric.get('required_keywords', [])}")

                print(f"\n{'-'*60}\n")

        if shown == 0:
            print("No enhancements needed or found for the specified criteria.")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Enhance CAIQ v4.1 evaluation rubrics")
    parser.add_argument("--preview", action="store_true", help="Preview changes without applying")
    parser.add_argument("--apply", action="store_true", help="Apply enhancements")
    parser.add_argument("--domain", type=str, help="Filter by domain (audit, cryptography, access_control, etc.)")
    parser.add_argument("--limit", type=int, default=5, help="Limit preview results")
    parser.add_argument("--use-placeholder", action="store_true", help="Use placeholder caiq_v4.json instead of full dataset")

    args = parser.parse_args()

    # Get data path
    script_dir = Path(__file__).parent
    data_path = script_dir.parent / "src" / "tprm_frameworks_mcp" / "data"

    # Initialize enhancer
    use_full = not args.use_placeholder
    enhancer = CAIQRubricEnhancer(data_path, use_full=use_full)

    if args.preview:
        # Show preview
        enhancer.preview_enhancements(domain_filter=args.domain, limit=args.limit)

        # Show stats
        stats = enhancer.enhance_questions(domain_filter=args.domain, dry_run=True)
        print(f"\n{'='*60}")
        print("Enhancement Statistics (Preview)")
        print(f"{'='*60}")
        print(f"Total Questions: {stats['total']}")
        print(f"Questions Enhanced: {stats['enhanced']}")
        print(f"Weights Adjusted: {stats['weight_adjusted']}")
        print(f"Risk Levels Adjusted: {stats['risk_adjusted']}")
        print(f"\nBy Domain:")
        for domain, count in sorted(stats['by_domain'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {domain.capitalize()}: {count} questions")

    elif args.apply:
        # Apply enhancements
        print("Applying rubric enhancements...")
        stats = enhancer.enhance_questions(domain_filter=args.domain, dry_run=False)

        # Save changes
        enhancer.save_data()

        print(f"\n{'='*60}")
        print("Enhancement Applied Successfully")
        print(f"{'='*60}")
        print(f"Total Questions: {stats['total']}")
        print(f"Questions Enhanced: {stats['enhanced']}")
        print(f"Weights Adjusted: {stats['weight_adjusted']}")
        print(f"Risk Levels Adjusted: {stats['risk_adjusted']}")
        print(f"\nBy Domain:")
        for domain, count in sorted(stats['by_domain'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {domain.capitalize()}: {count} questions")
        print(f"\nChanges saved to: {enhancer.caiq_file}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
