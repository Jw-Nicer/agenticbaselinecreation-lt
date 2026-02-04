
import zipfile
import os
import glob
import re

report_dir = r"c:\Users\John\.gemini\antigravity\playground\multiagent-baseline-lt\baseline reports lt"
files = glob.glob(os.path.join(report_dir, "*.docx"))

print(f"ANALYZING {len(files)} LEGACY REPORTS\n")

for filepath in files:
    filename = os.path.basename(filepath)
    print("="*80)
    print(f"📂 REPORT: {filename}")
    print("="*80)
    
    try:
        with zipfile.ZipFile(filepath) as z:
            # 1. Check for Images and Embeddings
            all_files = z.namelist()
            images = [f for f in all_files if f.startswith('word/media/')]
            embeddings = [f for f in all_files if f.startswith('word/embeddings/')]
            
            print(f"  🖼️  Images found: {len(images)} (Tables likely pasted as screenshots)")
            if len(embeddings) > 0:
                print(f"  📊 Embedded Spreadsheets: {len(embeddings)} (Actual Excel data hidden inside!)")
                for e in embeddings:
                    print(f"      - {os.path.basename(e)}")
            
            # 2. Extract Text to find Dates and Table Titles
            xml_content = z.read('word/document.xml').decode('utf-8')
            
            # Simple XML cleanup to get text
            text_content = re.sub(r'<[^>]+>', '', xml_content)
            
            # Find Dates (Month Year or MM/DD/YYYY)
            dates = re.findall(r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s\d{4}', text_content)
            dates += re.findall(r'\d{1,2}/\d{1,2}/\d{2,4}', text_content)
            unique_dates = sorted(list(set(dates)))
            
            print(f"\n  📅 PERIODS IDENTIFIED:")
            if unique_dates:
                print(f"      {', '.join(unique_dates[:5])} ...")
            else:
                print("      (No explicit dates found in text)")
            
            # Find Table Captions or Context
            # Looking for "Table X", "Figure X" or words like "Spend by", "Usage by"
            print(f"\n  📑 TABLE TYPES DETECTED (Based on text context):")
            keywords = ["Spend by", "Volume by", "Top 10", "Analysis", "Table", "Figure", "Baseline"]
            
            # Find lines containing these keywords
            found_tables = []
            # Split by rough paragraph markers in XML often leaves clues, 
            # but here we search the raw text blob.
            # Let's search for short phrases surrounding keywords
            for kw in keywords:
                matches = re.finditer(f"([^.]{{0,50}}{kw}[^.]{{0,50}})", text_content)
                for m in matches:
                    clean_match = m.group(1).strip()
                    if len(clean_match) > 10 and clean_match not in found_tables:
                        found_tables.append(clean_match)
            
            for t in found_tables[:10]: # Show top 10 detections
                print(f"      - \"...{t}...\"")
                
    except Exception as e:
        print(f"  ❌ Error analyzing file: {e}")
    print("\n")
