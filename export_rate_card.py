"""
Quick script to export the current rate card for review/editing.
"""
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'multi_agent_system', 'src'))

from agents.rate_card_agent import RateCardAgent

if __name__ == "__main__":
    rate_card = RateCardAgent()
    
    # Export to CSV
    output_path = "rate_card_current.csv"
    rate_card.export_rate_card(output_path)
    
    print(f"\n✅ Rate card exported successfully!")
    print(f"📄 File: {output_path}")
    print(f"\nYou can now:")
    print("  1. Open the CSV in Excel")
    print("  2. Add/edit rates based on actual contracts")
    print("  3. Save the file")
    print("  4. Import it back using rate_card.import_rate_card('your_file.csv')")
