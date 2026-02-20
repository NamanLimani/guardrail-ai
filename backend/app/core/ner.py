import os
import requests
import re
import time

class NERRedactor:
    def __init__(self):
        self.hf_token = os.getenv("HF_TOKEN")
        self.api_url = "https://router.huggingface.co/hf-inference/models/dslim/bert-base-NER"
        self.headers = {"Authorization": f"Bearer {self.hf_token}"}
        print("--- NER: Configured for Hugging Face Cloud Inference ---")

    def redact(self, text: str):
        # Added URL to the stats tracker
        stats = {"PER": 0, "ORG": 0, "LOC": 0, "SSN": 0, "CREDIT_CARD": 0, "EMAIL": 0, "URL": 0}
        
        # We process the first 2500 characters to capture more of the resume
        safe_text = text[:2500] 

        spans_to_redact = []
        if self.hf_token:
            try:
                payload = {
                    "inputs": safe_text, 
                    "parameters": {"aggregation_strategy": "simple"}
                }
                response = requests.post(self.api_url, headers=self.headers, json=payload, timeout=20)
                
                if response.status_code == 503:
                    print("NER: Model loading, waiting 5s...")
                    time.sleep(5)
                    return self.redact(text)

                if response.status_code == 200:
                    ner_results = response.json()
                    for entity in ner_results:
                        label = entity.get('entity_group', entity.get('entity', ''))
                        label = label.replace('B-', '').replace('I-', '')
                        
                        if label in ['PER', 'ORG', 'LOC']:
                            spans_to_redact.append((entity['start'], entity['end'], label))
                            stats[label] += 1
                else:
                    print(f"NER API Error: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"NER Request Failed: {e}")

        spans_to_redact.sort(key=lambda x: x[0], reverse=True)
        
        redacted_text = list(safe_text)
        for start, end, label in spans_to_redact:
            redacted_text[start:end] = f"<{label}>"
        
        final_text = "".join(redacted_text)

        # 1. OCR-Proof Email Fallback (Catches spaces before/after @)
        email_pattern = r'[a-zA-Z0-9._%+-]+\s*@\s*[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        stats["EMAIL"] += len(re.findall(email_pattern, final_text))
        final_text = re.sub(email_pattern, "<EMAIL>", final_text)
        
        # 2. URL Fallback (Catches GitHub, LinkedIn, etc.)
        url_pattern = r'(?:https?://)?(?:www\.)?(?:linkedin\.com|github\.com)\S+|[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/\S+'
        stats["URL"] += len(re.findall(url_pattern, final_text))
        final_text = re.sub(url_pattern, "<URL>", final_text)

        # 3. Standard SSN / Credit Card Fallbacks
        ssn_pattern = r'\b\d{3}-\d{2}-\d{4}\b'
        cc_pattern = r'\b(?:\d[ -]*?){13,16}\b'

        stats["SSN"] += len(re.findall(ssn_pattern, final_text))
        final_text = re.sub(ssn_pattern, "<SSN>", final_text)
        
        stats["CREDIT_CARD"] += len(re.findall(cc_pattern, final_text))
        final_text = re.sub(cc_pattern, "<CREDIT_CARD>", final_text)
        
        return final_text, stats

ner_redactor = NERRedactor()