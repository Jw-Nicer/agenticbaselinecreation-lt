
import os
import subprocess
import json
import shutil
from pathlib import Path

def test_full_pipeline_e2e():
    # Setup
    client = "test_client"
    input_dir = "tests/fixtures"

    # Run pipeline via CLI
    cmd = [
        "python", "baseline", "run",
        "--input", input_dir,
        "--client", client
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0, f"Pipeline failed: {result.stderr}"

    # Verify outputs
    out_dir = Path("out") / client
    assert out_dir.exists(), "Output directory not created"

    # Get the latest run
    runs = sorted([d for d in out_dir.iterdir() if d.is_dir()])
    assert len(runs) > 0, "No run directory found"
    latest_run = runs[-1]

    assert (latest_run / "baseline_v1_output.csv").exists()
    assert (latest_run / "manifest.json").exists()

    # Check manifest
    with open(latest_run / "manifest.json", "r") as f:
        manifest = json.load(f)

    assert manifest["client"] == client
    assert manifest["metrics"]["total_records"] > 0
    assert manifest["status"] == "COMPLETE"

if __name__ == "__main__":
    # If run directly, just run the test
    try:
        test_full_pipeline_e2e()
        print("E2E Test Passed!")
    except Exception as e:
        print(f"E2E Test Failed: {e}")
        exit(1)
