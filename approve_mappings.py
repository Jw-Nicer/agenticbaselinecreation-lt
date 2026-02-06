"""
Approve and manage pending schema mappings with correction tracking for active learning.

Usage:
    python approve_mappings.py --list                    # List all pending mappings
    python approve_mappings.py --show 0                  # Show details of pending mapping at index 0
    python approve_mappings.py --approve 0              # Approve mapping at index 0 as-is
    python approve_mappings.py --approve-all            # Approve all pending mappings
    python approve_mappings.py --correct 0              # Approve with interactive corrections
    python approve_mappings.py --stats                  # Show mapping success rates
    python approve_mappings.py --history                # Show recent correction history
"""

import argparse
import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SRC_DIR = BASE_DIR / "multi_agent_system" / "src"
sys.path.insert(0, str(SRC_DIR))

from core.memory_store import load_json, save_json
from agents.schema_agent import SchemaAgent


def show_mapping_details(entry: dict, index: int) -> None:
    """Display detailed information about a pending mapping."""
    print(f"\n{'='*60}")
    print(f"Pending Mapping [{index}]")
    print(f"{'='*60}")
    print(f"Vendor:           {entry.get('vendor', 'UNKNOWN')}")
    print(f"Source:           {entry.get('source', 'unknown')}")
    print(f"Field Confidence: {entry.get('field_confidence', 0):.2f}")
    print(f"Data Confidence:  {entry.get('data_confidence', 0):.2f}")
    print(f"\nColumns ({len(entry.get('columns', []))}):")
    for col in entry.get('columns', []):
        print(f"  - {col}")
    print(f"\nCurrent Mapping:")
    mapping = entry.get('mapping', {})
    for field, col in mapping.items():
        print(f"  {field:12} -> {col}")
    print(f"{'='*60}\n")


def approve_with_correction(agent: SchemaAgent, entry: dict, pending: list, pending_path: Path) -> None:
    """Interactive approval with optional corrections."""
    show_mapping_details(entry, pending.index(entry) if entry in pending else -1)

    print("Current mapping:")
    original_mapping = entry.get('mapping', {}).copy()
    corrected_mapping = original_mapping.copy()
    columns = entry.get('columns', [])

    # Show current mappings and allow corrections
    canonical_fields = ['date', 'language', 'minutes', 'charge', 'rate', 'modality']

    for field in canonical_fields:
        current = corrected_mapping.get(field, '(not mapped)')
        print(f"\n  {field}: {current}")
        print(f"  Enter new column name, 'skip' to remove, or press Enter to keep:")

        # Show available columns
        available = [c for c in columns if c not in corrected_mapping.values() or corrected_mapping.get(field) == c]
        if available:
            print(f"  Available: {', '.join(available[:10])}{'...' if len(available) > 10 else ''}")

        response = input("  > ").strip()

        if response.lower() == 'skip':
            if field in corrected_mapping:
                del corrected_mapping[field]
        elif response:
            if response in columns:
                corrected_mapping[field] = response
            else:
                print(f"  Warning: '{response}' not in columns, keeping original")

    # Check if corrections were made
    if corrected_mapping != original_mapping:
        print("\nCorrections detected:")
        for field in canonical_fields:
            orig = original_mapping.get(field, '(none)')
            corr = corrected_mapping.get(field, '(none)')
            if orig != corr:
                print(f"  {field}: {orig} -> {corr}")

        # Record correction for active learning
        agent.record_correction(
            source_columns=columns,
            original_mapping=original_mapping,
            corrected_mapping=corrected_mapping,
            vendor=entry.get('vendor')
        )
        print("\nCorrection recorded for active learning.")

    # Save the corrected mapping
    entry['mapping'] = corrected_mapping
    agent.save_approved_mapping(entry)

    # Remove from pending
    if entry in pending:
        pending.remove(entry)
    save_json(pending_path, pending)

    print("\nMapping approved and saved.")


