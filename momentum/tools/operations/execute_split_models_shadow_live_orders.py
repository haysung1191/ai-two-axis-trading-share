from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pandas as pd

import config
from kis_api import KISApi


ROOT = REPO_ROOT
SHADOW_DIR = ROOT / "output" / "split_models_shadow"
RUNTIME_STATUS_PATH = SHADOW_DIR / "shadow_operator_runtime_status.json"
LIVE_APPROVAL_PREFLIGHT_PATH = Path(r"C:\AI\overnight_runs\live_approval_preflight_latest.json")

KR_SYMBOL_ALIASES = {
    "0000J0": "006380",
    "0000Z0": "456070",
}

US_OVRS_EXCHANGE_BY_SYMBOL = {
    "CAT": "NYSE",
    "COP": "NYSE",
    "DOW": "NYSE",
    "FDX": "NYSE",
    "GEV": "NYSE",
    "GILD": "NASD",
    "JNJ": "NYSE",
    "LMT": "NYSE",
    "XLE": "AMEX",
    "XOM": "NYSE",
}

US_PRICE_EXCHANGE_BY_OVRS = {
    "NASD": "NAS",
    "NYSE": "NYS",
    "AMEX": "AMS",
}


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_orders(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    if "DeltaNotional" in frame.columns:
        frame["DeltaNotional"] = pd.to_numeric(frame["DeltaNotional"], errors="coerce")
    else:
        frame["DeltaNotional"] = pd.NA
    frame = frame[frame["ExecutionSide"].isin(["BUY", "SELL"])].copy()
    return frame.reset_index(drop=True)


def _load_existing_plan(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    if "Status" not in frame.columns:
        raise SystemExit("submit_existing_plan_requires_status_column")
    return frame.reset_index(drop=True)


def _load_initial_book(path: Path, total_capital: float) -> pd.DataFrame:
    frame = pd.read_csv(path)
    frame["TargetWeight"] = pd.to_numeric(frame["TargetWeight"], errors="coerce").fillna(0.0)
    frame = frame[frame["TargetWeight"] > 0].copy().reset_index(drop=True)
    frame["ExecutionSide"] = "BUY"
    frame["DeltaNotional"] = frame["TargetWeight"] * float(total_capital)
    return frame[["Market", "AssetType", "Symbol", "Name", "Sector", "ExecutionSide", "DeltaNotional"]]


def _is_valid_kr_symbol(symbol: str) -> bool:
    return isinstance(symbol, str) and len(symbol) == 6 and symbol.isdigit()


def _resolve_kr_symbol(symbol: str, overrides: dict[str, str]) -> str | None:
    resolved = overrides.get(symbol) or KR_SYMBOL_ALIASES.get(symbol) or symbol
    return resolved if _is_valid_kr_symbol(resolved) else None


def _resolve_us_exchange(symbol: str, overrides: dict[str, str]) -> str | None:
    exchange = overrides.get(symbol) or US_OVRS_EXCHANGE_BY_SYMBOL.get(symbol)
    if exchange in US_PRICE_EXCHANGE_BY_OVRS:
        return exchange
    return None


def _price_order_row(
    row: pd.Series,
    api: KISApi,
    overrides: dict[str, str],
    usd_krw_rate: float | None,
) -> tuple[dict[str, Any], float | None]:
    market = str(row["Market"])
    symbol = str(row["Symbol"])
    context: dict[str, Any] = {
        "Market": market,
        "Symbol": symbol,
        "ResolvedSymbol": symbol,
        "ResolvedExchange": "",
        "ResolvedPrice": pd.NA,
        "FXRate": pd.NA,
        "OneShareCostKRW": pd.NA,
    }

    if market == "KR":
        resolved_symbol = _resolve_kr_symbol(symbol, overrides)
        if resolved_symbol is None:
            raise ValueError("invalid_kr_symbol")
        quote = api.get_domestic_quote(resolved_symbol)
        context["ResolvedSymbol"] = resolved_symbol
        context["ResolvedExchange"] = "KRX"
        context["ResolvedPrice"] = float(quote["price"])
        context["OneShareCostKRW"] = float(quote["price"])
        return context, usd_krw_rate

    if market == "US":
        ovrs_exchange = _resolve_us_exchange(symbol, overrides)
        if ovrs_exchange is None:
            raise ValueError("missing_us_exchange_mapping")
        price_exchange = US_PRICE_EXCHANGE_BY_OVRS[ovrs_exchange]
        quote = api.get_overseas_quote(price_exchange, symbol)
        if usd_krw_rate is None:
            usd_krw_rate = float(api.get_usd_krw_rate())
        context["ResolvedExchange"] = ovrs_exchange
        context["ResolvedPrice"] = float(quote["price"])
        context["FXRate"] = usd_krw_rate
        context["OneShareCostKRW"] = float(quote["price"]) * usd_krw_rate
        return context, usd_krw_rate

    raise ValueError(f"unsupported_market:{market}")


def _select_adaptive_initial_book(
    book: pd.DataFrame,
    api: KISApi,
    overrides: dict[str, str],
    total_capital: float,
) -> tuple[pd.DataFrame, dict[str, object]]:
    priced_rows: list[dict[str, object]] = []
    usd_krw_rate: float | None = None

    working = book.copy()
    for column in ("MomentumScore", "FlowScore", "MAD63"):
        if column in working.columns:
            working[column] = pd.to_numeric(working[column], errors="coerce").fillna(0.0)
        else:
            working[column] = 0.0

    for _, row in working.iterrows():
        item = row.to_dict()
        try:
            pricing, usd_krw_rate = _price_order_row(row, api, overrides, usd_krw_rate)
            item.update(pricing)
            item["Status"] = "READY"
            item["Reason"] = ""
        except Exception as exc:  # noqa: BLE001
            item["Status"] = "BLOCKED"
            item["Reason"] = str(exc)
        priced_rows.append(item)

    priced = pd.DataFrame(priced_rows)
    ready = priced[priced["Status"] == "READY"].copy()
    blocked = priced[priced["Status"] == "BLOCKED"].copy()

    sort_columns = ["TargetWeight", "MomentumScore", "FlowScore", "MAD63"]
    ready = ready.sort_values(sort_columns, ascending=[False, False, False, False], kind="stable").reset_index(drop=True)

    remaining_capital = float(total_capital)
    selected_rows: list[dict[str, object]] = []
    unselected_rows: list[dict[str, object]] = []

    for _, row in ready.iterrows():
        one_share_cost = float(row["OneShareCostKRW"])
        if one_share_cost <= remaining_capital:
            selected_rows.append(row.to_dict())
            remaining_capital -= one_share_cost
        else:
            item = row.to_dict()
            item["Status"] = "UNSELECTED"
            item["Reason"] = "insufficient_capital_for_first_share"
            unselected_rows.append(item)

    selected = pd.DataFrame(selected_rows)
    if selected.empty:
        selected_orders = pd.DataFrame(
            columns=["Market", "AssetType", "Symbol", "Name", "Sector", "ExecutionSide", "DeltaNotional"]
        )
        summary = {
            "adaptive_selection_enabled": True,
            "adaptive_ready_count": int(len(ready)),
            "adaptive_blocked_count": int(len(blocked)),
            "adaptive_selected_count": 0,
            "adaptive_unselected_count": int(len(unselected_rows)),
            "adaptive_selected_symbols": [],
            "adaptive_min_first_share_bundle_krw": None,
            "adaptive_remaining_capital_after_seed_krw": float(total_capital),
            "adaptive_blocked_reasons": sorted({reason for reason in blocked["Reason"].fillna("").tolist() if reason}),
            "adaptive_unselected_symbols": [str(item["Symbol"]) for item in unselected_rows],
        }
        return selected_orders, summary

    selected_weight_sum = float(selected["TargetWeight"].sum())
    selected["SelectedWeight"] = selected["TargetWeight"] / selected_weight_sum
    selected["ExecutionSide"] = "BUY"
    selected["DeltaNotional"] = selected["SelectedWeight"] * float(total_capital)

    selected_orders = selected[["Market", "AssetType", "Symbol", "Name", "Sector", "ExecutionSide", "DeltaNotional"]].copy()
    selected_orders["SelectedWeight"] = selected["SelectedWeight"]
    selected_orders["OriginalTargetWeight"] = selected["TargetWeight"]

    summary = {
        "adaptive_selection_enabled": True,
        "adaptive_ready_count": int(len(ready)),
        "adaptive_blocked_count": int(len(blocked)),
        "adaptive_selected_count": int(len(selected)),
        "adaptive_unselected_count": int(len(unselected_rows)),
        "adaptive_selected_symbols": selected["Symbol"].tolist(),
        "adaptive_min_first_share_bundle_krw": float(selected["OneShareCostKRW"].sum()),
        "adaptive_remaining_capital_after_seed_krw": float(remaining_capital),
        "adaptive_blocked_reasons": sorted({reason for reason in blocked["Reason"].fillna("").tolist() if reason}),
        "adaptive_unselected_symbols": [str(item["Symbol"]) for item in unselected_rows],
    }
    return selected_orders.reset_index(drop=True), summary


def _build_plan(orders: pd.DataFrame, api: KISApi, overrides: dict[str, str]) -> tuple[pd.DataFrame, dict[str, object]]:
    usd_krw_rate: float | None = None
    rows: list[dict[str, object]] = []

    for _, row in orders.iterrows():
        market = str(row["Market"])
        symbol = str(row["Symbol"])
        side = str(row["ExecutionSide"])
        delta_notional = abs(float(row["DeltaNotional"])) if pd.notna(row["DeltaNotional"]) else None

        plan_row = {
            "Market": market,
            "Symbol": symbol,
            "ResolvedSymbol": symbol,
            "ExecutionSide": side,
            "Name": row.get("Name"),
            "DeltaNotional": delta_notional,
            "Status": "PLANNED",
            "Reason": "",
            "ResolvedExchange": "",
            "ResolvedPrice": pd.NA,
            "FXRate": pd.NA,
            "Quantity": pd.NA,
            "EstimatedOrderNotionalKRW": pd.NA,
        }

        try:
            if delta_notional is None or delta_notional <= 0:
                raise ValueError("missing_delta_notional")
            pricing, usd_krw_rate = _price_order_row(row, api, overrides, usd_krw_rate)
            quantity = int(math.floor(delta_notional / float(pricing["OneShareCostKRW"])))
            estimated_krw = quantity * float(pricing["OneShareCostKRW"])
            plan_row["ResolvedSymbol"] = pricing["ResolvedSymbol"]
            plan_row["ResolvedExchange"] = pricing["ResolvedExchange"]
            plan_row["ResolvedPrice"] = pricing["ResolvedPrice"]
            plan_row["FXRate"] = pricing["FXRate"]
            plan_row["Quantity"] = quantity
            plan_row["EstimatedOrderNotionalKRW"] = estimated_krw

            if int(plan_row["Quantity"]) <= 0:
                raise ValueError("zero_quantity_after_rounding")
        except Exception as exc:  # noqa: BLE001
            plan_row["Status"] = "SKIPPED"
            plan_row["Reason"] = str(exc)

        rows.append(plan_row)

    plan = pd.DataFrame(rows)
    summary = {
        "kis_env": config.ENV,
        "orders_considered": int(len(plan)),
        "planned_count": int((plan["Status"] == "PLANNED").sum()),
        "skipped_count": int((plan["Status"] == "SKIPPED").sum()),
        "usd_krw_rate": usd_krw_rate,
        "blocked_reasons": sorted({reason for reason in plan["Reason"].fillna("").tolist() if reason}),
    }
    return plan, summary


def _live_approval_caps() -> dict[str, float | str]:
    if not LIVE_APPROVAL_PREFLIGHT_PATH.exists():
        raise SystemExit("live_submit_blocked: missing live_approval_preflight_latest.json")
    approval = _load_json(LIVE_APPROVAL_PREFLIGHT_PATH)
    if approval.get("status") not in {"ready_for_human_live_review", "APPROVED"}:
        raise SystemExit(f"live_submit_blocked: live_approval_status={approval.get('status')}")
    blockers = approval.get("blockers")
    if isinstance(blockers, list) and blockers:
        raise SystemExit(f"live_submit_blocked: live_approval_blockers={','.join(str(item) for item in blockers)}")

    caps = approval.get("caps") if isinstance(approval.get("caps"), dict) else {}
    if not caps:
        caps = approval.get("approval_caps") if isinstance(approval.get("approval_caps"), dict) else {}
    profile = str(caps.get("profile") or approval.get("profile") or "")
    if profile != "small_account_growth_paper":
        raise SystemExit(f"live_submit_blocked: unsupported_live_profile={profile or 'missing'}")

    stock_cap = _as_float(caps.get("stock_cap_krw"), _as_float(caps.get("max_krw")))
    max_order = _as_float(caps.get("max_order_krw"))
    if stock_cap <= 0:
        raise SystemExit("live_submit_blocked: missing_positive_stock_cap_krw")
    if max_order <= 0:
        raise SystemExit("live_submit_blocked: missing_positive_max_order_krw")
    return {
        "profile": profile,
        "stock_cap_krw": stock_cap,
        "max_order_krw": max_order,
    }


def _enforce_live_approval_caps(plan: pd.DataFrame) -> None:
    caps = _live_approval_caps()
    planned = plan[plan["Status"] == "PLANNED"].copy()
    planned["EstimatedOrderNotionalKRW"] = pd.to_numeric(
        planned["EstimatedOrderNotionalKRW"],
        errors="coerce",
    ).fillna(0.0)
    total_notional = float(planned["EstimatedOrderNotionalKRW"].sum())
    max_order = float(caps["max_order_krw"])
    stock_cap = float(caps["stock_cap_krw"])

    failures: list[str] = []
    if total_notional <= 0:
        failures.append("planned_notional_zero")
    if total_notional > stock_cap:
        failures.append(f"planned_notional_exceeds_stock_cap:{total_notional:.2f}>{stock_cap:.2f}")
    oversized = planned[planned["EstimatedOrderNotionalKRW"] > max_order]
    if not oversized.empty:
        items = [
            f"{row.Symbol}:{float(row.EstimatedOrderNotionalKRW):.2f}>{max_order:.2f}"
            for row in oversized.itertuples()
        ]
        failures.append("planned_order_exceeds_max_order:" + "|".join(items))
    if failures:
        raise SystemExit(f"live_submit_blocked: {', '.join(failures)}")


def _enforce_submit_gate(plan: pd.DataFrame) -> None:
    if not RUNTIME_STATUS_PATH.exists():
        raise SystemExit("live_submit_blocked: missing shadow_operator_runtime_status.json")
    runtime_status = _load_json(RUNTIME_STATUS_PATH)
    failures: list[str] = []
    if runtime_status.get("live_readiness") != "GO":
        failures.append(f"live_readiness={runtime_status.get('live_readiness')}")
    if runtime_status.get("operator_gate_verdict") != "PASS":
        failures.append(f"operator_gate_verdict={runtime_status.get('operator_gate_verdict')}")
    if config.ENV != "PROD":
        failures.append(f"KIS_ENV={config.ENV}")
    skipped = plan[plan["Status"] == "SKIPPED"]
    if not skipped.empty:
        failures.append("plan_contains_skipped_rows")
    if failures:
        raise SystemExit(f"live_submit_blocked: {', '.join(failures)}")
    _enforce_live_approval_caps(plan)


def _submit_orders(plan: pd.DataFrame, api: KISApi) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for _, row in plan.iterrows():
        item = row.to_dict()
        if row["Status"] != "PLANNED":
            item["SubmitStatus"] = "SKIPPED"
            item["SubmitReason"] = row["Reason"]
            rows.append(item)
            continue

        symbol = str(row["Symbol"])
        resolved_symbol = str(row["ResolvedSymbol"])
        side = str(row["ExecutionSide"])
        quantity = int(row["Quantity"])
        market = str(row["Market"])
        try:
            if market == "KR":
                response = api.place_domestic_cash_order(resolved_symbol, side, quantity, order_type="market")
            else:
                response = api.place_overseas_order(
                    resolved_symbol,
                    side,
                    quantity,
                    ovrs_excg_cd=str(row["ResolvedExchange"]),
                    price=float(row["ResolvedPrice"]),
                )
            output = response.get("output", {}) or {}
            item["SubmitStatus"] = "SUBMITTED"
            item["SubmitReason"] = ""
            item["OrderNo"] = output.get("ODNO", "")
            item["KisRtCd"] = response.get("rt_cd", "")
            item["KisMsgCd"] = response.get("msg_cd", "")
            item["KisMsg1"] = response.get("msg1", "")
        except Exception as exc:  # noqa: BLE001
            item["SubmitStatus"] = "FAILED"
            item["SubmitReason"] = str(exc)
        rows.append(item)
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--orders-path", default=str(SHADOW_DIR / "shadow_rebalance_orders.csv"))
    parser.add_argument("--initial-book-path", default="")
    parser.add_argument("--submit-existing-plan-path", default="")
    parser.add_argument("--adaptive-initial-entry", action="store_true")
    parser.add_argument("--plan-path", default=str(SHADOW_DIR / "shadow_live_execution_plan.csv"))
    parser.add_argument("--summary-path", default=str(SHADOW_DIR / "shadow_live_execution_summary.json"))
    parser.add_argument("--submit-results-path", default=str(SHADOW_DIR / "shadow_live_submit_results.csv"))
    parser.add_argument("--preflight-path", default="")
    parser.add_argument("--exchange-overrides-json", default="")
    parser.add_argument("--total-capital", type=float, default=None)
    parser.add_argument("--submit-live", action="store_true")
    args = parser.parse_args()

    overrides = json.loads(args.exchange_overrides_json) if args.exchange_overrides_json else {}
    api = KISApi()
    if args.submit_existing_plan_path:
        if not args.submit_live:
            raise SystemExit("submit_existing_plan_requires_submit_live")
        plan = _load_existing_plan(Path(args.submit_existing_plan_path))
        adaptive_summary = {"adaptive_selection_enabled": False}
        summary = {
            "kis_env": config.ENV,
            "orders_considered": int(len(plan)),
            "planned_count": int((plan["Status"] == "PLANNED").sum()),
            "skipped_count": int((plan["Status"] == "SKIPPED").sum()),
            "usd_krw_rate": None,
            "blocked_reasons": sorted({reason for reason in plan["Reason"].fillna("").tolist() if reason}),
            "plan_mode": "existing_plan_submit",
        }
    elif args.initial_book_path:
        if args.total_capital is None or args.total_capital <= 0:
            raise SystemExit("initial_entry_requires_positive_total_capital")
        initial_book = pd.read_csv(Path(args.initial_book_path))
        if args.adaptive_initial_entry:
            orders, adaptive_summary = _select_adaptive_initial_book(initial_book, api, overrides, args.total_capital)
        else:
            orders = _load_initial_book(Path(args.initial_book_path), args.total_capital)
            adaptive_summary = {"adaptive_selection_enabled": False}
    else:
        orders = _load_orders(Path(args.orders_path))
        adaptive_summary = {"adaptive_selection_enabled": False}
        plan, summary = _build_plan(orders, api, overrides)
        summary["plan_mode"] = "rebalance"

    if not args.submit_existing_plan_path:
        plan, summary = _build_plan(orders, api, overrides)
        summary["plan_mode"] = "initial_entry" if args.initial_book_path else "rebalance"
        if args.total_capital is not None:
            summary["total_capital"] = float(args.total_capital)
    summary.update(adaptive_summary)

    plan_path = Path(args.plan_path)
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    if not args.submit_existing_plan_path:
        plan.to_csv(plan_path, index=False, encoding="utf-8-sig")

    submit_results_path = Path(args.submit_results_path)
    if args.submit_live:
        _enforce_submit_gate(plan)
        submit_results = _submit_orders(plan, api)
        submit_results.to_csv(submit_results_path, index=False, encoding="utf-8-sig")
        summary["submit_mode"] = "live"
        summary["submitted_count"] = int((submit_results["SubmitStatus"] == "SUBMITTED").sum())
        summary["failed_count"] = int((submit_results["SubmitStatus"] == "FAILED").sum())
        if args.submit_existing_plan_path:
            existing_plan_path = Path(args.submit_existing_plan_path)
            summary["submitted_plan_path"] = str(existing_plan_path)
            summary["submitted_plan_sha256"] = _sha256_file(existing_plan_path)
        if args.preflight_path:
            preflight_path = Path(args.preflight_path)
            summary["preflight_path"] = str(preflight_path)
            if preflight_path.exists():
                summary["preflight_sha256"] = _sha256_file(preflight_path)
    else:
        summary["submit_mode"] = "dry_run"
        summary["submitted_count"] = 0
        summary["failed_count"] = 0

    Path(args.summary_path).write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"plan_path={plan_path}")
    print(f"planned_count={summary['planned_count']}")
    print(f"skipped_count={summary['skipped_count']}")
    print(f"submit_mode={summary['submit_mode']}")
    if args.submit_live:
        print(f"submit_results_path={submit_results_path}")


if __name__ == "__main__":
    main()
