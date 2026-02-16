
import sys
from pathlib import Path
import pandas as pd
import datetime

# Ensure src is in path
BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR / "multi_agent_system" / "src"))

from agents.standardizer_agent import StandardizerAgent
from core.canonical_schema import CanonicalRecord

def test_standardizer_basic():
    agent = StandardizerAgent()
    df = pd.DataFrame([
        {"Call Date": "2024-01-01", "Lang": "Spanish", "Mins": 10, "Total": 12.50}
    ])
    mapping = {
        "date": "Call Date",
        "language": "Lang",
        "minutes": "Mins",
        "charge": "Total"
    }

    records = agent.process_dataframe(df, mapping, "test.csv", "VendorA")

    assert len(records) == 1
    assert isinstance(records[0], CanonicalRecord)
    assert records[0].language == "Spanish"
    assert records[0].minutes_billed == 10.0
    assert records[0].total_charge == 12.50
    assert records[0].date == datetime.date(2024, 1, 1)

if __name__ == "__main__":
    try:
        test_standardizer_basic()
        print("Standardizer Unit Test Passed!")
    except Exception as e:
        print(f"Standardizer Unit Test Failed: {e}")
        exit(1)
