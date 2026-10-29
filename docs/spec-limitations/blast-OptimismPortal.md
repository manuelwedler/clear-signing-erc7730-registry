# Blast OptimismPortal — ERC-7730 spec limitations

## L2 account credited by a deposit depends on the sender type
- **What the signer should see:** `depositTransaction` mints `msg.value` on Blast to the sender's own L2 address when the sender is an EOA, but to the *aliased* address (`msg.sender + 0x1111…1111`) when the sender is a contract (`AddressAliasHelper.applyL1ToL2Alias`, OptimismPortal.sol lines 439-442). A smart-account signer (for example a Safe) should see that the ETH is credited to the aliased address, not to its own.
- **What the spec cannot express:** no field format derives a value from `@.from` (Field formats > Address has `raw` and `addressName` only, no computed address), and `visible` rules (Field format specification > `visible`) cannot depend on whether `@.from` has code.
- **Workaround in this descriptor:** the sentence reads "Deposit {@.value} to Blast" and names no L2 account. A constant "Note" field (a literal `value`, no `path`) tells every signer: "From a contract wallet, the ETH is credited to its aliased address on Blast." It cannot show the aliased address itself, and EOA signers see the note too.
- **Proposed spec improvement:** a container value `@.fromAlias` (or a `params.alias` offset on `addressName`) and a `visible` rule keyed on the sender type, e.g. `{"ifSenderIs": ["contract"]}`, so a format can show "Credited to {@.fromAlias}" for contract senders only.

## ETH paid at finalization is a state-dependent fraction of the shown value
- **What the signer should see:** `finalizeWithdrawalTransaction` pays `_tx.value × sharePrice / 1e27` to the target, where `sharePrice ≤ 1e27` is read from the yield manager's checkpoint (WithdrawalQueue.sol `_calculateClaimableEther`, `_finalize`). The signer should see the real payout, not only its upper bound.
- **What the spec cannot express:** a field value computed from contract state or from arithmetic on another field. Field formats take a path or a literal value only (Field format specification > `path` / `value`); the spec deliberately has no on-chain read at display time (Security Considerations > External data resolution).
- **Workaround in this descriptor:** the amount is labelled "Maximum Amount" and the sentence says "up to {_tx.value}".
- **Proposed spec improvement:** none that keeps the spec free of external calls. If the spec ever admits state reads, a `scaledAmount` format with a `ratioPath` or `ratioCall` and an explicit precision would cover withdrawal queues of this kind (Lido and Blast share the share-price design).

## Cross-chain embedded calldata is not schema-valid
- **What the signer should see:** `depositTransaction._data` and the messenger's `sendMessage._message` decoded as calls on Blast (chain 81457). For the deposit: callee `_to`, value `_value`, sender the depositor's L2 account. For `sendMessage`: callee `_target`, sender the L2 messenger.
- **What the spec cannot express:** the spec text ("Field formats > calldata") lists `chainId`/`chainIdPath`, but `specs/erc7730-v2.schema.json` `$format/calldataParameters` has `additionalProperties: false` without them, and the pinned linter rejects them. Both registry runners render the field correctly with `chainId`.
- **Workaround in this descriptor:** `depositTransaction._data` and `sendMessage._message` already use the `calldata` format with `chainId: 81457`, as the ERC text describes, and `_isCreation` is pinned to false because creation data is not calldata. Until the schema change is released, the registry's schema validation and lint fail on these two fields. Both registry runners render them; with no descriptor for the callee on Blast, they show the call data raw.
- **Proposed spec improvement:** add `chainId` (integer) and `chainIdPath` to `calldataParameters` in the schema and to the linter model.

## A bytes argument whose meaning depends on another argument
- **What the signer should see:** on L1BlastBridge `bridgeERC20` for USDC or USDT, `_extraData` is a uint256 minimum DAI output (USDConversions lines 138-142). For DAI and stETH it is ignored.
- **What the spec cannot express:** there is no field that is visible only for some values of another field, and no defined result for a slice beyond the end of the bytes. With `_extraData.[0:32]` as `tokenAmount`, the runners agree on 32-byte data, but on empty data Sourcify shows "0 DAI" and Rust shows `<unresolved>`.
- **Workaround in this descriptor:** `_extraData.[0:32]` is shown as a DAI `tokenAmount` labelled "Min DAI if USDC/USDT", so the label carries the condition. For a DAI or stETH bridge the data is empty: the Sourcify runner shows "0 DAI" and the Rust runner shows `<unresolved>`, so the Rust runner fails those two test cases until the slice behaviour is defined and the runner is fixed.
- **Proposed spec improvement:** a `visible` rule conditioned on another path, and a defined out-of-range slice behaviour.
