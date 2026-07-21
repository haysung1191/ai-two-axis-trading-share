from __future__ import annotations

import sqlite3

from src.paper.exit_rules import evaluate_long_exit


def apply_fee(notional: float, fee_rate: float) -> float:
    return notional * fee_rate


def maybe_fill_scheduled_orders(
    conn: sqlite3.Connection,
    run_id: str,
    candle_close_ts_ms: int,
    symbol_to_entry_open: dict[str, float],
    slippage_rate: float,
) -> int:
    """
    Fill SCHEDULED orders whose entry_ts_ms == candle_close_ts_ms (entry at this candle open).
    Entry fill: entry_open * (1 + slippage_rate).
    Creates a position for each filled order.
    """
    cur = conn.execute(
        """
        SELECT id, symbol, qty, stop_dist, tp_dist, time_exit_ts_ms
        FROM paper_orders
        WHERE status='SCHEDULED' AND entry_ts_ms=?
        ORDER BY id
        """,
        (candle_close_ts_ms,),
    )
    filled = 0
    for r in cur.fetchall():
        sym = r["symbol"]
        if sym not in symbol_to_entry_open:
            continue
        entry_open = float(symbol_to_entry_open[sym])
        entry_fill = entry_open * (1.0 + slippage_rate)
        stop_price = entry_fill - float(r["stop_dist"])
        tp_price = entry_fill + float(r["tp_dist"])

        conn.execute(
            """
            UPDATE paper_orders
            SET entry_open=?, entry_fill=?, stop_price=?, tp_price=?, status='OPENED'
            WHERE id=? AND status='SCHEDULED'
            """,
            (entry_open, entry_fill, stop_price, tp_price, int(r["id"])),
        )

        conn.execute(
            """
            INSERT OR IGNORE INTO positions(symbol, entry_order_id, entry_run_id, entry_ts_ms, entry_fill, qty, stop_price, tp_price, time_exit_ts_ms)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                sym,
                int(r["id"]),
                run_id,
                int(candle_close_ts_ms),
                entry_fill,
                float(r["qty"]),
                stop_price,
                tp_price,
                int(r["time_exit_ts_ms"]),
            ),
        )
        filled += 1
    return filled


def maybe_exit_positions(
    conn: sqlite3.Connection,
    run_id: str,
    candle_close_ts_ms: int,
    symbol_to_ohlc: dict[str, tuple[float, float, float, float]],
    slippage_rate: float,
    fee_rate: float,
    cooldown_ms: int,
) -> int:
    """
    Evaluate exits for positions based on the just-closed candle.
    Exit fill: exit_pre_slip * (1 - slippage_rate).
    Fees: apply per side on notional.
    """
    cur = conn.execute(
        "SELECT symbol, entry_order_id, entry_fill, qty, stop_price, tp_price, time_exit_ts_ms FROM positions ORDER BY opened_at"
    )
    exited = 0
    for r in cur.fetchall():
        sym = r["symbol"]
        if sym not in symbol_to_ohlc:
            continue
        o, h, l, c = symbol_to_ohlc[sym]
        time_exit_now = int(r["time_exit_ts_ms"]) == int(candle_close_ts_ms)
        dec = evaluate_long_exit(o, h, l, c, float(r["stop_price"]), float(r["tp_price"]), time_exit_now)
        if not dec.should_exit:
            continue
        exit_pre = float(dec.exit_price_pre_slip)
        exit_fill = exit_pre * (1.0 - slippage_rate)

        qty = float(r["qty"])
        entry_fill = float(r["entry_fill"])
        entry_notional = qty * entry_fill
        exit_notional = qty * exit_fill
        fees = apply_fee(entry_notional, fee_rate) + apply_fee(exit_notional, fee_rate)
        pnl = (exit_notional - entry_notional) - fees
        pnl_pct = 0.0 if entry_notional == 0 else pnl / entry_notional

        mae = min(0.0, (l - entry_fill) * qty)
        mfe = max(0.0, (h - entry_fill) * qty)

        conn.execute(
            """
            INSERT OR IGNORE INTO trades(symbol, entry_order_id, exit_run_id, exit_ts_ms, exit_fill, qty, pnl_krw, pnl_pct, mae, mfe, exit_reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                sym,
                int(r["entry_order_id"]),
                run_id,
                int(candle_close_ts_ms),
                exit_fill,
                qty,
                pnl,
                pnl_pct,
                mae,
                mfe,
                str(dec.reason),
            ),
        )

        conn.execute("DELETE FROM positions WHERE symbol=?", (sym,))

        # Per-symbol cooldown after exit.
        cooldown_until = int(candle_close_ts_ms) + int(cooldown_ms)
        conn.execute(
            """
            INSERT INTO symbol_state(symbol, cooldown_until_ts_ms, last_exit_ts_ms, updated_at)
            VALUES (?, ?, ?, datetime('now'))
            ON CONFLICT(symbol) DO UPDATE SET
              cooldown_until_ts_ms=excluded.cooldown_until_ts_ms,
              last_exit_ts_ms=excluded.last_exit_ts_ms,
              updated_at=datetime('now')
            """,
            (sym, cooldown_until, int(candle_close_ts_ms)),
        )
        exited += 1
    return exited
