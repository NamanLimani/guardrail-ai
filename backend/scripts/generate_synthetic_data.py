import os
import random
import json
from faker import Faker
from datetime import datetime

# Initialize the Faker generator
# We use 'en_US' to ensure we get US-style SSNs and Phones for consistency
fake = Faker('en_US')

# CONFIGURATION
OUTPUT_DIR = "synthetic_docs"
NUM_DOCS = 50  # Let's start with 50 to test. We will ramp to 1000 later.

def ensure_output_dir():
    """Creates the directory if it doesn't exist."""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

# --- TEMPLATES ---
# We use templates because LLMs rely on "Context". 
# A random list of words {"John", "Apple", "555-0199"} has no semantic meaning.
# A sentence "Patient John ate an Apple. Call 555-0199" has embeddings.

def generate_resume():
    """
    Generates a fake Resume text.
    Target PII: Name, Email, Phone, Address.
    """
    profile = fake.profile()
    return f"""
    RESUME
    --------------------------------
    Name: {fake.name()}
    Email: {fake.email()}
    Phone: {fake.phone_number()}
    Address: {fake.address().replace('\n', ', ')}
    
    EXPERIENCE
    --------------------------------
    {fake.job()} at {fake.company()}
    Dates: {fake.date_between(start_date='-5y', end_date='today')} - Present
    
    EDUCATION
    --------------------------------
    University: {fake.company()} University
    Degree: BS in Computer Science
    GPA: {random.uniform(2.5, 4.0):.2f}
    """

def generate_invoice():
    """
    Generates a fake Financial Invoice.
    Target PII: Credit Card, IBAN, SSN (sometimes used for tax).
    """
    return f"""
    INVOICE #{fake.random_number(digits=6)}
    Date: {fake.date_this_year()}
    
    BILL TO:
    {fake.name()}
    {fake.address()}
    SSN (Tax ID): {fake.ssn()}
    
    PAYMENT DETAILS:
    Credit Card: {fake.credit_card_number()}
    Expires: {fake.credit_card_expire()}
    IBAN: {fake.iban()}
    
    Total Amount: ${random.uniform(100.00, 5000.00):.2f}
    """

def generate_medical_record():
    """
    Generates a fake Medical Record.
    Target PII: SSN, Date of Birth, Name.
    """
    return f"""
    CONFIDENTIAL MEDICAL RECORD
    --------------------------------
    Patient Name: {fake.name()}
    Date of Birth: {fake.date_of_birth()}
    Social Security Number: {fake.ssn()}
    
    Diagnosis:
    Patient complains of {fake.word()} pain. 
    Doctor recommends {fake.sentence()}.
    
    Insurance Provider: {fake.company()}
    Policy Number: {fake.uuid4()}
    """

# --- MAIN EXECUTION ---
def main():
    ensure_output_dir()
    
    print(f"--- GENERATING {NUM_DOCS} SYNTHETIC DOCUMENTS ---")
    
    data_registry = []

    for i in range(NUM_DOCS):
        # Randomly choose a document type
        doc_type = random.choice(['resume', 'invoice', 'medical'])
        
        if doc_type == 'resume':
            content = generate_resume()
        elif doc_type == 'invoice':
            content = generate_invoice()
        else:
            content = generate_medical_record()
            
        filename = f"{doc_type}_{i}_{fake.uuid4()[:8]}.txt"
        filepath = os.path.join(OUTPUT_DIR, filename)
        
        # Write the file to disk
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
            
        # Store metadata (we can use this later to verify if PII was caught)
        data_registry.append({
            "filename": filename,
            "type": doc_type,
            "filepath": filepath
        })

    # Save the registry
    with open("synthetic_manifest.json", "w") as f:
        json.dump(data_registry, f, indent=2)

    print(f"--- SUCCESS: Generated {NUM_DOCS} docs in '{OUTPUT_DIR}' ---")

if __name__ == "__main__":
    main()