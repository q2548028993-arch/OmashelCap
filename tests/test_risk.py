from risk.circuit_breaker import CircuitBreaker
from risk.manager import RiskManager


def test_stake_is_1_percent_of_balance():
    rm = RiskManager(balance=1000.0)
    assert rm.compute_stake() == 10.0


def test_stake_capped_at_max():
    rm = RiskManager(balance=100_000.0)
    stake = rm.compute_stake()
    assert stake <= 10.0  # MAX_STAKE from settings


def test_stake_minimum_enforced():
    rm = RiskManager(balance=1.0)
    stake = rm.compute_stake()
    assert stake >= 0.35  # MIN_STAKE from settings


def test_circuit_breaker_trips_on_max_losses():
    cb = CircuitBreaker(opening_balance=1000.0)
    for _ in range(5):
        cb.on_loss(current_balance=990.0)
    assert cb.is_tripped


def test_circuit_breaker_resets_on_win():
    cb = CircuitBreaker(opening_balance=1000.0)
    cb.on_loss(current_balance=990.0)
    cb.on_loss(current_balance=980.0)
    cb.on_win()
    assert cb._consecutive_losses == 0


def test_daily_drawdown_trips_circuit():
    cb = CircuitBreaker(opening_balance=1000.0)
    cb.on_loss(current_balance=940.0)  # 6% drawdown > 5% limit
    assert cb.is_tripped
