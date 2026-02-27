import fitz
import sys

def analyze_140(pdf_path):
    doc = fitz.open(pdf_path)
    page = doc[18]
    blocks = page.get_text("blocks")
    
    # We want to find the section headers on the page.
    # usually they are in a block that starts with the decimal number.
    sections = []
    
    for b in blocks:
        text = b[4].strip()
        # They sometimes look like "140.1 • Lustrous Pit"
        import re
        match = re.search(r'^(\d+\.\d+)\s*\u2022', text)
        if match:
            # Found a section start!
            sec_id = match.group(1)
            x0, y0, x1, y1 = b[0], b[1], b[2], b[3]
            sections.append({
                "id": sec_id,
                "x_mid": (x0 + x1) / 2,
                "y": y0,
                "blocks": []
            })
            
    print("Found sections:", [s["id"] for s in sections])
    
    # Now assign blocks to sections based on x-coordinate proximity
    # Often, pages are organized in columns.
    # We will compute the center X of each block.
    for b in blocks:
        text = b[4].strip()
        if len(text.split()) < 4 and not re.search(r'(?:read|Read)\s+\d+(?:\.\d+)?', text):
            continue
            
        bx_mid = (b[0] + b[2]) / 2
        
        # Find closest section by x-coordinate.
        closest = None
        min_dist = 9999
        for s in sections:
            dist = abs(s["x_mid"] - bx_mid)
            if dist < min_dist:
                min_dist = dist
                closest = s
                
        if closest and min_dist < 200: # Threshold so we don't grab text from the opposite side if it's unrelated
             closest["blocks"].append(text.replace('\n', ' '))
             
    for s in sections:
        print(f"=== {s['id']} ===")
        print(" ".join([b[:50] + "..." for b in s["blocks"]]))

if __name__ == '__main__':
    analyze_140(sys.argv[1])
