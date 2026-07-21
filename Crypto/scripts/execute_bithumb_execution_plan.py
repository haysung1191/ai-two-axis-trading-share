from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data.bithumb_private_client import BithumbPrivateClient


def load_execution_plan(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def append_execution_log(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def load_execution_log(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def build_execution_log_record(
    execution_payload: dict[str, Any],
    *,
    plan_path: str | None,
    mode: str,
) -> dict[str, Any]:
    return {
        "logged_at_utc": _utc_now_iso(),
        "mode": mode,
        "plan_path": plan_path,
        "run_id": execution_payload.get("run_id"),
        "candle_close_utc": execution_payload.get("candle_close_utc"),
        "strategy_track": execution_payload.get("strategy_track"),
        "intent_count": execution_payload.get("intent_count"),
        "submitted_count": execution_payload.get("submitted_count"),
        "total_quote_krw": execution_payload.get("total_quote_krw"),
        "submitted_orders": execution_payload.get("submitted_orders", []),
        "funding_checks": execution_payload.get("funding_checks", []),
        "standard_check_order_reference": execution_payload.get("standard_check_order_reference", []),
    }


def build_planned_client_order_ids(plan_payload: dict[str, Any], *, client_order_prefix: str) -> list[str]:
    client_order_ids: list[str] = []
    for index, order_intent in enumerate(plan_payload.get("order_intents", []), start=1):
        symbol = str(order_intent.get("symbol", "asset")).lower()
        client_order_ids.append(f"{client_order_prefix}-{symbol}-{index:02d}")
    return client_order_ids


def assert_no_duplicate_submission(
    plan_payload: dict[str, Any],
    *,
    client_order_prefix: str,
    execution_log_path: Path,
) -> None:
    existing_rows = load_execution_log(execution_log_path)
    run_id = plan_payload.get("run_id")
    planned_client_order_ids = set(build_planned_client_order_ids(plan_payload, client_order_prefix=client_order_prefix))
    existing_client_order_ids: set[str] = set()

    for row in existing_rows:
        if not isinstance(row, dict):
            continue
        if row.get("mode") != "submit":
            continue
        if run_id is not None and row.get("run_id") == run_id:
            raise RuntimeError(f"duplicate live submission blocked for run_id={run_id}")
        submitted_orders = row.get("submitted_orders", [])
        if not isinstance(submitted_orders, list):
            continue
        for submitted_order in submitted_orders:
            if not isinstance(submitted_order, dict):
                continue
            client_order_id = submitted_order.get("client_order_id")
            if client_order_id not in (None, ""):
                existing_client_order_ids.add(str(client_order_id))

    duplicate_client_order_ids = sorted(planned_client_order_ids & existing_client_order_ids)
    if duplicate_client_order_ids:
        raise RuntimeError(
            "duplicate live submission blocked for client_order_id="
            + ",".join(duplicate_client_order_ids)
        )


def _fetch_existing_exchange_order_by_client_order_id(
    client: BithumbPrivateClient,
    *,
    client_order_id: str,
) -> dict[str, Any] | None:
    if not hasattr(client, "get_order"):
        return None
    try:
        return client.get_order(client_order_id=client_order_id)
    except httpx.HTTPStatusError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def assert_no_exchange_duplicate_submission(
    plan_payload: dict[str, Any],
    *,
    client: BithumbPrivateClient,
    client_order_prefix: str,
) -> None:
    for client_order_id in build_planned_client_order_ids(plan_payload, client_order_prefix=client_order_prefix):
        existing_order = _fetch_existing_exchange_order_by_client_order_id(client, client_order_id=client_order_id)
        if not isinstance(existing_order, dict):
            continue
        state = str(existing_order.get("state", "")).lower()
        if state in {"wait", "watch"}:
            raise RuntimeError(
                f"exchange duplicate submission blocked for client_order_id={client_order_id} state={state}"
            )


def build_signed_request_preview(
    plan_payload: dict[str, Any],
    *,
    access_key: str | None = None,
    secret_key: str | None = None,
    client_order_prefix: str = "codex",
) -> dict[str, Any]:
    client = BithumbPrivateClient(access_key=access_key, secret_key=secret_key)
    if not client.has_credentials():
        raise RuntimeError("Bithumb API credentials are missing")

    requests: list[dict[str, Any]] = []
    for index, order_intent in enumerate(plan_payload.get("order_intents", []), start=1):
        symbol = str(order_intent.get("symbol", "asset")).lower()
        client_order_id = f"{client_order_prefix}-{symbol}-{index:02d}"
        request = client.build_market_buy_request(order_intent, client_order_id=client_order_id)
        requests.append(
            {
                "symbol": order_intent.get("symbol"),
                "market": order_intent.get("market"),
                "client_order_id": client_order_id,
                "request": request,
            }
        )

    return {
        "run_id": plan_payload.get("run_id"),
        "candle_close_utc": plan_payload.get("candle_close_utc"),
        "strategy_track": plan_payload.get("strategy_track"),
        "intent_count": len(requests),
        "signed_requests": requests,
        "standard_check_order_reference": plan_payload.get("standard_check_order_reference", []),
    }


def _normalize_allowed_markets(allowed_markets: list[str] | None) -> set[str]:
    return {str(market).strip().upper() for market in (allowed_markets or []) if str(market).strip()}


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _extract_krw_balance_from_accounts(accounts_payload: Any) -> float | None:
    rows = accounts_payload
    if isinstance(accounts_payload, dict):
        for key in ("data", "accounts", "result"):
            candidate = accounts_payload.get(key)
            if isinstance(candidate, list):
                rows = candidate
                break
    if not isinstance(rows, list):
        return None

    for row in rows:
        if not isinstance(row, dict):
            continue
        currency = str(row.get("currency") or row.get("unit_currency") or "").upper()
        if currency != "KRW":
            continue
        for key in ("balance", "available_balance", "avail_krw", "available_krw"):
            amount = _safe_float(row.get(key))
            if amount is not None:
                return amount
    return None


def _extract_krw_available_from_order_chance(chance_payload: Any) -> float | None:
    if not isinstance(chance_payload, dict):
        return None

    candidate_accounts: list[dict[str, Any]] = []
    for key in ("bid_account", "ask_account", "account"):
        value = chance_payload.get(key)
        if isinstance(value, dict):
            candidate_accounts.append(value)

    for account in candidate_accounts:
        for key in ("balance", "available_balance", "avail_balance", "available_krw"):
            amount = _safe_float(account.get(key))
            if amount is not None:
                return amount
    return None


def _build_funding_snapshot(client: BithumbPrivateClient, market: str) -> dict[str, Any]:
    chance_payload = client.get_order_chance(market)
    available_krw = _extract_krw_available_from_order_chance(chance_payload)
    source = "order_chance"

    if available_krw is None:
        accounts_payload = client.get_accounts()
        available_krw = _extract_krw_balance_from_accounts(accounts_payload)
        source = "accounts"
    else:
        accounts_payload = None

    if available_krw is None:
        raise RuntimeError(f"could not determine available KRW balance for {market}")

    return {
        "market": market,
        "available_krw": available_krw,
        "balance_source": source,
        "order_chance": chance_payload,
        "accounts": accounts_payload,
    }


def _extract_order_identifier(order_response: Any) -> dict[str, str | None]:
    if not isinstance(order_response, dict):
        return {"uuid": None, "client_order_id": None}
    return {
        "uuid": next(
            (
                str(order_response.get(key))
                for key in ("uuid", "order_id", "id")
                if order_response.get(key) not in (None, "")
            ),
            None,
        ),
        "client_order_id": next(
            (
                str(order_response.get(key))
                for key in ("client_order_id", "identifier")
                if order_response.get(key) not in (None, "")
            ),
            None,
        ),
    }


def _fetch_order_status_snapshot(
    client: BithumbPrivateClient,
    *,
    created_order_response: Any,
    client_order_id: str,
) -> dict[str, Any] | None:
    identifiers = _extract_order_identifier(created_order_response)
    lookup_uuid = identifiers["uuid"]
    lookup_client_order_id = identifiers["client_order_id"] or client_order_id
    if not lookup_uuid and not lookup_client_order_id:
        return None

    try:
        order_status = client.get_order(uuid=lookup_uuid, client_order_id=lookup_client_order_id)
    except httpx.HTTPStatusError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise
    return {
        "lookup_uuid": lookup_uuid,
        "lookup_client_order_id": lookup_client_order_id,
        "order": order_status,
    }


def _extract_order_state(status_snapshot: dict[str, Any] | None) -> str | None:
    if not isinstance(status_snapshot, dict):
        return None
    order = status_snapshot.get("order")
    if not isinstance(order, dict):
        return None
    state = order.get("state")
    return str(state).lower() if state is not None else None


def _is_terminal_order_state(state: str | None) -> bool:
    return state in {"done", "cancel"}


def _monitor_order_status(
    client: BithumbPrivateClient,
    *,
    initial_status: dict[str, Any] | None,
    created_order_response: Any,
    client_order_id: str,
    poll_interval_seconds: float,
    timeout_seconds: float,
    cancel_on_timeout: bool,
) -> dict[str, Any]:
    history: list[dict[str, Any]] = []
    current_status = initial_status
    if current_status is not None:
        history.append(current_status)

    deadline = time.monotonic() + timeout_seconds
    timed_out = False
    cancel_response: dict[str, Any] | None = None

    while current_status is not None and not _is_terminal_order_state(_extract_order_state(current_status)):
        if time.monotonic() >= deadline:
            timed_out = True
            break
        if poll_interval_seconds > 0:
            time.sleep(poll_interval_seconds)
        next_status = _fetch_order_status_snapshot(
            client,
            created_order_response=created_order_response,
            client_order_id=client_order_id,
        )
        if next_status is None:
            break
        current_status = next_status
        history.append(next_status)

    if timed_out and cancel_on_timeout and current_status is not None:
        order_identifier = _extract_order_identifier(created_order_response)
        cancel_response = client.cancel_order(
            order_id=order_identifier["uuid"],
            client_order_id=order_identifier["client_order_id"] or client_order_id,
        )
        post_cancel_status = _fetch_order_status_snapshot(
            client,
            created_order_response=created_order_response,
            client_order_id=client_order_id,
        )
        if post_cancel_status is not None:
            current_status = post_cancel_status
            history.append(post_cancel_status)
        cancel_state = str(cancel_response.get("state", "")).lower() if isinstance(cancel_response, dict) else None
        if cancel_state == "cancel" and _extract_order_state(current_status) != "cancel":
            current_status = {
                "lookup_uuid": order_identifier["uuid"],
                "lookup_client_order_id": order_identifier["client_order_id"] or client_order_id,
                "order": cancel_response,
            }
            history.append(current_status)

    return {
        "final_status": current_status,
        "status_history": history,
        "timed_out": timed_out,
        "cancel_response": cancel_response,
    }


def submit_execution_plan(
    plan_payload: dict[str, Any],
    *,
    access_key: str | None = None,
    secret_key: str | None = None,
    client_order_prefix: str = "codex",
    allowed_markets: list[str] | None = None,
    max_total_quote_krw: float | None = None,
    status_poll_seconds: float = 0.0,
    status_timeout_seconds: float = 0.0,
    cancel_on_timeout: bool = False,
    enforce_exchange_duplicate_check: bool = True,
) -> dict[str, Any]:
    client = BithumbPrivateClient(access_key=access_key, secret_key=secret_key)
    if not client.has_credentials():
        raise RuntimeError("Bithumb API credentials are missing")

    normalized_allowed_markets = _normalize_allowed_markets(allowed_markets)
    if not normalized_allowed_markets:
        raise RuntimeError("allowed_markets is required for live submission")
    if max_total_quote_krw is None:
        raise RuntimeError("max_total_quote_krw is required for live submission")
    if enforce_exchange_duplicate_check:
        assert_no_exchange_duplicate_submission(
            plan_payload,
            client=client,
            client_order_prefix=client_order_prefix,
        )

    order_intents = list(plan_payload.get("order_intents", []))
    total_quote_krw = sum(float(intent.get("quote_amount_krw", 0.0) or 0.0) for intent in order_intents)
    if total_quote_krw > float(max_total_quote_krw):
        raise RuntimeError(
            f"execution plan total quote {total_quote_krw:.0f} KRW exceeds max_total_quote_krw {float(max_total_quote_krw):.0f} KRW"
        )

    submitted_orders: list[dict[str, Any]] = []
    funding_checks: list[dict[str, Any]] = []
    for index, order_intent in enumerate(order_intents, start=1):
        market = str(order_intent.get("market", "")).upper()
        if not market:
            raise RuntimeError(f"order intent #{index} is missing market")
        if normalized_allowed_markets and market not in normalized_allowed_markets:
            raise RuntimeError(f"market {market} is not in allowed_markets")

        quote_amount_krw = float(order_intent.get("quote_amount_krw", 0.0) or 0.0)
        if quote_amount_krw <= 0:
            raise RuntimeError(f"order intent #{index} has invalid quote_amount_krw={quote_amount_krw}")

        funding_snapshot = _build_funding_snapshot(client, market)
        if funding_snapshot["available_krw"] < quote_amount_krw:
            raise RuntimeError(
                f"insufficient KRW balance for {market}: available {funding_snapshot['available_krw']:.0f} < required {quote_amount_krw:.0f}"
            )

        symbol = str(order_intent.get("symbol", "asset")).lower()
        client_order_id = f"{client_order_prefix}-{symbol}-{index:02d}"
        order_body = client.build_market_buy_order_body(order_intent, client_order_id=client_order_id)
        response = client.create_order(order_body)
        order_status = _fetch_order_status_snapshot(
            client,
            created_order_response=response,
            client_order_id=client_order_id,
        )
        monitoring = {
            "final_status": order_status,
            "status_history": [order_status] if order_status is not None else [],
            "timed_out": False,
            "cancel_response": None,
        }
        if order_status is not None and status_timeout_seconds > 0:
            monitoring = _monitor_order_status(
                client,
                initial_status=order_status,
                created_order_response=response,
                client_order_id=client_order_id,
                poll_interval_seconds=max(float(status_poll_seconds), 0.0),
                timeout_seconds=float(status_timeout_seconds),
                cancel_on_timeout=bool(cancel_on_timeout),
            )
        funding_checks.append(
            {
                "market": market,
                "quote_amount_krw": quote_amount_krw,
                "available_krw": funding_snapshot["available_krw"],
                "balance_source": funding_snapshot["balance_source"],
            }
        )
        submitted_orders.append(
            {
                "symbol": order_intent.get("symbol"),
                "market": market,
                "client_order_id": client_order_id,
                "quote_amount_krw": quote_amount_krw,
                "response": response,
                "order_status": monitoring["final_status"],
                "status_history": monitoring["status_history"],
                "timed_out": monitoring["timed_out"],
                "cancel_response": monitoring["cancel_response"],
            }
        )

    return {
        "run_id": plan_payload.get("run_id"),
        "candle_close_utc": plan_payload.get("candle_close_utc"),
        "strategy_track": plan_payload.get("strategy_track"),
        "intent_count": len(submitted_orders),
        "submitted_count": len(submitted_orders),
        "total_quote_krw": total_quote_krw,
        "funding_checks": funding_checks,
        "submitted_orders": submitted_orders,
        "standard_check_order_reference": plan_payload.get("standard_check_order_reference", []),
    }


def render_text_preview(payload: dict[str, Any]) -> str:
    lines = [
        f"run_id: {payload.get('run_id', '-')}",
        f"candle_close_utc: {payload.get('candle_close_utc', '-')}",
        f"strategy_track: {payload.get('strategy_track', '-')}",
        f"intent_count: {payload.get('intent_count', 0)}",
        "",
        "signed_requests:",
    ]
    for row in payload.get("signed_requests", []):
        request = row.get("request", {})
        headers = request.get("headers", {})
        bearer = str(headers.get("Authorization", ""))
        bearer_preview = f"{bearer[:24]}..." if bearer else "-"
        lines.append(
            "  "
            + " | ".join(
                [
                    str(row.get("market", "-")),
                    f"client_order_id={row.get('client_order_id', '-')}",
                    f"method={request.get('method', '-')}",
                    f"path={request.get('path', '-')}",
                    f"auth={bearer_preview}",
                ]
            )
        )
    if not payload.get("signed_requests"):
        lines.append("  (no actionable signed requests)")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Build signed Bithumb order request previews from an execution plan JSON. "
            "Standard operating check order: practical -> research -> contract -> brief."
        )
    )
    parser.add_argument("--plan-json", required=True, help="Execution plan JSON path from build_bithumb_execution_plan.py")
    parser.add_argument("--access-key", default=None, help="Optional Bithumb access key override")
    parser.add_argument("--secret-key", default=None, help="Optional Bithumb secret key override")
    parser.add_argument("--client-order-prefix", default="codex", help="Client order id prefix")
    parser.add_argument("--submit", action="store_true", help="Actually submit live orders instead of building a signed preview")
    parser.add_argument("--allowed-market", action="append", default=None, help="Allowed market whitelist item, e.g. KRW-BTC")
    parser.add_argument(
        "--max-total-quote-krw",
        type=float,
        default=None,
        help="Reject execution if summed quote_amount_krw exceeds this cap",
    )
    parser.add_argument("--status-poll-seconds", type=float, default=0.0, help="Polling interval after submission for order status")
    parser.add_argument("--status-timeout-seconds", type=float, default=0.0, help="Max seconds to monitor order status after submission")
    parser.add_argument("--cancel-on-timeout", action="store_true", help="Cancel live order if status monitoring times out")
    parser.add_argument(
        "--execution-log",
        default="logs\\bithumb_live_execution_log.jsonl",
        help="JSONL path for appending execution records; pass empty string to disable",
    )
    parser.add_argument(
        "--allow-duplicate-submission",
        action="store_true",
        help="Bypass execution log duplicate guard for run_id and client_order_id",
    )
    parser.add_argument(
        "--skip-exchange-duplicate-check",
        action="store_true",
        help="Skip exchange-side client_order_id duplicate check before submission",
    )
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("--output", default=None, help="Optional signed preview output path")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    plan_payload = load_execution_plan(Path(args.plan_json))
    if args.submit:
        if args.execution_log and not args.allow_duplicate_submission:
            assert_no_duplicate_submission(
                plan_payload,
                client_order_prefix=str(args.client_order_prefix),
                execution_log_path=Path(args.execution_log),
            )
        preview = submit_execution_plan(
            plan_payload,
            access_key=args.access_key,
            secret_key=args.secret_key,
            client_order_prefix=str(args.client_order_prefix),
            allowed_markets=args.allowed_market,
            max_total_quote_krw=args.max_total_quote_krw,
            status_poll_seconds=args.status_poll_seconds,
            status_timeout_seconds=args.status_timeout_seconds,
            cancel_on_timeout=args.cancel_on_timeout,
            enforce_exchange_duplicate_check=not args.skip_exchange_duplicate_check,
        )
        if args.execution_log:
            append_execution_log(
                Path(args.execution_log),
                build_execution_log_record(
                    preview,
                    plan_path=str(Path(args.plan_json).resolve()),
                    mode="submit",
                ),
            )
    else:
        preview = build_signed_request_preview(
            plan_payload,
            access_key=args.access_key,
            secret_key=args.secret_key,
            client_order_prefix=str(args.client_order_prefix),
        )
        if args.execution_log:
            append_execution_log(
                Path(args.execution_log),
                build_execution_log_record(
                    preview,
                    plan_path=str(Path(args.plan_json).resolve()),
                    mode="preview",
                ),
            )

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(preview, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.format == "json":
        print(json.dumps(preview, ensure_ascii=False, indent=2))
    else:
        if args.submit:
            print(json.dumps(preview, ensure_ascii=False, indent=2))
        else:
            print(render_text_preview(preview))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
