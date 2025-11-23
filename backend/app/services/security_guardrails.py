"""
Security Guardrails Service

Implements security filters to protect against:
- Prompt injection attacks
- Jailbreak attempts
- SQL injection patterns in queries
- Malicious instructions
- Command injection attempts
"""

from typing import Dict, List, Optional, Tuple
import logging
import re
from enum import Enum

logger = logging.getLogger(__name__)


class ThreatLevel(str, Enum):
    """Threat severity levels"""
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SecurityGuardrails:
    """Security filters for user queries"""

    # Prompt injection patterns
    PROMPT_INJECTION_PATTERNS = [
        # Direct instruction overrides
        r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
        r"disregard\s+(all\s+)?(previous|prior|above)\s+instructions",
        r"forget\s+(all\s+)?(previous|prior|above)\s+instructions",
        r"override\s+(system|previous)\s+",

        # Role manipulation
        r"you\s+are\s+now\s+(a|an)\s+",
        r"act\s+as\s+(a|an)\s+(DAN|unrestricted|unfiltered)",
        r"pretend\s+to\s+be\s+",
        r"simulate\s+being\s+",

        # System prompt extraction attempts
        r"(show|display|print|reveal)\s+(your\s+)?(system|hidden|secret)\s+(prompt|instructions)",
        r"what\s+(are|were)\s+your\s+(original|initial)\s+instructions",
        r"repeat\s+(your\s+)?(system|initial)\s+(prompt|instructions)",

        # Delimiter/escape attempts
        r"```\s*system",
        r"<\|endoftext\|>",
        r"<\|im_end\|>",
        r"</s>",

        # Jailbreak patterns
        r"DAN\s+mode",
        r"developer\s+mode",
        r"god\s+mode",
        r"sudo\s+mode",
    ]

    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r"'\s*OR\s+'1'\s*=\s*'1",
        r";\s*DROP\s+TABLE",
        r";\s*DELETE\s+FROM",
        r"UNION\s+SELECT",
        r"--\s*$",  # SQL comment at end
    ]

    # Command injection patterns
    COMMAND_INJECTION_PATTERNS = [
        r";\s*(rm|del|format)\s+",
        r"\|\s*bash",
        r"\|\s*sh",
        r"`.*`",  # Backtick command execution
        r"\$\(.*\)",  # Command substitution
    ]

    # Suspicious instruction keywords (weight-based scoring)
    SUSPICIOUS_KEYWORDS = {
        "ignore": 2,
        "disregard": 2,
        "forget": 2,
        "override": 3,
        "jailbreak": 5,
        "unrestricted": 3,
        "unfiltered": 3,
        "bypass": 3,
        "hack": 4,
        "exploit": 4,
        "vulnerability": 2,
        "injection": 4,
    }

    def __init__(self, strict_mode: bool = False):
        """
        Initialize security guardrails.

        Args:
            strict_mode: If True, applies stricter filtering (may have false positives)
        """
        self.strict_mode = strict_mode
        self.compiled_prompt_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.PROMPT_INJECTION_PATTERNS
        ]
        self.compiled_sql_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.SQL_INJECTION_PATTERNS
        ]
        self.compiled_command_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.COMMAND_INJECTION_PATTERNS
        ]

    def check_query_safety(self, query: str) -> Dict:
        """
        Comprehensive safety check for user query.

        Args:
            query: User's input query

        Returns:
            Dict with:
                - is_safe: bool
                - threat_level: ThreatLevel
                - threats_detected: List[str]
                - risk_score: int (0-100)
                - recommendation: str
        """
        threats = []
        risk_score = 0

        # 1. Check for prompt injection
        prompt_threats = self._detect_prompt_injection(query)
        if prompt_threats:
            threats.extend([f"Prompt injection: {t}" for t in prompt_threats])
            risk_score += 30

        # 2. Check for SQL injection
        sql_threats = self._detect_sql_injection(query)
        if sql_threats:
            threats.extend([f"SQL injection: {t}" for t in sql_threats])
            risk_score += 40

        # 3. Check for command injection
        cmd_threats = self._detect_command_injection(query)
        if cmd_threats:
            threats.extend([f"Command injection: {t}" for t in cmd_threats])
            risk_score += 40

        # 4. Check suspicious keywords (weight-based)
        keyword_score = self._check_suspicious_keywords(query)
        risk_score += keyword_score

        # 5. Check for excessive length (potential DoS)
        if len(query) > 5000:
            threats.append("Excessive query length")
            risk_score += 10

        # 6. Check for unusual character patterns
        if self._has_unusual_patterns(query):
            threats.append("Unusual character patterns")
            risk_score += 5

        # Determine threat level
        if risk_score >= 70:
            threat_level = ThreatLevel.CRITICAL
        elif risk_score >= 50:
            threat_level = ThreatLevel.HIGH
        elif risk_score >= 30:
            threat_level = ThreatLevel.MEDIUM
        elif risk_score > 0:
            threat_level = ThreatLevel.LOW
        else:
            threat_level = ThreatLevel.SAFE

        # Determine if query should be blocked
        is_safe = risk_score < (40 if self.strict_mode else 70)

        # Generate recommendation
        if threat_level == ThreatLevel.CRITICAL:
            recommendation = "Block query immediately - critical security threat"
        elif threat_level == ThreatLevel.HIGH:
            recommendation = "Block query - high risk detected"
        elif threat_level == ThreatLevel.MEDIUM:
            recommendation = "Warn user - proceed with caution"
        elif threat_level == ThreatLevel.LOW:
            recommendation = "Log for monitoring - low risk"
        else:
            recommendation = "Allow query"

        logger.info(
            f"Security check: threat_level={threat_level}, "
            f"risk_score={risk_score}, is_safe={is_safe}, "
            f"threats={len(threats)}"
        )

        return {
            "is_safe": is_safe,
            "threat_level": threat_level.value,
            "threats_detected": threats,
            "risk_score": risk_score,
            "recommendation": recommendation,
            "sanitized_query": self._sanitize_query(query) if not is_safe else query
        }

    def _detect_prompt_injection(self, query: str) -> List[str]:
        """Detect prompt injection attempts"""
        detected = []
        for pattern in self.compiled_prompt_patterns:
            if pattern.search(query):
                detected.append(f"Pattern: {pattern.pattern}")
        return detected

    def _detect_sql_injection(self, query: str) -> List[str]:
        """Detect SQL injection attempts"""
        detected = []
        for pattern in self.compiled_sql_patterns:
            if pattern.search(query):
                detected.append(f"Pattern: {pattern.pattern}")
        return detected

    def _detect_command_injection(self, query: str) -> List[str]:
        """Detect command injection attempts"""
        detected = []
        for pattern in self.compiled_command_patterns:
            if pattern.search(query):
                detected.append(f"Pattern: {pattern.pattern}")
        return detected

    def _check_suspicious_keywords(self, query: str) -> int:
        """
        Check for suspicious keywords and return weighted score.

        Returns:
            Score from 0-25 based on keyword matches
        """
        query_lower = query.lower()
        score = 0

        for keyword, weight in self.SUSPICIOUS_KEYWORDS.items():
            if keyword in query_lower:
                score += weight
                logger.debug(f"Suspicious keyword detected: '{keyword}' (weight={weight})")

        # Cap at 25 to avoid over-penalizing legitimate queries
        return min(score, 25)

    def _has_unusual_patterns(self, query: str) -> bool:
        """
        Detect unusual character patterns that might indicate an attack.

        Checks for:
        - Excessive special characters
        - Unusual Unicode characters
        - Repeated delimiter patterns
        """
        # Check for excessive special characters (>30% of query)
        special_chars = sum(1 for c in query if not c.isalnum() and not c.isspace())
        if special_chars / max(len(query), 1) > 0.3:
            return True

        # Check for unusual Unicode ranges (potential encoding tricks)
        unusual_unicode = sum(1 for c in query if ord(c) > 0x7F)
        if unusual_unicode / max(len(query), 1) > 0.1:
            return True

        # Check for repeated delimiters
        if re.search(r'([<>{}[\]"`]{3,})', query):
            return True

        return False

    def _sanitize_query(self, query: str) -> str:
        """
        Sanitize a potentially malicious query by removing dangerous patterns.

        Note: This is a fallback - high-risk queries should be blocked entirely.

        Args:
            query: The query to sanitize

        Returns:
            Sanitized query string
        """
        # Remove SQL comment markers
        sanitized = re.sub(r'--.*$', '', query, flags=re.MULTILINE)

        # Remove backticks and command substitution
        sanitized = re.sub(r'`[^`]*`', '', sanitized)
        sanitized = re.sub(r'\$\([^)]*\)', '', sanitized)

        # Remove delimiter/escape sequences
        sanitized = re.sub(r'<\|.*?\|>', '', sanitized)
        sanitized = re.sub(r'```.*?```', '', sanitized, flags=re.DOTALL)

        # Limit length
        if len(sanitized) > 2000:
            sanitized = sanitized[:2000] + "..."

        logger.warning(f"Query sanitized: '{query}' -> '{sanitized}'")
        return sanitized.strip()


# Singleton instance
_security_guardrails = None


def get_security_guardrails(strict_mode: bool = False) -> SecurityGuardrails:
    """Get or create global security guardrails instance"""
    global _security_guardrails
    if _security_guardrails is None:
        _security_guardrails = SecurityGuardrails(strict_mode=strict_mode)
    return _security_guardrails


def check_query_safety(query: str, strict_mode: bool = False) -> Dict:
    """
    Convenience function to check query safety.

    Args:
        query: User's input query
        strict_mode: If True, applies stricter filtering

    Returns:
        Safety check result dict
    """
    guardrails = get_security_guardrails(strict_mode=strict_mode)
    return guardrails.check_query_safety(query)
