import re

# List of keywords/phrases that flag a message as sensitive
SENSITIVE_KEYWORDS = [
    "refund",
    "cancel",
    "emergency",
    "angry",
    "complaint",
    "legal",
    "sue",
    "police",
    "injury",
    "problem with the host",
    "broken",
    "unsafe",
    "danger",
    "bedbugs",
    "disgusting",
    "fire",
    "flood",
    "theft"
]

# Optional: Regex patterns for more complex detection
SENSITIVE_PATTERNS = [
    r"\b(compensat(e|ion))\b",
    r"\b(reimburse)\b",
    r"\b(not acceptable)\b",
    r"\b(this is unacceptable)\b",
    r"\b(file(d)? a complaint)\b"
]

def is_sensitive(message: str) -> bool:
    """
    Returns True if the message is considered sensitive.
    """
    lowered = message.lower()

    # Check for keyword matches
    for keyword in SENSITIVE_KEYWORDS:
        if keyword in lowered:
            return True

    # Check for regex pattern matches
    for pattern in SENSITIVE_PATTERNS:
        if re.search(pattern, lowered):
            return True

    return False
