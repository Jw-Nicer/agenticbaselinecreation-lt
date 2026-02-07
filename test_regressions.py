import math
import os
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
SRC_DIR = BASE_DIR / "multi_agent_system" / "src"
sys.path.insert(0, str(SRC_DIR))

from agents.aggregator_agent import AggregatorAgent
from agents.intake_agent import IntakeAgent
from agents.schema_agent import SchemaAgent
from agents.simulator_agent import SimulatorAgent
from agents.qa_agent import QAgent
from core.canonical_schema import CanonicalRecord


class RegressionTests(unittest.TestCase):
    def test_csv_ingestion_loads_transaction_sheet(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, "vendor_sample.csv")
            rows = [
                "Service Date,Language,Minutes,Charge,Service Type",
                "2025-01-01,Spanish,10,$15.00,OPI",
                "2025-01-02,Mandarin,5,$10.00,VRI",
                "2025-01-03,Arabic,8,$12.00,OPI",
                "2025-01-04,French,12,$20.00,OPI",
                "2025-01-05,Korean,7,$11.00,VRI",
                "2025-01-06,Russian,9,$14.00,OPI",
            ]
            with open(csv_path, "w", encoding="utf-8") as f:
                f.write("\n".join(rows))

            intake = IntakeAgent(tmpdir)
            sheets = intake.load_clean_sheet(csv_path)

            self.assertIn("csv", sheets)
            self.assertGreaterEqual(len(sheets["csv"]), 5)

            raw_sheets = intake.load_all_sheets_for_reconciliation(csv_path)
            self.assertIn("csv_raw", raw_sheets)
            self.assertFalse(raw_sheets["csv_raw"].empty)

    def test_schema_assess_mapping_handles_currency_strings(self):
        df = pd.DataFrame(
            {
                "Service Date": ["2025-01-01", "2025-01-02", "2025-01-03"],
                "Language": ["Spanish", "Mandarin", "Arabic"],
                "Minutes": ["10", "5", "8"],
                "Total Charge": ["$15.00", "$10.25", "$12.75"],
            }
        )
        mapping = {
            "date": "Service Date",
            "language": "Language",
            "minutes": "Minutes",
            "charge": "Total Charge",
        }

        schema = SchemaAgent()
        assessment = schema.assess_mapping(df, mapping)

        self.assertGreater(assessment["data_confidence"], 0.8)
        self.assertGreater(assessment["final_confidence"], 0.6)

    def test_aggregator_zero_minutes_does_not_produce_inf(self):
        records = [
            CanonicalRecord(
                source_file="x.csv",
                vendor="TestVendor",
                date=pd.Timestamp("2025-01-01").date(),
                language="Spanish",
                modality="OPI",
                minutes_billed=0.0,
                total_charge=20.0,
            )
        ]

        baseline = AggregatorAgent().create_baseline(records)

        self.assertEqual(float(baseline.iloc[0]["CPM"]), 0.0)
        self.assertEqual(float(baseline.iloc[0]["Avg_Call_Length"]), 0.0)

    def test_simulator_handles_zero_opi_minutes(self):
        baseline = pd.DataFrame(
            [
                {"Month": "2025-01", "Vendor": "V", "Language": "Spanish", "Modality": "VRI", "Minutes": 100.0, "Cost": 120.0, "Calls": 10, "CPM": 1.2},
                {"Month": "2025-01", "Vendor": "V", "Language": "Spanish", "Modality": "OPI", "Minutes": 0.0, "Cost": 0.0, "Calls": 0, "CPM": 0.0},
            ]
        )

        out = SimulatorAgent().run_scenarios(baseline)
        savings = out["scenarios"]["vri_to_opi_shift"]["annual_impact"]

        self.assertTrue(math.isfinite(float(savings)))
        self.assertGreaterEqual(float(savings), 0.0)

    def test_qa_quarantined_records_are_excluded(self):
        records = [
            CanonicalRecord(
                source_file="x.csv",
                vendor="V",
                date=pd.Timestamp("2025-01-01").date(),
                language="Unknown",
                modality="OPI",
                minutes_billed=10.0,
                total_charge=10.0,
            ),
            CanonicalRecord(
                source_file="x.csv",
                vendor="V",
                date=pd.Timestamp("2025-01-01").date(),
                language="Spanish",
                modality="OPI",
                minutes_billed=10.0,
                total_charge=10.0,
            ),
        ]

        out, stats = QAgent().process_records(records)
        self.assertEqual(stats["critical_errors_quarantined"], 1)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].language, "Spanish")

    def test_qa_missing_cost_is_quarantined(self):
        records = [
            CanonicalRecord(
                source_file="x.csv",
                vendor="V",
                date=pd.Timestamp("2025-01-01").date(),
                language="Spanish",
                modality="OPI",
                minutes_billed=12.0,
                total_charge=0.0,
            ),
            CanonicalRecord(
                source_file="x.csv",
                vendor="V",
                date=pd.Timestamp("2025-01-01").date(),
                language="Spanish",
                modality="OPI",
                minutes_billed=12.0,
                total_charge=10.0,
            ),
        ]

        out, stats = QAgent().process_records(records)
        self.assertEqual(stats["critical_errors_quarantined"], 1)
        self.assertEqual(len(out), 1)
        self.assertGreater(out[0].total_charge, 0.0)


if __name__ == "__main__":
    unittest.main()
