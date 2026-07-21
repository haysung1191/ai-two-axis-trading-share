# Policy Shadow Rollout

Required env vars:
- `POLICY_BUNDLE_PATH`
- `POLICY_MANIFEST_PATH`
- `TRACE_ENABLED`
- `POLICY_SHADOW_ENABLED`
- `POLICY_ACTIVE`
- `POLICY_SOFT_REJECT_ENABLED`
- `POLICY_SYMBOL_ALLOWLIST`
- `POLICY_MAX_SCORE_DELTA`

Safe initial values:
- `TRACE_ENABLED=1`
- `POLICY_SHADOW_ENABLED=1`
- `POLICY_ACTIVE=0`
- `POLICY_SOFT_REJECT_ENABLED=0`
- `POLICY_SYMBOL_ALLOWLIST=KRW-BTC`
- `POLICY_MAX_SCORE_DELTA=0.05`

VM bundle location:
- Place files at `/opt/crypto-scanner/policy/current/policy_bundle.json`
- Place files at `/opt/crypto-scanner/policy/current/manifest.json`

Confirm bundle loaded:
- Open the dashboard and check the `Policy Integration` section
- Or inspect `selection_trace` after one hourly run

Disable immediately:
- Set `POLICY_SHADOW_ENABLED=0`
- Set `POLICY_ACTIVE=0`
- Restart the service

Rollback:
- Restore the previous `/opt/crypto-scanner/policy/current` directory or disable flags
- Baseline scanner behavior continues when bundle is missing or invalid

SQLite table to inspect:
- `selection_trace`

Example commands:
```bash
python scripts/install_policy_bundle.py --bundle artifacts/<run_id>/publish/policy_bundle.json --manifest artifacts/<run_id>/publish/manifest.json --target-dir /opt/crypto-scanner/policy/current
sqlite3 state.db "SELECT ts, symbol, policy_bundle_id, policy_decision, final_decision FROM selection_trace ORDER BY id DESC LIMIT 10;"
```
