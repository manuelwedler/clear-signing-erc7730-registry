# ERC-7730 wishlist

Spec and schema changes found while writing the top-contracts descriptors. An issue on ethereum/ERCs will be created from this list later. Each item names the PRs that would benefit and how they would use the change.

## 1. Prepend bytes to embedded calldata before decoding

- **Problem:** some contracts do not forward a `bytes` argument as it is. MetaMask MetaSwap (`0x881D40237659C251811CEC9c364ef91dC08D300C`, `swap(string,address,uint256,bytes)`) builds the call as `adapter.selector + abi.encode(msg.sender) + adapter.data + data` (MetaSwap.sol lines 146-151). The `calldata` format can name the callee and the selector, also through a map keyed on `aggregatorId`. But it decodes only `data`, which is the tail of an ABI encoding: without the sender word in front, every argument shifts by one word, and the offset of the inner `bytes` misses.
- **Proposal:** an optional `calldata` parameter that lists values to put in front of the field before decoding, each a path, a constant or a map reference, ABI-encoded as one word each or as raw bytes. For example: `"prefix": [{"abiEncode": "@.from"}, {"map": "$.metadata.maps.adapterData", "keyPath": "aggregatorId"}]`.
- **Related work:** ethereum/ERCs PR 1925, "Add ERC: Custom Encoding Layout for ERC-7730" (open draft, checked 2026-10-29 at commit `e5f8d3d`). It does not add bytes in front of embedded calldata. But two of its features would cover MetaSwap another way: a `customEncoding` `object` layout (with `offset` and `lengthFrom`) can decode the fixed words of `data` and its inner aggregator calldata, and its `interaction` construct builds a call from a target, a function signature and separate argument values. If PR 1925 is adopted, this item may be dropped.
- **Which of our PRs would benefit:** none of the six directly. It would make a MetaSwap descriptor possible. MetaSwap is in the top contracts (rank 12 in the 24-hour list on the Sourcify dashboard) and was dropped from the handoff as "needs a spec change".
- **How we would use it:** a MetaSwap descriptor with `calldata` on `data`, with `callee` and `selector` mapped from `aggregatorId`, and a prefix of `@.from` plus the mapped fixed data. Adapter descriptors would still be needed, which requires the adapters to be verified.

## 2. Allow `chainId` and `chainIdPath` in the `calldata` format schema

- **Status: done.** ethereum/ERCs PR 2124 adds both parameters to `calldataParameters` in the v2.0.0, v2.1.0 and v2 schema files (the ERC text already listed them) and forbids setting both at once. The registry synced it in #3180 on 2026-10-29. The registry linter still needs the matching change. Keep this item in the issue only as a reference.

- **Problem:** the ERC text lists `chainIdPath` / `chainId` for the `calldata` format ("Field formats > calldata": "Specifies the chain ID if it differs from the current contract's chain"). But `$format/calldataParameters` in `erc7730-v2.schema.json` (and v1) has only callee, selector, amount and spender, with `additionalProperties: false`. The pinned linter rejects `chainId` too. Both registry test runners already render it correctly.
- **Proposal:** add `chainId` (integer or map reference) and `chainIdPath` (string) to `calldataParameters`, as `tokenAmount` already has them. This is a MINOR schema release (2.2.0), because it only accepts more descriptors. The linter model (sourcifyeth/python-erc7730) needs the same change. A spec PR is being prepared; see `agent-instructions-erc7730-calldata-chainid.md` in this folder.
- **Status in our PRs:** #3174 and #3172 use `chainId` and pass schema validation since the sync; lint fails on it until the linter is updated.
- **Which of our PRs would benefit and how:**
  - **#3174 Base:** `OptimismPortal2.depositTransaction._data` as `calldata` with callee `_to`, `chainId: 8453`, amount `_value`. The `mustMatch ["0x"]` pin on `_data` could then go, so deposits that call a contract on Base are clear-signed. A prototype rendered the real deposit `0xfbcfabdb570a0ccda01975caf9ef7de8ca71476ab98a80be63788871780785e4` as a nested 1inch swap on Base in both runners. `L1CrossDomainMessenger.sendMessage._message` as `calldata` with callee `_target`, `chainId: 8453`, spender the L2 messenger `0x4200000000000000000000000000000000000007`, instead of raw.
  - **#3172 Blast:** the same for `OptimismPortal.depositTransaction._data` and `L1CrossDomainMessenger.sendMessage._message`, with `chainId: 81457`. Both are shown raw today.
  - The deposit's spender would still be wrong for contract-wallet signers, because the L2 call runs as the aliased address. That is a separate limitation in the Base and Blast spec-limitation notes.

