# Write Tests for Bot Orchestrator

**Labels:** `priority: critical`, `type: testing`, `mvp`, `tdd`, `bot`

## Description
Write tests for main bot controller before implementation.

## Tasks
- [ ] Create `tests/unit/test_bot.py`:
  - [ ] Test bot initialization with config
  - [ ] Test bot start (all components start)
  - [ ] Test bot stop (graceful shutdown)
  - [ ] Test event flow wiring
  - [ ] Test error handling (component failure)
- [ ] Create `tests/integration/test_bot.py`:
  - [ ] Test bot runs on testnet
  - [ ] Test bot detects and copies real trade
  - [ ] Test bot handles shutdown signal

## Test Examples
```python
def test_bot_initializes_all_components():
    """Bot should initialize all required components"""
    settings = Settings(...)
    bot = CopyTradingBot(settings)

    assert bot.blockchain is not None
    assert bot.kuru_client is not None
    assert bot.monitor is not None
    assert bot.detector is not None
    assert bot.copier is not None
    assert bot.executor is not None

def test_bot_starts_monitoring():
    """Bot start should begin wallet monitoring"""
    bot = CopyTradingBot(settings)
    bot.start()

    assert bot.is_running
    assert bot.monitor.is_monitoring

def test_bot_stops_gracefully():
    """Bot stop should cleanup all components"""
    bot = CopyTradingBot(settings)
    bot.start()
    bot.stop()

    assert not bot.is_running
    assert not bot.monitor.is_monitoring

@pytest.mark.integration
def test_bot_runs_end_to_end_on_testnet():
    """Bot should run and copy trades on real testnet"""
    settings = Settings()  # Load from .env
    bot = CopyTradingBot(settings)

    bot.start()

    # Simulate source wallet placing order
    # ... place test order from source wallet ...

    # Wait for detection and copying
    time.sleep(5)

    # Verify order was copied
    # ... check Kuru API for copied order ...

    bot.stop()
```

## Acceptance Criteria
- Unit tests with mocked components
- Integration test runs full bot on testnet
- Tests verify component initialization
- Tests verify event flow
- Tests verify graceful shutdown
- All tests initially fail

## Dependencies
- All previous core components
