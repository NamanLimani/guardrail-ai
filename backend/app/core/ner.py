# from transformers import AutoTokenizer, AutoModelForTokenClassification
# from transformers import pipeline
# import re

# class NERRedactor:
#     def __init__(self):
#         # 1. Load the Pre-trained BERT Model
#         # "dslim/bert-base-NER" is a standard model for Person/Org/Location detection
#         print("--- NER: Loading BERT Model (dslim/bert-base-NER)... ---")
#         self.tokenizer = AutoTokenizer.from_pretrained("dslim/bert-base-NER")
#         self.model = AutoModelForTokenClassification.from_pretrained("dslim/bert-base-NER")
        
#         # 2. Create the Pipeline
#         # 'aggregation_strategy="simple"' merges sub-tokens (e.g., "Amy" + "Mitchell" -> "Amy Mitchell")
#         self.nlp = pipeline("ner", model=self.model, tokenizer=self.tokenizer, aggregation_strategy="simple")
#         print("--- NER: Model Loaded Successfully ---")

#     def redact(self, text: str):
#         """
#         Returns: (redacted_text, pii_stats)
#         pii_stats example: {"PER": 2, "SSN": 1, "ORG": 1}
#         """
#         stats = {"PER": 0, "ORG": 0, "LOC": 0, "SSN": 0, "CREDIT_CARD": 0, "EMAIL": 0}

#         # A. DEEP LEARNING PASS
#         ner_results = self.nlp(text)
#         spans_to_redact = []
#         for entity in ner_results:
#             if entity['entity_group'] in ['PER', 'ORG', 'LOC']:
#                 spans_to_redact.append((entity['start'], entity['end'], entity['entity_group']))
#                 stats[entity['entity_group']] += 1 # Count it
        
#         # Sort and Redact
#         spans_to_redact.sort(key=lambda x: x[0], reverse=True)
#         redacted_text = list(text)
#         for start, end, label in spans_to_redact:
#             redacted_text[start:end] = f"<{label}>"
#         text = "".join(redacted_text)

#         # B. REGEX PASS (Count matches using len(re.findall))
        
#         # Email
#         email_matches = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
#         stats["EMAIL"] += len(email_matches)
#         text = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', "<EMAIL>", text)
        
#         # SSN
#         ssn_matches = re.findall(r'\b\d{3}-\d{2}-\d{4}\b', text)
#         stats["SSN"] += len(ssn_matches)
#         text = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', "<SSN>", text)
        
#         # Credit Card
#         cc_matches = re.findall(r'\b(?:\d[ -]*?){13,16}\b', text)
#         stats["CREDIT_CARD"] += len(cc_matches)
#         text = re.sub(r'\b(?:\d[ -]*?){13,16}\b', "<CREDIT_CARD>", text)
        
#         return text, stats  # <--- RETURN BOTH

# # Create a singleton instance
# ner_redactor = NERRedactor()


import os
import requests
import re

class NERRedactor:
    def __init__(self):
        self.hf_token = os.getenv("HF_TOKEN")
        # The specific Hugging Face URL for our chosen NER model
        self.api_url = "https://api-inference.huggingface.co/models/dslim/bert-base-NER"
        self.headers = {"Authorization": f"Bearer {self.hf_token}"}
        print("--- NER: Configured for Hugging Face Cloud Inference ---")

    def redact(self, text: str):
        stats = {"PER": 0, "ORG": 0, "LOC": 0, "SSN": 0, "CREDIT_CARD": 0, "EMAIL": 0}
        
        # We need to cap text length because the API has limits per request (~512 words)
        # For a production app we would split it into chunks, but this works for our portfolio.
        safe_text = text[:2000] 

        # A. DEEP LEARNING PASS (Via Cloud API)
        spans_to_redact = []
        if self.hf_token:
            try:
                # We ask the API to "aggregate" sub-words automatically
                payload = {"inputs": safe_text, "parameters": {"aggregation_strategy": "simple"}}
                response = requests.post(self.api_url, headers=self.headers, json=payload, timeout=15)
                
                if response.status_code == 200:
                    ner_results = response.json()
                    for entity in ner_results:
                        # API returns 'entity_group' (e.g., 'PER', 'ORG')
                        ent_label = entity.get('entity_group', entity.get('entity', '')).replace('B-', '').replace('I-', '')
                        
                        if ent_label in ['PER', 'ORG', 'LOC']:
                            spans_to_redact.append((entity['start'], entity['end'], ent_label))
                            stats[ent_label] += 1
                else:
                    print(f"NER API Error: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"NER Request Failed: {e}")

        # Sort spans backwards so replacing text doesn't mess up the index positions!
        spans_to_redact.sort(key=lambda x: x[0], reverse=True)
        
        redacted_text = list(safe_text)
        for start, end, label in spans_to_redact:
            redacted_text[start:end] = f"<{label}>"
        
        final_text = "".join(redacted_text)

        # B. REGEX PASS (Local)
        # Email
        email_matches = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', final_text)
        stats["EMAIL"] += len(email_matches)
        final_text = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', "<EMAIL>", final_text)
        
        # SSN
        ssn_matches = re.findall(r'\b\d{3}-\d{2}-\d{4}\b', final_text)
        stats["SSN"] += len(ssn_matches)
        final_text = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', "<SSN>", final_text)
        
        # Credit Card
        cc_matches = re.findall(r'\b(?:\d[ -]*?){13,16}\b', final_text)
        stats["CREDIT_CARD"] += len(cc_matches)
        final_text = re.sub(r'\b(?:\d[ -]*?){13,16}\b', "<CREDIT_CARD>", final_text)
        
        return final_text, stats

# Create a singleton instance
ner_redactor = NERRedactor()