
import zipfile
import xml.etree.ElementTree as ET
import os
import glob

def read_docx(filepath):
    """
    Reads text from a .docx file by extracting the XML content.
    No external libraries required (uses standard zipfile/xml).
    """
    try:
        with zipfile.ZipFile(filepath) as z:
            xml_content = z.read('word/document.xml')
        
        tree = ET.fromstring(xml_content)
        
        # XML namespace for Word
        namespaces = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        
        text = []
        for node in tree.iter():
            if node.tag.endswith('t'):  # 't' tag contains text
                if node.text:
                    text.append(node.text)
            elif node.tag.endswith('p'): # 'p' tag is paragraph
                text.append('\n')
                
        return "".join(text)
    except Exception as e:
        return f"[Error reading file: {e}]"

# Scan the baseline reports directory
report_dir = r"c:\Users\John\.gemini\antigravity\playground\multiagent-baseline-lt\baseline reports lt"
files = glob.glob(os.path.join(report_dir, "*.docx"))

print(f"Found {len(files)} Word reports.\n")

for filepath in files:
    filename = os.path.basename(filepath)
    print("="*60)
    print(f"📄 REPORT: {filename}")
    print("="*60)
    
    content = read_docx(filepath)
    
    # improved cleanup
    clean_text = content.replace('\n\n', '\n').strip()
    
    # Print first 500 characters to show we read it
    print(f"Extract (first 800 chars):\n")
    print(clean_text[:800] + "...\n")
    
    # Try to find key numbers (dollar amounts)
    import re
    amounts = re.findall(r'\$\s?[\d,]+(?:\.\d{2})?', clean_text)
    if amounts:
        print(f"💰 Found {len(amounts)} financial figures. Top 5: {amounts[:5]}")
    else:
        print("⚠️ No financial figures found (maybe formatted differently)")
        
    print("\n")
