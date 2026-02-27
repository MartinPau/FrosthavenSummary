import fitz
import sys

def parse_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    page = doc[18]
    blocks = page.get_text("blocks")
    
    # We want to robustly partition the page into sub-sections.
    # 1. Find all section headers: "140.2 • Title", "140.1", "Conclusion" etc.
    # For Frosthaven Section Books, the headers have distinct styling or start with the ID.
    import re
    
    sections = []
    
    for i, b in enumerate(blocks):
        text = b[4].strip()
        
        # Look for headers like " 140.1 \u2022 Lustrous Pit" or just "140.1" (sometimes the bullet is extracted weirdly)
        match = re.search(r'^\s*(\d+\.\d+)\s*[\u2022\ufffd\-\.]', text)
        if match:
            sections.append({
                "id": match.group(1),
                "y": b[1], # Top Y coordinate
                "x_mid": (b[0] + b[2]) / 2,
                "text": text,
                "blocks": []
            })
            
    # Sort sections by Y coordinate (top-to-bottom) then X
    # Actually, we should just assign each block to the "nearest" section header that is ABOVE it.
    
    for b in blocks:
        text = b[4].strip()
        if len(text.split()) < 4 and not re.search(r'(?:read|Read)\s+\d+(?:\.\d+)?', text):
            continue
            
        bx_mid = (b[0] + b[2]) / 2
        by = b[1] # Top Edge
        
        # Candidate headers must be physically above this block (or very close y)
        candidates = [s for s in sections if s["y"] <= by + 10]
        
        if not candidates:
            continue
            
        # Among candidates, find the one with closest X alignment or same column
        # In multi-column layouts, the block's center X should be close to the header's center X
        closest = None
        min_dist = float('inf')
        
        # We can penalize Y distance a bit less than X distance to group columns
        for c in candidates:
            dist_x = abs(c["x_mid"] - bx_mid)
            dist_y = abs(by - c["y"])
            # Weighted distance
            score = (dist_x * 2) + dist_y
            if score < min_dist:
                min_dist = score
                closest = c
                
        if closest and abs(closest["x_mid"] - bx_mid) < 200: # Threshold for column width
            closest["blocks"].append(text.replace('\n', ' '))
            
    for s in sections:
        print(f"=== {s['id']} ===")
        print(" ".join([b[:60] + "..." for b in s["blocks"]]))

if __name__ == '__main__':
    parse_pdf(sys.argv[1])
