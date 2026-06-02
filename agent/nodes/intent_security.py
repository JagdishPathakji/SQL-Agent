import re
from typing import Optional
from .intent_models import IntentClassification

def detect_security_violations(user_query: str) -> Optional[IntentClassification]:
    """Scans the user query for dangerous patterns before sending it to the LLM.
    
    Detects Prompt Injection, SQL write abuse, and Schema Exfiltration.
    """
    
    # 1. Prompt Injection Scanning
    injection_patterns = [
        r"ignore\s+(?:all\s+)?(?:previous\s+)?instructions",
        r"override\s+security",
        r"act\s+as\s+a\s+(?:system|admin|bot|database)",
        r"reveal\s+system\s+prompt",
        r"system\s+prompt",
        r"reveal\s+instruction",
        r"ignore\s+safety\s+guidelines"
    ]
    
    for pat in injection_patterns:
        if re.search(pat, user_query, re.IGNORECASE):
            return IntentClassification(
                intent="unsafe_request",
                confidence=1.0,
                requires_clarification=False,
                conversational_response="Security Violation: Prompt Injection attempt detected. Action blocked."
            )
            
    # 2. SQL Write Abuse Scanning
    abuse_patterns = [
        r"\bdrop\s+table\b",
        r"\balter\s+table\b",
        r"\bdelete\s+from\b",
        r"\btruncate\s+table\b",
        r"\bcreate\s+user\b",
        r"\bgrant\s+",
        r"\brevoke\s+",
        r"\binsert\s+into\b",
        r"\bupdate\s+\w+\s+set\b"
    ]
    
    for pat in abuse_patterns:
        if re.search(pat, user_query, re.IGNORECASE):
            return IntentClassification(
                intent="unsafe_request",
                confidence=1.0,
                requires_clarification=False,
                conversational_response="Security Violation: Forbidden SQL statement pattern (non-SELECT) detected."
            )
            
    # 3. Data Exfiltration Scanning
    exfiltration_patterns = [
        r"export\s+(?:entire\s+)?database\b",
        r"show\s+all\s+schema\b",
        r"dump\s+database\b",
        r"dump\s+schema\b",
        r"reveal\s+all\s+columns\b",
        r"sqlite_master",
        r"information_schema"
    ]
    
    for pat in exfiltration_patterns:
        if re.search(pat, user_query, re.IGNORECASE):
            return IntentClassification(
                intent="unsafe_request",
                confidence=1.0,
                requires_clarification=False,
                conversational_response="Security Violation: Database inventory/schema harvesting attempt detected."
            )
            
    return None
