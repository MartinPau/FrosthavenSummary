import fitz
import sys
import re

def parse_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    page = doc[18]
    blocks = page.get_text("blocks")
    
    sections = []
    
    for b in blocks:
        text = b[4].strip()
        match = re.search(r'^\s*(\d+\.\d+)\s*[\u2022\ufffd\-\.]?', text)
        if match:
            sec_id = match.group(1)
            sections.append({
                "id": sec_id,
                "x": b[0],
                "y": b[1],
                "blocks": []
            })
            
    # Group headers into rows
    rows = []
    for s in sorted(sections, key=lambda x: x["y"]):
        placed = False
        for r in rows:
            if abs(r["y"] - s["y"]) < 30:
                r["headers"].append(s)
                placed = True
                break
        if not placed:
            rows.append({"y": s["y"], "headers": [s]})
            
    # Sort rows by Y
    rows.sort(key=lambda r: r["y"], reverse=True) # Highest Y (bottom of page) first, wait no, visually Y=0 is top.
    # So we want highest Y value (further down the page).
    # If we iterate rows sorted by Y descending:
    # row[0] is y=460
    # row[1] is y=28
            
    for b in blocks:
        text = b[4].strip()
        if len(text.split()) < 4 and not re.search(r'(?:read|Read)\s+\d+(?:\.\d+)?', text):
            continue
            
        bx_mid = (b[0] + b[2]) / 2
        by = b[1]
        
        assigned = False
        for r in rows:
            if r["y"] <= by + 10:
                # This row is immediately above the block!
                # Find the closest header in this row by left X coordinate
                closest = min(r["headers"], key=lambda h: abs(h["x"] - b[0]))
                closest["blocks"].append(text.replace('\n', ' '))
                assigned = True
                break
                
        if not assigned and rows:
            # If above all rows, assign to the first row (y=28)
            closest = min(rows[-1]["headers"], key=lambda h: abs(h["x"] - b[0]))
            closest["blocks"].append(text.replace('\n', ' '))
            
    for s in sections:
        print(f"=== {s['id']} ===")
        print(" ".join([b[:60] + "..." for b in s["blocks"]]))

if __name__ == '__main__':
    parse_pdf(sys.argv[1])
