import fitz
import sys
import glob
import os
import json
import re

def clean_text(text):
    text = text.replace('\ufffd', "'")
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def parse_pdf(pdf_path, is_scenario=False):
    print(f"Parsing {pdf_path}")
    doc = fitz.open(pdf_path)
    data = {}
    
    for i in range(len(doc)):
        page = doc[i]
        blocks = page.get_text("blocks")
        
        # Determine the primary keys on this page.
        # Scenarios have a single primary key per page defined by the bullet title.
        # Sections can have multiple sub-sections per page (e.g. 140.1, 140.2)
        
        if is_scenario:
            page_key = None
            for b in blocks:
                text = b[4].strip()
                match = re.search(r'^(\d+)\s*\u2022', text)
                if match:
                    page_key = match.group(1)
                    break
                    
            if page_key:
                if page_key not in data:
                    data[page_key] = {"text": "", "links": []}
                    
                for b in blocks:
                    text = b[4].strip()
                    page_text = clean_text(text)
                    
                    if len(text.split()) > 3 or re.search(r'(?:read|Read)\s+\d+(?:\.\d+)?', text) or re.search(r'^(\d+)\s*\u2022', text):
                        data[page_key]["text"] += " " + page_text
                        
                    links = re.findall(r'(?:read|Read)\s+(\d+(?:\.\d+)?)', page_text)
                    for link in links:
                        if link not in data[page_key]["links"]:
                            data[page_key]["links"].append(link)
        else:
            # SECTION BOOK LOGIC
            # Find sub-section headers (e.g. " 140.2 \u2022 A Waiting Game")
            # Or standalone numbers like "140.2" prominently at top of text blocks
            sections_on_page = []
            
            for b in blocks:
                text = b[4].strip()
                # Matches "140.1", " 140.1 ", "140.1 •"
                match = re.search(r'^\s*(\d+\.\d+)\s*[\u2022\ufffd\-\.]?', text)
                if match:
                    sec_id = match.group(1)
                    sections_on_page.append({
                        "id": sec_id,
                        "x_left": b[0],
                        "y": b[1]
                    })
                    if sec_id not in data:
                        data[sec_id] = {"text": "", "links": []}
            
            # If no clear section header, maybe try the fallback (e.g. whole number page)
            if not sections_on_page:
                full_text = page.get_text()
                match = re.search(r'^\s*(\d+(?:\.\d+)?)\s*$', full_text, re.MULTILINE)
                if match:
                    sec_id = match.group(1)
                    sections_on_page.append({
                        "id": sec_id,
                        "x_left": 0, # Dummy left align
                        "y": 0 # Top of page
                    })
                    if sec_id not in data:
                        data[sec_id] = {"text": "", "links": []}
                        
            # GROUP HEADERS BY ROWS (to accurately handle multi-column vs page-width headers)
            rows = []
            for s in sorted(sections_on_page, key=lambda x: x["y"]):
                placed = False
                for r in rows:
                    if abs(r["y"] - s["y"]) < 30: # Same horizontal row
                        r["headers"].append(s)
                        placed = True
                        break
                if not placed:
                    rows.append({"y": s["y"], "headers": [s]})
                    
            # Sort rows by Y descending (bottom-most last, top-most first)
            # Actually, we want to find the row immediately above the text block
            rows.sort(key=lambda r: r["y"], reverse=True)
                        
            # Distance-based assignment to separate text from columns
            for b in blocks:
                text = b[4].strip()
                if len(text.split()) < 4 and not re.search(r'(?:read|Read)\s+\d+(?:\.\d+)?', text):
                    continue
                    
                bx0 = b[0]
                by = b[1]
                
                assigned = False
                for r in rows:
                    # Candidates must be physically above or very close (y-coord)
                    if r["y"] <= by + 10:
                        # Find closest header in this row by left X alignment
                        closest = min(r["headers"], key=lambda h: abs(h["x_left"] - bx0))
                        
                        sec_id = closest["id"]
                        page_text = clean_text(text)
                        data[sec_id]["text"] += " " + page_text
                        
                        # Look for goals / links
                        links = re.findall(r'(?:read|Read)\s+(\d+(?:\.\d+)?)', page_text)
                        for link in links:
                            if link not in data[sec_id]["links"]:
                                data[sec_id]["links"].append(link)
                                
                        assigned = True
                        break
                        
                if not assigned and rows:
                    # If it's above all rows, assign to the nearest header in the topmost row (last in the sorted reversed list)
                    closest = min(rows[-1]["headers"], key=lambda h: abs(h["x_left"] - bx0))
                    sec_id = closest["id"]
                    page_text = clean_text(text)
                    data[sec_id]["text"] += " " + page_text
                    
                    links = re.findall(r'(?:read|Read)\s+(\d+(?:\.\d+)?)', page_text)
                    for link in links:
                        if link not in data[sec_id]["links"]:
                            data[sec_id]["links"].append(link)
                    
    # Clean up
    for k in data:
        data[k]["text"] = clean_text(data[k]["text"])
        
    return data

def main():
    base_dir = r"c:\Users\marti\Documents\FrosthavenSummary\worldhaven-master\images\books\frosthaven"
    
    scenario_files = glob.glob(os.path.join(base_dir, "fh-scenario-book-*.pdf"))
    section_files = glob.glob(os.path.join(base_dir, "fh-section-book-*.pdf"))
    
    database = {
        "scenarios": {},
        "sections": {}
    }
    
    for f in scenario_files:
        parsed = parse_pdf(f, is_scenario=True)
        for k, v in parsed.items():
             database["scenarios"][k] = v
                 
    for f in section_files:
        parsed = parse_pdf(f, is_scenario=False)
        for k, v in parsed.items():
            if '.' in k or k.isdigit():
                 database["sections"][k] = v
                 
    out_path = "frosthaven_data.json"
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(database, f, indent=2, ensure_ascii=False)
        
    print(f"Saved database to {out_path}")
    print(f"Total Scenarios parsed: {len(database['scenarios'])}")
    print(f"Total Sections parsed: {len(database['sections'])}")

if __name__ == '__main__':
    main()
