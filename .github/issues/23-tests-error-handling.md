# Write Tests for Error Handling

**Labels:** `priority: medium`, `type: testing`, `mvp`, `tdd`, `utils`

## Description
Write tests for custom exceptions and error handling utilities.

## Tasks
- [ ] Create `tests/unit/core/test_exceptions.py`:
  - [ ] Test custom exception definitions
  - [ ] Test exception messages
  - [ ] Test exception attributes
- [ ] Create `tests/unit/utils/test_decorators.py`:
  - [ ] Test @retry decorator
  - [ ] Test retry with exponential backoff
  - [ ] Test max retry limit
  - [ ] Test async timeout decorator

## Test Examples
```python
def test_retry_decorator_retries_on_failure():
    """@retry should retry failed calls"""
    call_count = 0

    @retry(max_attempts=3, backoff=0.1)
    def failing_func():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise Exception("Temporary failure")
        return "success"

    result = failing_func()
    assert result == "success"
    assert call_count == 3

def test_retry_decorator_raises_after_max_attempts():
    """@retry should raise after exceeding max attempts"""
    @retry(max_attempts=3)
    def always_fails():
        raise Exception("Permanent failure")

    with pytest.raises(Exception):
        always_fails()

def test_async_timeout_decorator():
    """@async_timeout should timeout slow async functions"""
    @async_timeout(seconds=0.1)
    async def slow_func():
        await asyncio.sleep(1)

    with pytest.raises(asyncio.TimeoutError):
        await slow_func()
```

## Acceptance Criteria
- Tests verify retry logic
- Tests verify backoff timing
- Tests verify timeout behavior
- All tests initially fail

## Dependencies
- Issue #1: Add Project Dependencies
