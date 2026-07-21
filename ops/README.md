# AI Ops Control Plane

This directory is the execution-control boundary between research outputs and
any future broker-facing process.

Version 1 is shadow-only:

- research repos produce reports and frozen candidates;
- ops promotes only approved frozen candidates into immutable shadow contracts;
- ops records risk decisions, shadow order intents, and ledger events;
- no broker secrets, paper submit, or live submit path exists here yet.

The control-plane rule is:

```text
Research may generate candidates.
Ops may create contracts.
Execution may only act on contracts.
```

## Important Paths

```text
C:\AI\ops\contracts\crypto
C:\AI\ops\registry\ops_registry.sqlite
C:\AI\ops\runstate\kill_switch.json
C:\AI\ops\signals\shadow
C:\AI\ops\orders\intents
C:\AI\ops\reports
```

## Commands

Build or refresh shadow contracts from the latest crypto freeze pack:

```powershell
python C:\AI\ops\scripts\ops_control_plane.py promote-crypto-shadow
```

Run the shadow-only control-plane pass:

```powershell
python C:\AI\ops\scripts\ops_control_plane.py run-shadow
```

Write the current ops status report:

```powershell
python C:\AI\ops\scripts\ops_control_plane.py report
```

## Safety Defaults

- `paper_enabled` is false.
- `live_enabled` is false.
- `allow_live_submit` is false in generated contracts.
- broker adapter is `shadow_only`.
- order intents are no-submit shadow intents.
- `C:\AI\ops\runstate\DISABLE_ALL_TRADING` halts new shadow planning too.
