# WI-004: Update Kuru Contract Address Constant

**Status:** Not Started
**Priority:** Critical
**Complexity:** Low
**Component:** Configuration

## Description

The Kuru testnet contract address is currently a placeholder string. This needs to be updated with the actual deployed contract address.

**File:** `src/kuru_copytr_bot/config/constants.py`
**Line:** 8

## Current Implementation

```python
KURU_CONTRACT_ADDRESS_TESTNET = "0xKuruTestnetAddress0000000000000000000000"  # Placeholder
```

## Research Requirements

Before implementation, research and verify:

1. **Kuru Official Documentation:**
   - Check official Kuru documentation for contract addresses
   - Review deployment information for testnet
   - Verify contract addresses for mainnet (if available)

2. **Kuru SDK:**
   - Check if SDK provides contract addresses
   - Review SDK configuration files
   - Look for constants or configuration modules

3. **Monad Block Explorer:**
   - Verify contract deployment on Monad testnet
   - Check contract verification status
   - Review contract code if verified

4. **Kuru Community Resources:**
   - Check GitHub repositories
   - Review Discord/Telegram announcements
   - Check for official contract registry

## Requirements

### Functional Requirements

1. Replace placeholder with actual Kuru testnet contract address
2. Verify contract address is valid (checksummed)
3. Add mainnet contract address if available
4. Add comments with source/verification links

### Non-Functional Requirements

1. Ensure address is from official source
2. Document where address was obtained
3. Include block explorer links for verification

## Acceptance Criteria

### Research Phase
- [ ] Kuru official documentation checked for contract addresses
- [ ] Kuru SDK reviewed for contract address constants
- [ ] Contract verified on Monad testnet block explorer
- [ ] Source of contract address documented (documentation link, SDK version, etc.)

### Implementation Phase
- [ ] Placeholder address removed
- [ ] Real Kuru testnet contract address added
- [ ] Address is properly checksummed (Web3.toChecksumAddress format)
- [ ] Mainnet address added if available (or marked as TBD)
- [ ] Comment added with:
  - Source of address (documentation URL, SDK reference)
  - Block explorer verification link
  - Date when address was verified
  - Contract version if applicable
- [ ] Address format validated (42 characters, starts with "0x")

### Testing
- [ ] Unit test added to verify address format
- [ ] Unit test verifies address is checksummed
- [ ] Integration test verifies contract is deployed at address
- [ ] Test verifies contract responds to basic calls

### General
- [ ] No placeholder or dummy addresses
- [ ] Address from official/verified source only
- [ ] Code committed to current branch with message: "feat: update Kuru contract address with verified testnet address (WI-004)"

## Implementation Notes

1. This should be completed **before** WI-002 (transaction encoding)
2. Consider adding contract version constant
3. Consider adding deployment block number for event filtering
4. May want to add multiple network support (testnet, mainnet)
5. Consider creating a network configuration structure

## Example Format

```python
# Kuru Protocol Contract Addresses
# Source: https://docs.kuru.protocol/contracts
# Verified: 2025-01-15

KURU_CONTRACT_ADDRESS_TESTNET = "0x1234567890AbCdEf1234567890AbCdEf12345678"  # Monad Testnet
# Explorer: https://explorer.monad.testnet/address/0x1234...
# Deployed: Block 123456

KURU_CONTRACT_ADDRESS_MAINNET = None  # TBD - Mainnet not launched yet
```

## Dependencies

- None (highest priority - blocks WI-002)

## Estimated Effort

1-2 hours (mostly research to find official address)
