import argparse
import json
import math
import sys
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd


BASELINE_CANDIDATES = {
    "cost": ["Cost", "TotalCost", "Spend", "Amount", "total_cost", "total_spend"],
    "minutes": ["Minutes", "Duration", "TotalMinutes", "minutes", "total_minutes"],
    "calls": ["Calls", "CallCount", "Count", "calls", "call_count"],
    "cpm": ["CPM", "CostPerMinute", "RatePerMinute", "cost_per_minute", "rate_per_minute"],
    "profile": ["Vendor", "Profile", "Client", "Account", "Facility", "vendor", "profile"],
}

TX_CANDIDATES = {
    "cost": ["total_charge", "charge", "cost", "amount", "TotalCharge", "Cost"],
    "minutes": ["minutes_billed", "minutes", "duration", "Minutes", "Duration"],
    "calls": ["calls_count", "calls", "count", "Calls", "CallCount"],
    "profile": ["vendor", "Vendor", "profile", "Profile", "client", "Client"],
}


def _load_validation_config(root: Path) -> Dict:
    cfg_path = root / "config" / "validation_config.json"
    if not cfg_path.exists():
        return {}
    try:
        return json.loads(cfg_path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _float(v) -> float:
    try:
        return float(v)
    except Exception:
        return 0.0


def _resolve_column(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    cols = list(df.columns)
    by_lower = {str(c).lower(): c for c in cols}
    for c in candidates:
        if c in cols:
            return c
        lc = c.lower()
        if lc in by_lower:
            return by_lower[lc]
    return None


def _is_finite_series(series: pd.Series) -> bool:
    return bool(series.apply(lambda x: pd.isna(x) or math.isfinite(_float(x))).all())


def _per_profile_deltas(
    baseline: pd.DataFrame,
    tx: pd.DataFrame,
    b_profile: str,
    t_profile: str,
    b_cost: str,
    t_cost: str,
    b_minutes: str,
    t_minutes: str,
    b_calls: str,
) -> Dict[str, Dict[str, float]]:
    b = baseline.groupby(b_profile, dropna=False).agg(
        baseline_cost=(b_cost, "sum"),
        baseline_minutes=(b_minutes, "sum"),
        baseline_calls=(b_calls, "sum"),
    )
    t = tx.groupby(t_profile, dropna=False).agg(
        tx_cost=(t_cost, "sum"),
        tx_minutes=(t_minutes, "sum"),
    )
    t["tx_calls"] = tx.groupby(t_profile, dropna=False).size()

    merged = b.join(t, how="outer").fillna(0.0)
    out = {}
    for key, row in merged.iterrows():
        out[str(key)] = {
            "cost_delta": _float(row["baseline_cost"] - row["tx_cost"]),
            "minutes_delta": _float(row["baseline_minutes"] - row["tx_minutes"]),
            "calls_delta": _float(row["baseline_calls"] - row["tx_calls"]),
            "baseline_cost": _float(row["baseline_cost"]),
            "tx_cost": _float(row["tx_cost"]),
            "baseline_minutes": _float(row["baseline_minutes"]),
            "tx_minutes": _float(row["tx_minutes"]),
            "baseline_calls": _float(row["baseline_calls"]),
            "tx_calls": _float(row["tx_calls"]),
        }
    return out


def main():
    parser = argparse.ArgumentParser(
        description="Universal baseline validator for multi-profile outputs."
    )
    root = Path(__file__).resolve().parent
    parser.add_argument("--baseline", default=str(root / "baseline_v1_output.csv"))
    parser.add_argument("--transactions", default=str(root / "baseline_transactions.csv"))
    parser.add_argument("--output", default=str(root / "baseline_validation_report.json"))
    parser.add_argument("--tolerance", type=float, default=0.01)
    parser.add_argument("--profile-col", default="", help="Optional profile/vendor column to force.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail when utilization exists with zero/missing cost (globally or by profile).",
    )
    parser.add_argument(
        "--strict-allowlist",
        default="",
        help="Comma-separated profile names allowed to have unpriced utilization in strict mode.",
    )
    args = parser.parse_args()
    cfg = _load_validation_config(root)
    strict_cfg = cfg.get("strict", {}) if isinstance(cfg, dict) else {}
    strict_allowlist_cfg = strict_cfg.get("profile_allowlist", [])
    strict_allowlist_cli = [
        x.strip() for x in args.strict_allowlist.split(",") if x.strip()
    ]
    strict_allowlist = (
        strict_allowlist_cli
        if strict_allowlist_cli
        else ([x for x in strict_allowlist_cfg if isinstance(x, str)] if isinstance(strict_allowlist_cfg, list) else [])
    )
    strict_allowset_lower = {x.lower() for x in strict_allowlist}

    baseline_path = Path(args.baseline)
    transactions_path = Path(args.transactions)
    report_path = Path(args.output)

    result = {
        "status": "FAIL",
        "checks": {},
        "resolved_columns": {},
        "warnings": [],
        "summary": {},
        "profiles": {},
        "files": {
            "baseline": str(baseline_path.resolve()),
            "transactions": str(transactions_path.resolve()),
        },
        "strict_allowlist": strict_allowlist,
    }

    if not baseline_path.exists() or not transactions_path.exists():
        result["checks"]["files_exist"] = False
        report_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"Validation failed: required files missing. Report: {report_path}")
        return

    baseline = pd.read_csv(baseline_path)
    tx = pd.read_csv(transactions_path)

    b_cost = _resolve_column(baseline, BASELINE_CANDIDATES["cost"])
    b_minutes = _resolve_column(baseline, BASELINE_CANDIDATES["minutes"])
    b_calls = _resolve_column(baseline, BASELINE_CANDIDATES["calls"])
    b_cpm = _resolve_column(baseline, BASELINE_CANDIDATES["cpm"])
    b_profile = args.profile_col or _resolve_column(baseline, BASELINE_CANDIDATES["profile"])

    t_cost = _resolve_column(tx, TX_CANDIDATES["cost"])
    t_minutes = _resolve_column(tx, TX_CANDIDATES["minutes"])
    t_profile = args.profile_col or _resolve_column(tx, TX_CANDIDATES["profile"])

    result["resolved_columns"] = {
        "baseline_cost": b_cost,
        "baseline_minutes": b_minutes,
        "baseline_calls": b_calls,
        "baseline_cpm": b_cpm,
        "baseline_profile": b_profile,
        "tx_cost": t_cost,
        "tx_minutes": t_minutes,
        "tx_profile": t_profile,
    }

    result["checks"]["baseline_required_columns_ok"] = all([b_cost, b_minutes, b_calls])
    result["checks"]["transaction_required_columns_ok"] = all([t_cost, t_minutes])
    if not (result["checks"]["baseline_required_columns_ok"] and result["checks"]["transaction_required_columns_ok"]):
        report_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"Validation failed: missing required columns. Report: {report_path}")
        return

    baseline_cost = _float(baseline[b_cost].sum())
    baseline_minutes = _float(baseline[b_minutes].sum())
    baseline_calls = _float(baseline[b_calls].sum())

    tx_cost = _float(tx[t_cost].sum())
    tx_minutes = _float(tx[t_minutes].sum())
    tx_calls = float(len(tx))

    tol = args.tolerance
    result["checks"]["cost_totals_match"] = abs(baseline_cost - tx_cost) <= tol
    result["checks"]["minutes_totals_match"] = abs(baseline_minutes - tx_minutes) <= tol
    result["checks"]["calls_totals_match"] = abs(baseline_calls - tx_calls) <= 0.5
    result["checks"]["no_negative_cost"] = bool((baseline[b_cost] >= 0).all() and (tx[t_cost] >= 0).all())
    result["checks"]["no_negative_minutes"] = bool((baseline[b_minutes] >= 0).all() and (tx[t_minutes] >= 0).all())
    # Data completeness signal: records/minutes with no cost.
    unpriced_tx_mask = (tx[t_minutes] > 0) & (tx[t_cost] <= 0)
    result["summary"]["unpriced_transaction_rows"] = int(unpriced_tx_mask.sum())
    result["summary"]["unpriced_transaction_minutes"] = _float(tx.loc[unpriced_tx_mask, t_minutes].sum())
    unpriced_profiles = (
        sorted([str(x) for x in tx.loc[unpriced_tx_mask, t_profile].dropna().unique().tolist()])
        if t_profile
        else []
    )
    result["summary"]["unpriced_transaction_profiles"] = unpriced_profiles
    result["checks"]["has_no_unpriced_transactions"] = bool(unpriced_tx_mask.sum() == 0)
    if not result["checks"]["has_no_unpriced_transactions"]:
        result["warnings"].append(
            "Some transactions have minutes > 0 with zero/missing cost. "
            "Use --strict to fail on this condition."
        )

    if b_cpm:
        result["checks"]["cpm_finite"] = _is_finite_series(baseline[b_cpm])
        recomputed = baseline[b_cost].div(baseline[b_minutes]).replace([float("inf"), -float("inf")], 0.0).fillna(0.0)
        diff = (recomputed - baseline[b_cpm].fillna(0.0)).abs()
        result["checks"]["cpm_consistent"] = bool((diff <= 0.01).all())
    else:
        result["checks"]["cpm_finite"] = True
        result["checks"]["cpm_consistent"] = True

    # Per-profile checks (if profile columns exist in both files)
    if b_profile and t_profile:
        profile_deltas = _per_profile_deltas(
            baseline=baseline,
            tx=tx,
            b_profile=b_profile,
            t_profile=t_profile,
            b_cost=b_cost,
            t_cost=t_cost,
            b_minutes=b_minutes,
            t_minutes=t_minutes,
            b_calls=b_calls,
        )
        result["profiles"] = profile_deltas
        result["checks"]["profile_cost_match"] = all(abs(v["cost_delta"]) <= tol for v in profile_deltas.values())
        result["checks"]["profile_minutes_match"] = all(abs(v["minutes_delta"]) <= tol for v in profile_deltas.values())
        result["checks"]["profile_calls_match"] = all(abs(v["calls_delta"]) <= 0.5 for v in profile_deltas.values())
        unpriced_profiles = []
        for profile_name, vals in profile_deltas.items():
            if vals["tx_minutes"] > 0 and vals["tx_cost"] <= 0:
                unpriced_profiles.append(profile_name)
        result["summary"]["profiles_with_unpriced_utilization"] = sorted(unpriced_profiles)
        result["checks"]["profiles_have_priced_utilization"] = len(unpriced_profiles) == 0
    else:
        result["checks"]["profile_cost_match"] = True
        result["checks"]["profile_minutes_match"] = True
        result["checks"]["profile_calls_match"] = True
        result["checks"]["profiles_have_priced_utilization"] = result["checks"]["has_no_unpriced_transactions"]
        result["summary"]["profiles_with_unpriced_utilization"] = []

    # Strict mode gates on utilization completeness.
    unpriced_not_allowed = [
        p for p in result["summary"].get("profiles_with_unpriced_utilization", [])
        if p.lower() not in strict_allowset_lower
    ]
    result["summary"]["unpriced_profiles_not_in_allowlist"] = sorted(unpriced_not_allowed)
    result["checks"]["unpriced_profiles_allowed"] = len(unpriced_not_allowed) == 0
    if args.strict and strict_allowlist and result["summary"].get("profiles_with_unpriced_utilization"):
        result["warnings"].append(
            "Strict allowlist applied for unpriced utilization profiles: "
            + ", ".join(strict_allowlist)
        )

    if args.strict:
        result["checks"]["strict_no_unpriced_transactions"] = (
            result["checks"]["has_no_unpriced_transactions"] or result["checks"]["unpriced_profiles_allowed"]
        )
        result["checks"]["strict_profiles_priced"] = (
            result["checks"]["profiles_have_priced_utilization"] or result["checks"]["unpriced_profiles_allowed"]
        )
    else:
        result["checks"]["strict_no_unpriced_transactions"] = True
        result["checks"]["strict_profiles_priced"] = True

    strict_only_checks = {
        "has_no_unpriced_transactions",
        "profiles_have_priced_utilization",
    }
    failed = []
    for k, v in result["checks"].items():
        if v:
            continue
        if (not args.strict) and (k in strict_only_checks):
            continue
        failed.append(k)
    result["status"] = "PASS" if not failed else "FAIL"
    result["summary"] = {
        "failed_checks": failed,
        "baseline_rows": int(len(baseline)),
        "transaction_rows": int(len(tx)),
        "baseline_cost": baseline_cost,
        "transaction_cost": tx_cost,
        "baseline_minutes": baseline_minutes,
        "transaction_minutes": tx_minutes,
        "baseline_calls": baseline_calls,
        "transaction_calls": tx_calls,
        "profile_count": int(len(result["profiles"])) if result["profiles"] else 0,
        "strict_mode": bool(args.strict),
        "unpriced_transaction_rows": result["summary"].get("unpriced_transaction_rows", 0),
        "unpriced_transaction_minutes": result["summary"].get("unpriced_transaction_minutes", 0.0),
        "profiles_with_unpriced_utilization": result["summary"].get("profiles_with_unpriced_utilization", []),
        "unpriced_transaction_profiles": result["summary"].get("unpriced_transaction_profiles", []),
        "strict_allowlist": strict_allowlist,
        "unpriced_profiles_not_in_allowlist": result["summary"].get("unpriced_profiles_not_in_allowlist", []),
    }

    report_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"Validation {result['status']}. Report: {report_path}")
    if failed:
        print("Failed checks:")
        for name in failed:
            print(f" - {name}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