## 3. A `bytes` argument whose meaning depends on another argument

- **Problem:** the same argument can mean different things depending on another argument, and the spec has no conditional field. On Blast's `L1BlastBridge.bridgeERC20`, `_extraData` is a uint256 minimum output for USDC and USDT (USDConversions.sol lines 138-142) and is ignored for DAI and stETH. Separately, the result of a byte slice beyond the end of the data is undefined: for `_extraData.[0:32]` on empty bytes, the Sourcify runner shows "0 DAI" and the Rust runner shows `<unresolved>`.
- **Proposal:** a `visible` rule conditioned on another path, for example `{"ifPath": "_localToken", "in": ["0xA0b8…USDC", "0xdAC1…USDT"]}`, and a normative rule for slices that go past the end of the data (for example: treat the field as absent).
- **Which of our PRs would benefit and how:**
  - **#3172 Blast:** show `_extraData.[0:32]` as `tokenAmount` in DAI ("Minimum DAI out") only for USDC and USDT bridges, instead of the raw bytes labelled "Min Out (USDC/USDT)".
  - **#3176 Pendle:** the same mechanism would cover two related cases: the `TokenOutput` minimum, whose token is `tokenRedeemSy` only when `swapType` is NONE (today `swapType` is pinned to 0, which refuses 59 of 167 sampled aggregator exits), and `swapData.extCalldata`, which is calldata only for some swap types (today it is hidden).

## 4. An address format for `bytes32` and for non-EVM addresses on another chain

- **Problem:** cross-chain contracts pass addresses as `bytes32` next to a separate chain id, so that the same argument can hold an EVM address or a non-EVM one, such as a Solana public key. `addressName` applies only to the `address` type (Field formats > addressName). `interoperableAddressName` needs ERC-7930 bytes, which carry the chain inside the value. So there is no way to say "this `bytes32` is an account on the chain at this other path". Even an argument that is always an EVM address cannot use `addressName` if its type is `bytes32`.
- **Proposal:** let `addressName` accept `bytes32` (an EVM address in the low 20 bytes, high bytes zero), and add `chainIdPath` / `chainId` to it, as `tokenAmount` and `tokenTicker` have. For a non-EVM chain, the wallet shows the value in that chain's native address form (for example base58 for Solana), or as an ERC-7930 / CAIP-10 interoperable address. The same `chainId` parameter would let the wallet resolve names (ENS and others) on the right chain for EVM addresses on L2s.
- **Which of our PRs would benefit and how:**
  - **#3173 Across:** `recipient`, `exclusiveRelayer` and `outputToken` of the `bytes32` deposit functions, and `updatedRecipient` of `speedUpDeposit`, with `chainIdPath: destinationChainId`. They are raw today, because the destination can be Solana. The `bytes32` `depositor` is always an EVM address on Ethereum and already uses `addressName`, which the tooling must accept (see the to-dos).
  - **#3174 Base and #3172 Blast:** the L2 recipient `_to` of `depositTransaction`, `bridgeETHTo`, `bridgeERC20To` and similar, with `chainId: 8453` or `81457`, so that names resolve on the L2.
  - **#3171 SwftSwap:** only partly. Its `destination` is a string address on a chain named inside another string (`toToken`), which this proposal does not cover.

