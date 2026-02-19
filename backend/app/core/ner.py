from transformers import AutoTokenizer, AutoModelForTokenClassification
from transformers import pipeline
import re

class NERRedactor:
    def __init__(self):
        # 1. Load the Pre-trained BERT Model
        # "dslim/bert-base-NER" is a standard model for Person/Org/Location detection
        print("--- NER: Loading BERT Model (dslim/bert-base-NER)... ---")
        self.tokenizer = AutoTokenizer.from_pretrained("dslim/bert-base-NER")
        self.model = AutoModelForTokenClassification.from_pretrained("dslim/bert-base-NER")
        
        # 2. Create the Pipeline
        # 'aggregation_strategy="simple"' merges sub-tokens (e.g., "Amy" + "Mitchell" -> "Amy Mitchell")
        self.nlp = pipeline("ner", model=self.model, tokenizer=self.tokenizer, aggregation_strategy="simple")
        print("--- NER: Model Loaded Successfully ---")

    def redact(self, text: str):
        """
        Returns: (redacted_text, pii_stats)
        pii_stats example: {"PER": 2, "SSN": 1, "ORG": 1}
        """
        stats = {"PER": 0, "ORG": 0, "LOC": 0, "SSN": 0, "CREDIT_CARD": 0, "EMAIL": 0}

        # A. DEEP LEARNING PASS
        ner_results = self.nlp(text)
        spans_to_redact = []
        for entity in ner_results:
            if entity['entity_group'] in ['PER', 'ORG', 'LOC']:
                spans_to_redact.append((entity['start'], entity['end'], entity['entity_group']))
                stats[entity['entity_group']] += 1 # Count it
        
        # Sort and Redact
        spans_to_redact.sort(key=lambda x: x[0], reverse=True)
        redacted_text = list(text)
        for start, end, label in spans_to_redact:
            redacted_text[start:end] = f"<{label}>"
        text = "".join(redacted_text)

        # B. REGEX PASS (Count matches using len(re.findall))
        
        # Email
        email_matches = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
        stats["EMAIL"] += len(email_matches)
        text = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', "<EMAIL>", text)
        
        # SSN
        ssn_matches = re.findall(r'\b\d{3}-\d{2}-\d{4}\b', text)
        stats["SSN"] += len(ssn_matches)
        text = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', "<SSN>", text)
        
        # Credit Card
        cc_matches = re.findall(r'\b(?:\d[ -]*?){13,16}\b', text)
        stats["CREDIT_CARD"] += len(cc_matches)
        text = re.sub(r'\b(?:\d[ -]*?){13,16}\b', "<CREDIT_CARD>", text)
        
        return text, stats  # <--- RETURN BOTH

# Create a singleton instance
ner_redactor = NERRedactor()