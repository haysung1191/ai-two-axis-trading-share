# Policy Shadow Rollout Checklist

1. Copy `policy_bundle.json` and `manifest.json` to `/opt/crypto-scanner/policy/current/`
2. Set:
   - `TRACE_ENABLED=1`
   - `POLICY_SHADOW_ENABLED=1`
   - `POLICY_ACTIVE=0`
   - `POLICY_SOFT_REJECT_ENABLED=0`
3. Restart the service
4. Run:
   - `python scripts/policy_sanity_check.py`
5. Verify:
   - bundle status is `loaded`
   - dashboard `Policy Integration` section shows the current bundle
   - `selection_trace` rows appear after the next hourly run
6. Disable immediately if needed:
   - set `POLICY_SHADOW_ENABLED=0`
   - set `POLICY_ACTIVE=0`
   - restart service
7. If bundle is invalid:
   - check `logs` / service journal
   - run `python scripts/policy_sanity_check.py`
   - inspect `selection_trace` and bundle files under `/opt/crypto-scanner/policy/current/`
