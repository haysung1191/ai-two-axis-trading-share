from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass(frozen=True)
class AppConfig:
    db_path: str
    log_level: str
    config_path: str
    app_env: str

    exchange: dict
    strategy: dict
    scanner: dict
    email: dict
    policy: dict = field(default_factory=dict)

    smtp: dict = field(default_factory=dict)


def load_config() -> AppConfig:
    app_env = os.getenv("APP_ENV", "dev")
    db_path = os.getenv("DB_PATH", "state.db")
    config_path = os.getenv("CONFIG_PATH", "config/config.yaml")
    log_level = os.getenv("LOG_LEVEL", "INFO")

    cfg_file = Path(config_path)
    with cfg_file.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}

    smtp = {
        "host": os.getenv("SMTP_HOST", ""),
        "port": int(os.getenv("SMTP_PORT", "587")),
        "user": os.getenv("SMTP_USER", ""),
        "pass": os.getenv("SMTP_PASS", ""),
        "from": os.getenv("SMTP_FROM", ""),
        "to": os.getenv("SMTP_TO", ""),
        "tls": os.getenv("SMTP_TLS", "1") not in ("0", "false", "False", ""),
    }

    return AppConfig(
        db_path=db_path,
        log_level=log_level,
        config_path=str(cfg_file),
        app_env=app_env,
        exchange=cfg.get("exchange", {}),
        strategy=cfg.get("strategy", {}),
        scanner=cfg.get("scanner", {}),
        email=cfg.get("email", {}),
        policy=cfg.get("policy", {}),
        smtp=smtp,
    )
