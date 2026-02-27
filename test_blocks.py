import fitz
import sys
import pprint

def extract_blocks(pdf_path, page_num):
    doc = fitz.open(pdf_path)
    page = doc[page_num - 1]
    blocks = page.get_text("blocks")
    for b in blocks:
        # Each block is (x0, y0, x1, y1, "text", block_no, block_type)
        print(f"B: {b[4][:100].replace('\n', ' ')}")

if __name__ == '__main__':
    extract_blocks(sys.argv[1], int(sys.argv[2]))
