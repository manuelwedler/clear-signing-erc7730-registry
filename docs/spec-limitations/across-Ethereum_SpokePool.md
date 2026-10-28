# Across Ethereum SpokePool — ERC-7730 spec limitations

## Destination-chain recipient given as bytes32 next to a separate chain id
- **What the signer should see:** `recipient` (and `depositor`, `exclusiveRelayer`, `outputToken`) of `deposit`, `depositNow` and `unsafeDeposit` are `bytes32`. The chain they live on is the separate `destinationChainId` argument. For an EVM destination the value is a left-padded EVM address; for Solana it is a 32-byte public key. The signer should see the recipient as a checked, resolvable address on the destination chain.
- **What the spec cannot express:** `addressName` applies to the `address` type only (Reference > Field formats > Address). `interoperableAddressName` applies to `bytes` that hold an ERC-7930 encoding, with the chain inside the bytes (Field formats > Interoperable addresses). There is no format for "a bytes32 account whose chain is the value at this other path", and no conditional format that would slice `[12:32]` only when the destination is an EVM chain.
- **Workaround in this descriptor:** `recipient` and `depositor` are shown as raw bytes32 in the bytes32 variants; the `address` variants (`depositV3`, `depositV3Now`, `speedUpV3Deposit`) use `addressName`. A slice `recipient.[12:32]` was rejected because it would show a Solana key as a 20-byte EVM address.
- **Proposed spec improvement:** add `chainIdPath`/`chainId` parameters to `addressName` (as `tokenAmount` already has) and allow `addressName` on `bytes32` when the chain is EVM, with the rule that a wallet shows the raw value when the chain at `chainIdPath` is not an EVM chain.

## Output amount denominated in a token on another chain
- **What the signer should see:** `outputAmount` is what the recipient receives, in the units of `outputToken` on `destinationChainId`. The signer should see "at least 99.5 USDC on Arbitrum One".
- **What the spec cannot express:** `tokenAmount` has `chainIdPath` (Field formats > tokenAmount), but it is a SHOULD without a defined fallback: a wallet that does not implement it resolves `outputToken` on the signing chain, where the same address may be a different token or absent, and scales by the wrong decimals (USDC has 6 decimals on Ethereum and 18 on BNB Smart Chain). Nothing in the spec lets an author require "raw if the (chain, token) pair is unknown". For a non-EVM destination (Solana) the token is a bytes32 mint, which `tokenPath` cannot name at all.
- **Workaround in this descriptor:** `outputAmount` is shown with format `raw` under the label "Output Amount (raw)", and `outputToken` as a raw address/bytes32 under "Output Token (dest.)". The amount paid in is the only formatted amount.
- **Proposed spec improvement:** make the fallback normative: when `chainIdPath`/`chainId` is present and the wallet cannot resolve metadata for that exact chain and token, it MUST display the raw integer with an "unknown token" warning and MUST NOT fall back to the signing chain's metadata. Allow `tokenPath` to point at a `bytes32` for non-EVM chains with the same fallback.

## Argument whose meaning depends on its magnitude
- **What the signer should see:** `exclusivityParameter` is "no exclusivity" when 0, a duration added to the block time when at most `MAX_EXCLUSIVITY_PERIOD_SECONDS` (one year), and an absolute timestamp otherwise (SpokePool.sol, `_depositV3`).
- **What the spec cannot express:** a field has one `format`; there is no rule that picks `duration` or `date` by a value range (Display Formatting > Field format specification).
- **Workaround in this descriptor:** the field is hidden with the reason that it only decides which relayer may fill first and does not change what the signer pays or what the recipient gets.
- **Proposed spec improvement:** a `formatBy` rule with value ranges, e.g. `{"ranges": [{"max": 0, "format": "enum"}, {"max": 31536000, "format": "duration"}, {"format": "date"}]}`.

## Bytes argument that holds an ABI-encoded struct of calls
- **What the signer should see:** for a deposit with a `message`, the actions that run on arrival. For example: "on Base, swap the received USDC on <router>, then send the rest to <fallbackRecipient>".
- **What the spec cannot express:** the `calldata` format needs a selector and ABI arguments (Field formats > calldata). `message` is `abi.encode(Instructions{Call[]{target, callData, value}, fallbackRecipient})`, with no selector. No format ABI-decodes a `bytes` field into a struct so that its members can use `calldata` with `chainIdPath`.
- **Workaround in this descriptor:** `message` and `updatedMessage` stay pinned with `mustMatch ["0x"]`. Deposits with destination actions fall back to blind signing.
- **Proposed spec improvement:** a `bytes` format such as `abiDecode` with a `types` parameter. Its decoded members could then be addressed by path and formatted, including `calldata` with `chainIdPath` and `calleePath`.
