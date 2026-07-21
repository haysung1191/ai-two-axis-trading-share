import pytest
from pydantic import ValidationError

from app.domains.governance.contracts import DesignSpec, Spec


def test_contract_validation_rejects_invalid_spec() -> None:
    with pytest.raises(ValidationError):
        Spec(run_goal="x", context="ok", requirements=[])


def test_design_spec_contract_validation_accepts_valid_payload() -> None:
    payload = {
        "run_id": "run-1",
        "architecture_summary": "summary",
        "components": ["PO Agent"],
        "constraints": ["must log all steps"],
    }
    contract = DesignSpec.model_validate(payload)
    assert contract.run_id == "run-1"

