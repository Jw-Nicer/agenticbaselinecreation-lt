
import pandas as pd

file_path = "baseline_v1_output.csv"
try:
    df = pd.read_csv(file_path)
    
    print("="*60)
    print("SCANNING GENERATED BASELINE REPORT (baseline_v1_output.csv)")
    print("="*60)
    print(f"Total Rows: {len(df):,}")
    print(f"Total Spend: ${df['Cost'].sum():,.2f}")
    print(f"Total Minutes: {df['Minutes'].sum():,.0f}")
    
    print("\nTOP 5 LANGUAGES BY SPEND:")
    print(df.groupby("Language")["Cost"].sum().sort_values(ascending=False).head(5))
    
    print("\nSPEND BY VENDOR:")
    print(df.groupby("Vendor")["Cost"].sum().sort_values(ascending=False))
    
    print("\nSPEND BY MODALITY:")
    print(df.groupby("Modality")["Cost"].sum().sort_values(ascending=False))
    
    print("\nSAMPLE ROWS (First 5):")
    print(df.head(5).to_string(index=False))

except Exception as e:
    print(f"Error reading report: {e}")
