"""
COMPREHENSIVE WORD DOCUMENT EXTRACTOR
Extracts ALL content from .docx files:
- Full text
- Tables (from XML)
- Images (saved as files)
- Embedded Excel sheets (saved as files)
"""

import zipfile
import os
import glob
import re
import shutil
import xml.etree.ElementTree as ET

# Configuration
REPORT_DIR = r"c:\Users\John\.gemini\antigravity\playground\multiagent-baseline-lt\baseline reports lt"
OUTPUT_DIR = r"c:\Users\John\.gemini\antigravity\playground\multiagent-baseline-lt\extracted_report_content"

# Namespaces used in Word XML
WORD_NS = {
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'wp': 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing'
}

def extract_text_from_docx(z):
    """Extract all text content from document.xml"""
    try:
        xml_content = z.read('word/document.xml')
        tree = ET.fromstring(xml_content)
        
        paragraphs = []
        current_para = []
        
        for elem in tree.iter():
            # Text content
            if elem.tag.endswith('}t'):
                if elem.text:
                    current_para.append(elem.text)
            # Paragraph break
            elif elem.tag.endswith('}p'):
                if current_para:
                    paragraphs.append(''.join(current_para))
                    current_para = []
        
        if current_para:
            paragraphs.append(''.join(current_para))
            
        return '\n'.join(paragraphs)
    except Exception as e:
        return f"[Error extracting text: {e}]"

def extract_tables_from_docx(z):
    """Extract table data from document.xml"""
    tables = []
    try:
        xml_content = z.read('word/document.xml')
        tree = ET.fromstring(xml_content)
        
        # Find all table elements
        for tbl in tree.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tbl'):
            table_data = []
            for row in tbl.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tr'):
                row_data = []
                for cell in row.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tc'):
                    cell_text = []
                    for t in cell.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'):
                        if t.text:
                            cell_text.append(t.text)
                    row_data.append(' '.join(cell_text))
                if row_data:
                    table_data.append(row_data)
            if table_data:
                tables.append(table_data)
    except Exception as e:
        print(f"    [Warning] Table extraction error: {e}")
    
    return tables

def extract_images(z, output_folder):
    """Extract all images from word/media/"""
    images_extracted = []
    media_folder = os.path.join(output_folder, 'images')
    os.makedirs(media_folder, exist_ok=True)
    
    for name in z.namelist():
        if name.startswith('word/media/'):
            img_name = os.path.basename(name)
            img_path = os.path.join(media_folder, img_name)
            with z.open(name) as src, open(img_path, 'wb') as dst:
                dst.write(src.read())
            images_extracted.append(img_name)
    
    return images_extracted

def extract_embeddings(z, output_folder):
    """Extract embedded Excel/OLE objects"""
    embeddings_extracted = []
    embed_folder = os.path.join(output_folder, 'embedded_files')
    os.makedirs(embed_folder, exist_ok=True)
    
    for name in z.namelist():
        if name.startswith('word/embeddings/'):
            emb_name = os.path.basename(name)
            emb_path = os.path.join(embed_folder, emb_name)
            with z.open(name) as src, open(emb_path, 'wb') as dst:
                dst.write(src.read())
            embeddings_extracted.append(emb_name)
    
    return embeddings_extracted

def format_table_as_text(table):
    """Convert table data to readable text format"""
    if not table:
        return ""
    
    # Calculate column widths
    col_widths = []
    for row in table:
        for i, cell in enumerate(row):
            if i >= len(col_widths):
                col_widths.append(len(str(cell)))
            else:
                col_widths[i] = max(col_widths[i], len(str(cell)))
    
    # Format rows
    lines = []
    for row in table:
        formatted_cells = []
        for i, cell in enumerate(row):
            width = col_widths[i] if i < len(col_widths) else 20
            formatted_cells.append(str(cell).ljust(width)[:50])  # Cap at 50 chars
        lines.append(' | '.join(formatted_cells))
    
    return '\n'.join(lines)

def main():
    # Create output directory
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR)
    
    files = glob.glob(os.path.join(REPORT_DIR, "*.docx"))
    print(f"{'='*70}")
    print(f"EXTRACTING ALL CONTENT FROM {len(files)} WORD REPORTS")
    print(f"{'='*70}\n")
    
    master_summary = []
    
    for filepath in files:
        filename = os.path.basename(filepath)
        safe_name = re.sub(r'[^\w\-]', '_', filename.replace('.docx', ''))[:50]
        doc_output_folder = os.path.join(OUTPUT_DIR, safe_name)
        os.makedirs(doc_output_folder, exist_ok=True)
        
        print(f"Processing: {filename}")
        
        try:
            with zipfile.ZipFile(filepath) as z:
                # 1. Extract Text
                print("  - Extracting text...")
                text_content = extract_text_from_docx(z)
                text_path = os.path.join(doc_output_folder, 'full_text.txt')
                with open(text_path, 'w', encoding='utf-8') as f:
                    f.write(text_content)
                
                # 2. Extract Tables
                print("  - Extracting tables...")
                tables = extract_tables_from_docx(z)
                if tables:
                    tables_path = os.path.join(doc_output_folder, 'tables.txt')
                    with open(tables_path, 'w', encoding='utf-8') as f:
                        for i, table in enumerate(tables):
                            f.write(f"\n{'='*50}\nTABLE {i+1}\n{'='*50}\n")
                            f.write(format_table_as_text(table))
                            f.write("\n")
                
                # 3. Extract Images
                print("  - Extracting images...")
                images = extract_images(z, doc_output_folder)
                
                # 4. Extract Embedded Files
                print("  - Extracting embedded files...")
                embeddings = extract_embeddings(z, doc_output_folder)
                
                # Summary for this document
                summary = {
                    'file': filename,
                    'text_length': len(text_content),
                    'tables_count': len(tables),
                    'images_count': len(images),
                    'embeddings_count': len(embeddings),
                    'output_folder': doc_output_folder
                }
                master_summary.append(summary)
                
                print(f"  ✓ Text: {len(text_content):,} chars")
                print(f"  ✓ Tables: {len(tables)}")
                print(f"  ✓ Images: {len(images)}")
                print(f"  ✓ Embedded files: {len(embeddings)}")
                print()
                
        except Exception as e:
            print(f"  ✗ Error: {e}\n")
    
    # Write master summary
    summary_path = os.path.join(OUTPUT_DIR, 'EXTRACTION_SUMMARY.txt')
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write("EXTRACTION SUMMARY\n")
        f.write("="*50 + "\n\n")
        for s in master_summary:
            f.write(f"File: {s['file']}\n")
            f.write(f"  Text: {s['text_length']:,} characters\n")
            f.write(f"  Tables: {s['tables_count']}\n")
            f.write(f"  Images: {s['images_count']}\n")
            f.write(f"  Embedded: {s['embeddings_count']}\n")
            f.write(f"  Output: {s['output_folder']}\n\n")
    
    print("="*70)
    print(f"EXTRACTION COMPLETE!")
    print(f"All content saved to: {OUTPUT_DIR}")
    print("="*70)

if __name__ == "__main__":
    main()
