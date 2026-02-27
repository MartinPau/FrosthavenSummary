import fitz  # PyMuPDF
import sys

def test_extract(pdf_path):
    print(f"Testing {pdf_path}")
    try:
        doc = fitz.open(pdf_path)
        for i in range(min(3, len(doc))):
            page = doc[i]
            text = page.get_text()
            print(f"--- Page {i+1} ---")
            print(text[:500])  # Print first 500 chars
            print("-----------------")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    test_extract(sys.argv[1])
