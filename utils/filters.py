import csv
import os
import re

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SENSITIVE_TERMS_PATH = os.path.join(PROJECT_ROOT, "data", "sensitive_terms.csv")

def load_sensitive_terms():
    keywords = []
    patterns = []

    try:
        with open(SENSITIVE_TERMS_PATH, newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                term_type = row["type"].strip().lower()
                term = row["term"].strip()
                if term_type == "keyword":
                    keywords.append(term)
                elif term_type == "pattern":
                    patterns.append(term)
    except FileNotFoundError:
        print(f"[WARN] Sensitive terms file not found: {SENSITIVE_TERMS_PATH}")

    return keywords, patterns

# Load terms once
SENSITIVE_KEYWORDS, SENSITIVE_PATTERNS = load_sensitive_terms()

def is_sensitive(message: str) -> bool:
    """
    Returns True if the message is considered sensitive based on keywords or patterns.
    """
    lowered = message.lower()

    for keyword in SENSITIVE_KEYWORDS:
        if keyword in lowered:
            return True

    for pattern in SENSITIVE_PATTERNS:
        if re.search(pattern, lowered):
            return True

    return False