## 5. Adopt the custom encoding layout of ethereum/ERCs PR 1925

- **Problem:** some `bytes` arguments are not calldata but other encodings: ABI-encoded structs, packed data, or calls the contract assembles itself. The core spec can only show them raw or hide them.
- **Proposal:** adopt PR 1925 ("Add ERC: Custom Encoding Layout for ERC-7730", open draft, checked 2026-10-29 at commit `e5f8d3d`). Its `switch` cases decode a `bytes` value as a regular ABI tuple named by its type string, with `calldata` formats on the decoded members (`~.[].callData`); `customEncoding` describes packed layouts; `interaction` builds a call from separate values.
- **Which of our PRs would benefit and how:**
  - **#3173 Across:** the deposit `message`, which is `abi.encode(Instructions{Call[] calls, address fallbackRecipient})` for Across's MulticallHandler. A `switch` case with that tuple type could show each destination call with the `calldata` format (callee `~.calls.[].target`, amount `~.calls.[].value`, and the destination chain id from wishlist item 2), and the fallback recipient. The `mustMatch ["0x"]` pin on `message` could then go for that handler. The case still depends on the recipient being that handler, which the `switch` would need as its expression.
  - **#3176 Pendle:** the aggregator route data for 0x routes is `abi.encode(...)`, not calldata (PendleSwap.sol lines 57-59); a `switch` on the swap type could decode it.
  - MetaSwap (no PR): see item 1.


## 6. A chain for native-currency amounts

- **Problem:** the `amount` format ("Field formats > amount") always renders a value in the native currency of the chain the transaction is signed on. It has no `chainId` / `chainIdPath`, unlike `tokenAmount` and `tokenTicker`. So an amount that is spent on another chain, such as the ETH that an L1 deposit sends on the L2, is labelled with the L1's currency. That is right for Base and Blast, which use ETH on both chains, but wrong for an L2 with a custom gas token.
- **Proposal:** add the optional `chainId` / `chainIdPath` parameters of `tokenAmount` to `amount`, with the same semantics: the wallet renders the value in the native currency of that chain.
- **Which of our PRs would benefit and how:**
  - **#3174 Base:** `OptimismPortal2.depositTransaction._value` ("ETH Sent on L2") with `chainId: 8453`. Today the chain is only in the label.
  - **#3172 Blast:** `OptimismPortal.depositTransaction._value` ("ETH to Send on L2") with `chainId: 81457`.
  - Any OP Stack portal with a custom gas token, where the label workaround would show the wrong currency.

## 7. `specialValues` on every format, not only `date`

- **Problem:** contracts give special meaning to exact values: zero or the maximum integer for "no limit" or "everything", the zero address for "this contract" or "nobody". The spec has `threshold` / `message` only on `amount` and `tokenAmount`, and ethereum/ERCs PR 2027 ("Update ERC-7730: add specialValues to the date format", open, checked 2026-10-29 at commit `aae5348`) adds a `specialValues` map to `date` only. Other formats, and in particular `addressName`, `raw` and `unit`, cannot label a special value. The visibility rules cannot replace a value with a text either.
- **Proposal:** extend PR 2027's `specialValues` to every field format: keys are decimal strings for integer types and checksummed or lowercase hex strings for addresses and bytes, and values are the text to display for that exact value. A wallet MUST display the mapped text when the value matches. This could be a change request on PR 2027 itself rather than a separate proposal.
- **Which of our PRs would benefit and how:**
  - **#3175 Uniswap:** `collect.params.recipient` with `{"0x0000000000000000000000000000000000000000": "This contract (any caller can sweep)"}`, instead of a raw zero address explained in the sentence. `collect.params.amount0Max` and `amount1Max` with `{"340282366920938463463374607431768211455": "All owed"}`, instead of a 39-digit number.
  - **#3173 Across:** `exclusiveRelayer` with `{"0x0000…0000": "Any relayer"}` and `exclusivityParameter` with `{"0": "No exclusivity"}`, so both could be shown instead of hidden.

