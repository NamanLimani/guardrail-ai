import logging
import pdfplumber
import docx
import pytesseract
from pdf2image import convert_from_path

logger = logging.getLogger("uvicorn")

def extract_text_from_pdf(file_path: str) -> str:
    """
    Universal Parser: Handles .txt, .pdf, .docx, and Scanned Images (OCR).
    """
    print(f"--- PARSER: Starting extraction for {file_path} ---")
    
    text_content = ""
    
    try:
        # STRATEGY 1: Text Files
        if file_path.endswith(".txt"):
            print("--- PARSER: Detected Text File ---")
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()

        # STRATEGY 2: Word Documents (.docx)
        elif file_path.endswith(".docx"):
            print("--- PARSER: Detected Word Document ---")
            doc = docx.Document(file_path)
            full_text = []
            for para in doc.paragraphs:
                full_text.append(para.text)
            return "\n".join(full_text)

        # STRATEGY 3: PDFs (Digital & Scanned)
        else:
            print("--- PARSER: Detected PDF ---")
            with pdfplumber.open(file_path) as pdf:
                print(f"--- PARSER: Found {len(pdf.pages)} pages ---")
                
                for i, page in enumerate(pdf.pages):
                    # 3a. Try Digital Extraction first
                    extracted = page.extract_text()
                    
                    if extracted and len(extracted.strip()) > 10:
                        # If we found meaningful text, use it
                        print(f"--- PARSER: Page {i+1} is Digital Text ---")
                        text_content += extracted + "\n"
                    else:
                        # 3b. Fallback to OCR (Scanned Image)
                        print(f"--- PARSER: Page {i+1} has NO text. Switching to OCR... ---")
                        try:
                            # Convert this specific page to an image
                            # Note: We convert the PDF file, grabbing just page i+1
                            images = convert_from_path(file_path, first_page=i+1, last_page=i+1)
                            for img in images:
                                ocr_text = pytesseract.image_to_string(img)
                                text_content += ocr_text + "\n"
                            print(f"--- PARSER: OCR Successful for Page {i+1} ---")
                        except Exception as e:
                            print(f"--- PARSER OCR ERROR: {e} ---")

            return text_content

    except Exception as e:
        print(f"--- PARSER ERROR: {e} ---")
        return ""