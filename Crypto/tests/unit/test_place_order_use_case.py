import pytest

from app.domains.trading.repositories import InMemoryLedgerRepository
from app.domains.trading.schemas import PlaceOrderRequest
from app.domains.trading.use_cases import PlaceOrderUseCase
from app.infrastructure.orchestration.langgraph_workflow import SupervisorWorkflow


@pytest.mark.asyncio
async def test_place_order_records_event() -> None:
    repository = InMemoryLedgerRepository()
    use_case = PlaceOrderUseCase(repository=repository, workflow=SupervisorWorkflow())

    result = await use_case.execute(
        PlaceOrderRequest(symbol="BTC-KRW", side="buy", quantity=1.25)
    )

    assert result.status == "accepted"
    assert result.symbol == "BTC-KRW"
    assert len(repository.events) == 1
    assert repository.events[0]["event_type"] == "ORDER_PLACED"
