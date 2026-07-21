from src.paper.exit_rules import evaluate_long_exit


def test_sl_first_when_both_hit():
    dec = evaluate_long_exit(
        candle_o=100,
        candle_h=130,
        candle_l=70,
        candle_c=120,
        stop_price=80,
        tp_price=120,
        time_exit_now=False,
    )
    assert dec.should_exit is True
    assert dec.reason in ("SL", "SL_GAP")


def test_gap_down_sl_at_open():
    dec = evaluate_long_exit(
        candle_o=75,
        candle_h=90,
        candle_l=70,
        candle_c=85,
        stop_price=80,
        tp_price=120,
        time_exit_now=False,
    )
    assert dec.should_exit is True
    assert dec.reason == "SL_GAP"
    assert dec.exit_price_pre_slip == 75


def test_tp_gap_fills_at_tp():
    dec = evaluate_long_exit(
        candle_o=150,
        candle_h=160,
        candle_l=140,
        candle_c=155,
        stop_price=100,
        tp_price=120,
        time_exit_now=False,
    )
    assert dec.should_exit is True
    assert dec.reason == "TP_GAP"
    assert dec.exit_price_pre_slip == 120


def test_time_exit_at_close_only_if_no_hits():
    dec = evaluate_long_exit(
        candle_o=100,
        candle_h=110,
        candle_l=95,
        candle_c=105,
        stop_price=90,
        tp_price=120,
        time_exit_now=True,
    )
    assert dec.should_exit is True
    assert dec.reason == "TIME"
    assert dec.exit_price_pre_slip == 105

