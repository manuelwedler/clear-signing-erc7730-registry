# Across Ethereum SpokePool — ERC-7730 spec limitations

## Destination-chain account given as bytes32 next to a separate chain id
- **What the signer should see:** `recipient`, `exclusiveRelayer` and `outputToken` of `deposit`, `depositNow` and `unsafeDeposit`, and `updatedRecipient` of `speedUpDeposit`, are `bytes32`. They live on the chain given by the separate `destinationChainId` argument. For an EVM destination the value is a left-padded EVM address. For Solana it is a 32-byte public key (an account or a token mint). The signer should see the recipient as a checked, resolvable address on the destination chain, and the output token as its ticker or its full key.
- **What the spec cannot express:** `addressName` and `tokenTicker` are defined for addresses (Reference > Field formats). `interoperableAddressName` applies to `bytes` that hold an ERC-7930 encoding, with the chain inside the bytes (Field formats > Interoperable addresses). There is no format for "a bytes32 account whose chain is the value at this other path", and no rule that reads the value as a 20-byte address only when that chain is an EVM chain and as a full 32-byte key otherwise.
- **Workaround in this descriptor:**
  - `recipient` and `updatedRecipient` are shown as raw bytes32. A slice `[12:32]` was rejected because it would show a Solana key as a 20-byte EVM address.
  - `outputToken` uses `tokenTicker` on the full bytes32 value with `chainIdPath: #.destinationChainId`. For an EVM destination the wallet shows the ticker; for a Solana mint the lookup fails and the wallet shows the full 32-byte key. The Rust runner does exactly this; the Sourcify runner does not accept `tokenTicker` on bytes32 yet (a tooling to-do).
  - The origin-chain `depositor` is always an EVM address (`checkAddress`, SpokePool.sol line 1385; `toAddress`, line 862), so it uses `addressName` on the bytes32 value. The Sourcify runner does not accept that yet either.
  - The `address` variants use `addressName` and `tokenTicker` on the address.
- **Proposed spec improvement:** allow `addressName` and `tokenTicker` on `bytes32`, with `chainIdPath`/`chainId` parameters. A wallet reads the value as an EVM address when the chain is an EVM chain and the top 12 bytes are zero; otherwise it shows the full 32-byte value or resolves it in that chain's own address format. This is wishlist item 4.

## Chain id named from a registry that does not match the protocol's ids
- **What the signer should see:** the destination chain that Across actually routes to, for every id Across uses.
- **What the spec cannot express:** the `chainId` format (Integer formats > chainId) names the value from "EIP-155 reference values" and takes no parameters. Across uses ids that the EIP-155 registry (chainid.network) names differently or does not list: 999 is HyperEVM for Across, but the registry entry is "Wanchain Testnet", and 34268394551451 (Solana) has no entry. The format cannot override the name for an id, does not name its reference source, and does not define what a wallet shows for an id with no name. The contract does not check the id (SpokePool.sol line 1453 only emits it), so any value can be signed.
- **Workaround in this descriptor:** two fields on `destinationChainId` with complementary `visible: {"ifNotIn": [...]}` lists.
  - The `chainId` field shows the registry name for the 9 ids where wallet libraries agree on it (1, 10, 56, 137, 324, 8453, 42161, 43114, 59144).
  - An `enum` field (`metadata.enums.destinationChainOverride`) names the other 14 Across ids: 999 "HyperEVM" and 34268394551451 "Solana", plus 12 ids for which at least one wallet library has no name, labelled with their registry names.
  - An id outside both lists shows both fields.
  - Because a sentence may only refer to always-visible fields (Value interpolation), the interpolated intent no longer names the chain. The field carries it.
- **Proposed spec improvement:** give `chainId` an optional `$ref` to a `metadata.enums` entry that overrides registry names for the listed ids; name the reference source (for example the ethereum-lists/chains registry, or CAIP-2 for non-EVM chains); require that an id with no name is shown as its decimal value, marked as an unknown chain; and allow an interpolated path to refer to a set of fields on the same path whose visibility rules are complementary.

## Argument whose meaning depends on its magnitude
- **What the signer should see:** `exclusivityParameter` means "no exclusivity" when it is 0. When it is at most `MAX_EXCLUSIVITY_PERIOD_SECONDS` (one year), it is a duration added to the block time. Otherwise it is an absolute timestamp (SpokePool.sol, `_depositV3`).
- **What the spec cannot express:** a field has one `format`. There is no rule that picks `duration` or `date` by a value range (Display Formatting > Field format specification).
- **Workaround in this descriptor:** the field is hidden. It only decides which relayer may fill first, and it does not change what the signer pays or what the recipient gets.
- **Proposed spec improvement:** a `formatBy` rule with value ranges, for example `{"ranges": [{"max": 0, "format": "enum"}, {"max": 31536000, "format": "duration"}, {"format": "date"}]}`.

## Bytes argument that holds an ABI-encoded struct of calls
- **What the signer should see:** for a deposit with a `message`, the actions that run on arrival. For example: "on Base, swap the received USDC on <router>, then send the rest to <fallbackRecipient>".
- **What the spec cannot express:** the `calldata` format needs a selector and ABI arguments (Field formats > calldata). `message` is `abi.encode(Instructions{Call[]{target, callData, value}, fallbackRecipient})` for Across's MulticallHandler, with no selector. The core spec has no format that ABI-decodes a `bytes` field into a struct so that its members can use `calldata` with a chain id.
- **Workaround in this descriptor:** `message` and `updatedMessage` stay pinned with `mustMatch ["0x"]`. Deposits with destination actions fall back to blind signing.
- **Proposed spec improvement:** adopt the custom encoding layout of ethereum/ERCs PR 1925 (wishlist item 5). A `switch` case keyed on the tuple type `((address target,bytes callData,uint256 value)[] calls,address fallbackRecipient)` would decode the message, and its calls could use `calldata` with the destination chain id (wishlist item 2).