def show_stats(agent: SchemaAgent) -> None:
    """Display mapping success rates."""
    rates = agent.get_success_rates()

    print("\n" + "="*50)
    print("Mapping Success Rates")
    print("="*50)

    if not rates:
        print("No statistics available yet.")
        return

    for source, stats in rates.items():
        total = stats.get('total', 0)
        corrected = stats.get('corrected', 0)
        rate = stats.get('success_rate', 1.0)
        print(f"\n{source.upper()}:")
        print(f"  Total mappings:    {total}")
        print(f"  Corrected:         {corrected}")
        print(f"  Success rate:      {rate:.1%}")

    print("="*50 + "\n")


def show_history(agent: SchemaAgent, vendor: str = None, limit: int = 10) -> None:
    """Display recent correction history."""
    history = agent.get_correction_history(vendor=vendor, limit=limit)

    print("\n" + "="*50)
    print(f"Recent Corrections{f' for {vendor}' if vendor else ''}")
    print("="*50)

    if not history:
        print("No corrections recorded yet.")
        return

    for i, entry in enumerate(history):
        print(f"\n[{i}] {entry.get('timestamp', 'unknown')}")
        print(f"    Vendor: {entry.get('vendor', 'UNKNOWN')}")
        for corr in entry.get('corrections', []):
            print(f"    {corr['field']}: {corr['original']} -> {corr['corrected']}")

    print("="*50 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Approve pending schema mappings with correction tracking.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument("--list", action="store_true", help="List pending mappings")
    parser.add_argument("--show", type=int, metavar="INDEX", help="Show details of a pending mapping")
    parser.add_argument("--approve-all", action="store_true", help="Approve all pending mappings")
    parser.add_argument("--approve", type=int, metavar="INDEX", help="Approve a single pending mapping by index")
    parser.add_argument("--correct", type=int, metavar="INDEX", help="Approve with interactive corrections")
    parser.add_argument("--stats", action="store_true", help="Show mapping success rates")
    parser.add_argument("--history", action="store_true", help="Show recent correction history")
    parser.add_argument("--vendor", type=str, help="Filter by vendor (for --history)")
    args = parser.parse_args()

    agent = SchemaAgent()
    pending_path = Path(BASE_DIR) / "agent_memory" / "pending_mappings.json"
    pending = load_json(pending_path, [])
    if not isinstance(pending, list):
        pending = []

    if args.stats:
        show_stats(agent)
        return

    if args.history:
        show_history(agent, vendor=args.vendor)
        return

    if args.list:
        if not pending:
            print("No pending mappings.")
            return
        print(f"\n{'='*70}")
        print(f"{'Idx':<5} {'Vendor':<20} {'Source':<12} {'Field':<8} {'Data':<8}")
        print(f"{'='*70}")
        for i, entry in enumerate(pending):
            vendor = entry.get("vendor", "UNKNOWN")[:18]
            source = entry.get("source", "unknown")[:10]
            field_conf = entry.get("field_confidence", 0)
            data_conf = entry.get("data_confidence", 0)
            print(f"[{i:<3}] {vendor:<20} {source:<12} {field_conf:<8.2f} {data_conf:<8.2f}")
        print(f"{'='*70}\n")
        print(f"Total: {len(pending)} pending mappings")
        print("Use --show INDEX to see details, --approve INDEX to approve, --correct INDEX to approve with corrections")
        return

    if args.show is not None:
        if args.show < 0 or args.show >= len(pending):
            print("Invalid index.")
            return
        show_mapping_details(pending[args.show], args.show)
        return

    if args.approve_all:
        if not pending:
            print("No pending mappings to approve.")
            return
        count = len(pending)
        for entry in pending:
            agent.save_approved_mapping(entry)
            # Track as successful (no correction needed)
            agent.track_mapping_success(source=entry.get('source'))
        save_json(pending_path, [])
        print(f"Approved {count} mappings.")
        return

    if args.approve is not None:
        if args.approve < 0 or args.approve >= len(pending):
            print("Invalid index.")
            return
        entry = pending.pop(args.approve)
        agent.save_approved_mapping(entry)
        agent.track_mapping_success(source=entry.get('source'))
        save_json(pending_path, pending)
        print("Approved 1 mapping.")
        return

    if args.correct is not None:
        if args.correct < 0 or args.correct >= len(pending):
            print("Invalid index.")
            return
        entry = pending[args.correct]
        approve_with_correction(agent, entry, pending, pending_path)
        return

    parser.print_help()


if __name__ == "__main__":
    main()
