import re

def redact_text(text: str) -> str:
    """
    Scrub PII from text using Regex.
    Target: Email, Phone, SSN, Credit Card.
    """
    # 1. Email Pattern
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    text = re.sub(email_pattern, "<EMAIL>", text)
    
    # 2. Phone Pattern (US Style: 123-456-7890 or (123) 456-7890)
    phone_pattern = r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
    text = re.sub(phone_pattern, "<PHONE>", text)

    # 3. SSN Pattern (XXX-XX-XXXX) <-- NEW!
    ssn_pattern = r'\b\d{3}-\d{2}-\d{4}\b'
    text = re.sub(ssn_pattern, "<SSN>", text)

    # 4. Credit Card Pattern (XXXX-XXXX-XXXX-XXXX) <-- NEW!
    # (Simplified: Matches 13-19 digits with optional separators)
    cc_pattern = r'\b(?:\d[ -]*?){13,16}\b'
    text = re.sub(cc_pattern, "<CREDIT_CARD>", text)

    return text