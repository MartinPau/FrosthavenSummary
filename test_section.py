import fitz
import sys

def test_section(pdf_path, search_term="140.2"):
    doc = fitz.open(pdf_path)
    for i in range(len(doc)):
        page = doc[i]
        text = page.get_text()
        if search_term in text:
            print(f"--- Found on Page {i+1} ---")
            print(text[:500])
            print("...")

if __name__ == '__main__':
    test_section(sys.argv[1])
