# Write Tests for Configuration Management

**Labels:** `priority: critical`, `type: testing`, `mvp`, `tdd`, `config`

## Description
Write tests for configuration loading, validation, and environment variable handling.

## Tasks
- [ ] Create `tests/unit/config/test_settings.py`:
  - [ ] Test loading from environment variables
  - [ ] Test required fields validation
  - [ ] Test default values
  - [ ] Test invalid configuration rejection
  - [ ] Test sensitive data handling (private keys)
  - [ ] Test RPC endpoint validation
  - [ ] Test wallet address validation
- [ ] Create `tests/unit/config/test_constants.py`:
  - [ ] Test constants are defined
  - [ ] Test contract addresses are valid
  - [ ] Test chain ID is correct

## Test Examples
```python
def test_settings_requires_private_key():
    """Settings should require private key"""
    with pytest.raises(ValidationError):
        Settings(private_key=None)

def test_settings_validates_wallet_address_format():
    """Settings should validate Ethereum address format"""
    with pytest.raises(ValidationError):
        Settings(wallet_address="invalid_address")

def test_settings_loads_from_env(monkeypatch):
    """Settings should load from environment variables"""
    monkeypatch.setenv("PRIVATE_KEY", "0x...")
    monkeypatch.setenv("MONAD_RPC_URL", "https://...")
    settings = Settings()
    assert settings.private_key is not None

def test_settings_validates_source_wallets_list():
    """Settings should validate source wallets is a list"""
    with pytest.raises(ValidationError):
        Settings(source_wallets="not_a_list")

def test_copy_ratio_must_be_positive():
    """Copy ratio must be > 0"""
    with pytest.raises(ValidationError):
        Settings(copy_ratio=-0.5)
```

## Acceptance Criteria
- Tests cover all configuration fields
- Tests verify Pydantic validation works
- Tests verify environment variable loading
- Tests verify default values
- Tests verify security constraints (private key handling)
- All tests initially fail

## Dependencies
- Issue #1: Add Project Dependencies
