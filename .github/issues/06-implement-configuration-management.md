# Implement Configuration Management

**Labels:** `priority: critical`, `type: implementation`, `mvp`, `tdd`, `config`

## Description
Implement configuration system to pass all tests from Issue #5.

## Tasks
- [ ] Implement `src/kuru_copytr_bot/config/settings.py`:
  - [ ] `Settings` class with Pydantic
  - [ ] Environment variable loading (dotenv)
  - [ ] Field definitions:
    - [ ] `private_key: str` (required, validated)
    - [ ] `wallet_address: str` (derived from private key)
    - [ ] `monad_rpc_url: str` (required)
    - [ ] `kuru_api_url: str` (required)
    - [ ] `source_wallets: List[str]` (required, validated addresses)
    - [ ] `copy_ratio: Decimal` (default=1.0, must be > 0)
    - [ ] `max_position_size_usd: Decimal` (required)
    - [ ] `dry_run: bool` (default=False)
    - [ ] `log_level: str` (default="INFO")
- [ ] Implement `src/kuru_copytr_bot/config/constants.py`:
  - [ ] Kuru contract addresses (testnet)
  - [ ] Monad chain ID
  - [ ] Event signatures/ABIs
  - [ ] Gas limits
- [ ] Create `.env.example` with all required fields documented

## Acceptance Criteria
- All tests from Issue #5 pass
- Settings validated on instantiation
- Clear error messages for invalid config
- Secure handling of private keys
- Example .env.example file provided

## Dependencies
- Issue #1: Add Project Dependencies
- Issue #5: Write Tests for Configuration Management
