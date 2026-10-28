# Blast OptimismPortal — ERC-7730 spec limitations

## L2 account credited by a deposit depends on the sender type
- **What the signer should see:** `depositTransaction` mints `msg.value` on Blast to the sender's own L2 address when the sender is an EOA, but to the *aliased* address (`msg.sender + 0x1111…1111`) when the sender is a contract (`AddressAliasHelper.applyL1ToL2Alias`, OptimismPortal.sol lines 439-442). A smart-account signer (for example a Safe) should see that the ETH is credited to the aliased address, not to its own.
- **What the spec cannot express:** no field format derives a value from `@.from` (Field formats > Address has `raw` and `addressName` only, no computed address), and `visible` rules (Field format specification > `visible`) cannot depend on whether `@.from` has code.
- **Workaround in this descriptor:** the sentence reads "Deposit {@.value} to Blast" and names no L2 account. The report states the aliasing caveat.
- **Proposed spec improvement:** a container value `@.fromAlias` (or a `params.alias` offset on `addressName`) and a `visible` rule keyed on the sender type, e.g. `{"ifSenderIs": ["contract"]}`, so a format can show "Credited to {@.fromAlias}" for contract senders only.

## ETH paid at finalization is a state-dependent fraction of the shown value
- **What the signer should see:** `finalizeWithdrawalTransaction` pays `_tx.value × sharePrice / 1e27` to the target, where `sharePrice ≤ 1e27` is read from the yield manager's checkpoint (WithdrawalQueue.sol `_calculateClaimableEther`, `_finalize`). The signer should see the real payout, not only its upper bound.
- **What the spec cannot express:** a field value computed from contract state or from arithmetic on another field. Field formats take a path or a literal value only (Field format specification > `path` / `value`); the spec deliberately has no on-chain read at display time (Security Considerations > External data resolution).
- **Workaround in this descriptor:** the amount is labelled "Maximum Amount" and the sentence says "up to {_tx.value}".
- **Proposed spec improvement:** none that keeps the spec free of external calls. If the spec ever admits state reads, a `scaledAmount` format with a `ratioPath` or `ratioCall` and an explicit precision would cover withdrawal queues of this kind (Lido and Blast share the share-price design).
