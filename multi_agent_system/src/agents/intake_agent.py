
import os
import hashlib
from contextlib import contextmanager
import pandas as pd
from typing import List, Dict, Any
from core.memory_store import ensure_memory_dir, load_json, save_json

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
        mem_dir = ensure_memory_dir()
        self._classify_path = mem_dir / "intake_classifications.json"
        self._classify_cache = load_json(self._classify_path, {})
        try:
            from core.ai_client import AIClient
            self.ai = AIClient()
        except ImportError:
            self.ai = None

    def scan_files(self) -> List[str]:
        """Returns list of valid absolute file paths."""
        files_found = []
        for root, dirs, files in os.walk(self.data_dir):
            for file in files:
                if file.lower().endswith(('.xlsx', '.xls', '.csv')) and not file.startswith('~$'):
                    files_found.append(os.path.join(root, file))
        return files_found

    @contextmanager
    def _open_excel_file(self, filepath: str):
        """
        Open Excel files with engine settings that suppress noisy legacy .xls logs.
        """
        ext = os.path.splitext(filepath)[1].lower()
        if ext == ".xls":
            with open(os.devnull, "w", encoding="utf-8") as sink:
                with pd.ExcelFile(filepath, engine="xlrd", engine_kwargs={"logfile": sink}) as xls:
                    yield xls
            return
        with pd.ExcelFile(filepath) as xls:
            yield xls

    def load_clean_sheet(self, filepath: str) -> Dict[str, pd.DataFrame]:
        """
        Intelligently loads an Excel file. 
        It looks for the 'header' row by finding the row with the most text columns or specific keywords.
        Returns a dictionary of {sheet_name: dataframe}.
        
        Enhanced: Now scans ALL sheets and picks the best one(s) with transaction data.
        """
        dfs = {}
        diagnostics = {'file': os.path.basename(filepath), 'sheets_analyzed': [], 'best_sheet': None}
        ext = os.path.splitext(filepath)[1].lower()

        # CSV path: treat as a single logical sheet
        if ext == ".csv":
            try:
                preview = pd.read_csv(filepath, nrows=100, header=None)
                sheet_name = "csv"
                sheet_score = self._score_sheet_for_transactions(preview)
                header_row_idx = self._detect_header_row(preview)
                classification = self._classify_sheet(preview, filepath, sheet_name, sheet_score)

                diagnostics['sheets_analyzed'].append({
                    'sheet': sheet_name,
                    'score': sheet_score,
                    'header_row': header_row_idx,
                    'classification': classification
                })

                is_transaction = classification.get('type') == 'transaction' and classification.get('confidence', 0) >= 0.6
                strong_heuristic = sheet_score >= 3
                if (strong_heuristic or is_transaction) and header_row_idx is not None:
                    full_df = pd.read_csv(filepath, header=header_row_idx)
                    full_df = full_df.dropna(how='all')
                    if len(full_df) >= 5:
                        dfs[sheet_name] = full_df
                        diagnostics['best_sheet'] = sheet_name
            except Exception as e:
                diagnostics['error'] = str(e)
                print(f"Error loading {filepath}: {e}")

            self.file_diagnostics[filepath] = diagnostics
            return dfs
        
        try:
            with self._open_excel_file(filepath) as xls:
                sheet_scores = []
                    
                for sheet in xls.sheet_names:
                    try:
                        # Read first ~100 rows to find the header
                        preview = pd.read_excel(xls, sheet_name=sheet, nrows=100, header=None)
                        
                        # Score this sheet for transaction data
                        sheet_score = self._score_sheet_for_transactions(preview)
                        header_row_idx = self._detect_header_row(preview)
                        classification = self._classify_sheet(preview, filepath, sheet, sheet_score)
                        
                        sheet_scores.append({
                            'sheet': sheet,
                            'score': sheet_score,
                            'header_row': header_row_idx,
                            'classification': classification
                        })
                        
                        diagnostics['sheets_analyzed'].append({
                            'sheet': sheet,
                            'score': sheet_score,
                            'header_row': header_row_idx,
                            'classification': classification
                        })
                        
                    except Exception as e:
                        diagnostics['sheets_analyzed'].append({
                            'sheet': sheet,
                            'score': None,
                            'header_row': None,
                            'error': str(e)
                        })
                        continue
                
                # Sort by score and pick the best sheet(s)
                sheet_scores.sort(key=lambda x: x['score'], reverse=True)
                
                # Load sheets with score >= 3 (likely have transaction data)
                for sheet_info in sheet_scores:
                    classification = sheet_info.get('classification', {})
                    is_transaction = classification.get('type') == 'transaction' and classification.get('confidence', 0) >= 0.6
                    strong_heuristic = sheet_info['score'] >= 3
                    if (strong_heuristic or is_transaction) and sheet_info['header_row'] is not None:
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

    def load_all_sheets_for_reconciliation(self, filepath: str) -> Dict[str, pd.DataFrame]:
        """
        Load broad/raw sheet data for reconciliation scans.
        Unlike load_clean_sheet(), this does not filter for transaction-only sheets.
        """
        sheets = {}
        ext = os.path.splitext(filepath)[1].lower()

        try:
            if ext == ".csv":
                sheets["csv_raw"] = pd.read_csv(filepath, header=None)
                return sheets

            with self._open_excel_file(filepath) as xls:
                for sheet in xls.sheet_names:
                    try:
                        sheets[sheet] = pd.read_excel(xls, sheet_name=sheet, header=None)
                    except Exception:
                        continue
        except Exception:
            return {}

        return sheets

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

    def _classify_sheet(self, df_preview: pd.DataFrame, filepath: str, sheet_name: str, score: int) -> Dict[str, Any]:
        """
        Classify a sheet as transaction/invoice/summary/unknown.
        Uses heuristics first, then AI when ambiguous. Caches results by preview signature.
        """
        signature = self._preview_signature(df_preview, filepath, sheet_name)
        cached = self._classify_cache.get(signature)
        if cached:
            return cached

        # Heuristic decision
        if score >= 3:
            result = {"type": "transaction", "confidence": 0.7, "source": "heuristic"}
            self._cache_classification(signature, result)
            return result
        if score <= 0:
            result = {"type": "summary", "confidence": 0.6, "source": "heuristic"}
            self._cache_classification(signature, result)
            return result

        # AI fallback for ambiguous scores
        if self.ai and self.ai.enabled:
            sample_rows = df_preview.fillna("").astype(str).values.tolist()
            sample_rows = sample_rows[:12]
            system_prompt = (
                "You are an intake classifier for language services spreadsheets. "
                "Classify the sheet type based on the preview."
            )
            user_prompt = (
                f"File: {os.path.basename(filepath)}\n"
                f"Sheet: {sheet_name}\n"
                f"Heuristic score: {score}\n"
                f"Preview rows (raw, header not detected): {sample_rows}\n\n"
                "Return JSON: {\"type\": \"transaction|invoice|summary|unknown\", \"confidence\": 0-1, \"rationale\": \"...\"}"
            )
            ai_result = self.ai.complete_json(system_prompt, user_prompt)
            if isinstance(ai_result, dict):
                ctype = str(ai_result.get("type", "unknown")).strip().lower()
                if ctype not in {"transaction", "invoice", "summary", "unknown"}:
                    ctype = "unknown"
                try:
                    conf = float(ai_result.get("confidence", 0))
                except Exception:
                    conf = 0.0
                result = {"type": ctype, "confidence": conf, "source": "ai", "rationale": ai_result.get("rationale")}
                self._cache_classification(signature, result)
                return result

        result = {"type": "unknown", "confidence": 0.0, "source": "heuristic"}
        self._cache_classification(signature, result)
        return result

    def _preview_signature(self, df_preview: pd.DataFrame, filepath: str, sheet_name: str) -> str:
        # Hash a small, deterministic slice of the preview for caching
        flat = df_preview.fillna("").astype(str).values.flatten().tolist()
        joined = "|".join(flat[:200])
        payload = f"{os.path.basename(filepath)}::{sheet_name}::{joined}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]

    def _cache_classification(self, signature: str, result: Dict[str, Any]) -> None:
        self._classify_cache[signature] = result
        save_json(self._classify_path, self._classify_cache)
    
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
                    ctype = s.get('classification', {}).get('type', 'unknown')
                    csrc = s.get('classification', {}).get('source', 'n/a')
                    report.append(f"    {status} '{s['sheet']}': score={s['score']}, header_row={s['header_row']}, type={ctype} ({csrc})")
                    
        return "\n".join(report)
