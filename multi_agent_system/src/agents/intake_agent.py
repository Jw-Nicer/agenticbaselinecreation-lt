
import os 
import pandas as pd
from typing import List, Dict, Tuple

class IntakeAgent:
    """
    Scans directories, identifies file types (Excel, CSV), and reads raw dataframes.
    Acts as the eyes for the system.
    
    Enhanced to:
    - Scan ALL sheets and score them for transaction data
    - Handle invoice formats by finding detail sheets
    - Detect header rows intelligently
    """
    
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.file_diagnostics = {}  # Store diagnostics for each file

    def scan_files(self) -> List[str]:
        """Returns list of valid absolute file paths."""
        files_found = []
        for root, dirs, files in os.walk(self.data_dir):
            for file in files:
                if file.lower().endswith(('.xlsx', '.xls', '.csv')) and not file.startswith('~$'):
                    files_found.append(os.path.join(root, file))
        return files_found

    def load_clean_sheet(self, filepath: str) -> Dict[str, pd.DataFrame]:
        """
        Intelligently loads an Excel file. 
        It looks for the 'header' row by finding the row with the most text columns or specific keywords.
        Returns a dictionary of {sheet_name: dataframe}.
        
        Enhanced: Now scans ALL sheets and picks the best one(s) with transaction data.
        """
        dfs = {}
        diagnostics = {'file': os.path.basename(filepath), 'sheets_analyzed': [], 'best_sheet': None}
        
        try:
            with pd.ExcelFile(filepath) as xls:
                sheet_scores = []
                
                for sheet in xls.sheet_names:
                    try:
                        # Read first ~100 rows to find the header
                        preview = pd.read_excel(xls, sheet_name=sheet, nrows=100, header=None)
                        
                        # Score this sheet for transaction data
                        sheet_score = self._score_sheet_for_transactions(preview)
                        header_row_idx = self._detect_header_row(preview)
                        
                        sheet_scores.append({
                            'sheet': sheet,
                            'score': sheet_score,
                            'header_row': header_row_idx
                        })
                        
                        diagnostics['sheets_analyzed'].append({
                            'sheet': sheet,
                            'score': sheet_score,
                            'header_row': header_row_idx
                        })
                        
                    except Exception as e:
                        pass
                
                # Sort by score and pick the best sheet(s)
                sheet_scores.sort(key=lambda x: x['score'], reverse=True)
                
                # Load sheets with score >= 3 (likely have transaction data)
                for sheet_info in sheet_scores:
                    if sheet_info['score'] >= 3 and sheet_info['header_row'] is not None:
                        sheet = sheet_info['sheet']
                        header_row_idx = sheet_info['header_row']
                        
                        full_df = pd.read_excel(xls, sheet_name=sheet, header=header_row_idx)
                        full_df = full_df.dropna(how='all')
                        
                        # Additional filter: must have at least 5 data rows
                        if len(full_df) >= 5:
                            dfs[sheet] = full_df
                            if diagnostics['best_sheet'] is None:
                                diagnostics['best_sheet'] = sheet
                    
        except Exception as e:
            diagnostics['error'] = str(e)
            print(f"Error loading {filepath}: {e}")
        
        self.file_diagnostics[filepath] = diagnostics
        return dfs

    def _score_sheet_for_transactions(self, df_preview: pd.DataFrame) -> int:
        """
        Score a sheet for how likely it contains transaction-level data.
        Higher score = more likely to have usable data.
        """
        score = 0
        
        # Convert all text to lowercase for searching
        all_text = ' '.join([str(x).lower() for x in df_preview.values.flatten() if pd.notna(x)])
        
        # Positive signals (transaction data)
        positive_keywords = ['language', 'date', 'minutes', 'duration', 'session', 
                            'call', 'charge', 'amount', 'interpreter', 'service']
        for kw in positive_keywords:
            if kw in all_text:
                score += 1
                
        # Negative signals (summary/invoice sheets)
        negative_keywords = ['total new charges', 'bill to:', 'remit to:', 'thank you for', 
                            'invoice summary', 'payment due']
        for kw in negative_keywords:
            if kw in all_text:
                score -= 2
                
        # Bonus for having many rows (transaction data typically has 50+ rows)
        if len(df_preview) > 30:
            score += 2
            
        # Negative for having very few rows (likely summary)
        if len(df_preview) < 10:
            score -= 2
            
        return score

    def _detect_header_row(self, df_preview: pd.DataFrame) -> int:
        """
        Scans a preview dataframe to find the row index that looks most like a header.
        Score based on:
        - Contains 'Language'
        - Contains 'Date'
        - Contains 'Charge' or 'Amount'
        """
        best_idx = None
        max_score = 0
        
        target_keywords = ['language', 'date', 'charge', 'amount', 'minutes', 'duration', 
                          'service', 'interpreter', 'session id', 'start time', 'call date', 
                          'invoice number', 'client id', 'description', 'quantity']
        
        for idx, row in df_preview.iterrows():
            # Convert row to string, lowercase
            row_vals = [str(x).lower() for x in row.values if pd.notna(x)]
            
            score = 0
            for val in row_vals:
                if any(k in val for k in target_keywords):
                    score += 1
            
            # Bonus: Row has many non-null string values (headers are usually strings)
            if len(row_vals) > 3: 
                score += 1
                
            if score > max_score and score >= 2: # Threshold to avoid false positives
                max_score = score
                best_idx = idx
                
        return best_idx
    
    def get_file_compatibility_report(self) -> str:
        """Generate a report of file compatibility based on diagnostics."""
        report = []
        report.append("=" * 60)
        report.append("FILE COMPATIBILITY REPORT")
        report.append("=" * 60)
        
        for filepath, diag in self.file_diagnostics.items():
            report.append(f"\nFile: {diag['file']}")
            if 'error' in diag:
                report.append(f"  [ERROR] {diag['error']}")
            else:
                report.append(f"  Sheets analyzed: {len(diag['sheets_analyzed'])}")
                report.append(f"  Best sheet: {diag['best_sheet']}")
                for s in diag['sheets_analyzed']:
                    status = "[OK]" if s['score'] >= 3 else "[SKIP]"
                    report.append(f"    {status} '{s['sheet']}': score={s['score']}, header_row={s['header_row']}")
                    
        return "\n".join(report)
