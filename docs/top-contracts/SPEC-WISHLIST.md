# ERC-7730 wishlist

Spec and schema changes found while writing the top-contracts descriptors. An issue on ethereum/ERCs will be created from this list later. Each item names the PRs that would benefit and how they would use the change.

## 1. Prepend bytes to embedded calldata before decoding

- **Problem:** some contracts do not forward a `bytes` argument as it is. MetaMask MetaSwap (`0x881D40237659C251811CEC9c364ef91dC08D300C`, `swap(string,address,uint256,bytes)`) builds the call as `adapter.selector + abi.encode(msg.sender) + adapter.data + data` (MetaSwap.sol lines 146-151). The `calldata` format can name the callee and the selector, also through a map keyed on `aggregatorId`. But it decodes only `data`, which is the tail of an ABI encoding: without the sender word in front, every argument shifts by one word, and the offset of the inner `bytes` misses.
- **Proposal:** an optional `calldata` parameter that lists values to put in front of the field before decoding, each a path, a constant or a map reference, ABI-encoded as one word each or as raw bytes. For example: `"prefix": [{"abiEncode": "@.from"}, {"map": "$.metadata.maps.adapterData", "keyPath": "aggregatorId"}]`.
- **Related work:** ethereum/ERCs PR 1925, "Add ERC: Custom Encoding Layout for ERC-7730" (open draft, checked 2026-10-29). It adds `format: "customEncoding"` to describe non-ABI `bytes` layouts, with `offset`, `length`, `lengthFrom` and `toEnd`. It could describe the static words inside MetaSwap's `data` as a layout. It does not add bytes in front of embedded calldata, so it does not solve this item.
- **Which of our PRs would benefit:** none of the six directly. It would make a MetaSwap descriptor possible. MetaSwap is in the top contracts (rank 12 in the 24-hour list on the Sourcify dashboard) and was dropped from the handoff as "needs a spec change".
- **How we would use it:** a MetaSwap descriptor with `calldata` on `data`, with `callee` and `selector` mapped from `aggregatorId`, and a prefix of `@.from` plus the mapped fixed data. Adapter descriptors would still be needed, which requires the adapters to be verified.

## 2. Allow `chainId` and `chainIdPath` in the `calldata` format schema

- **Problem:** the ERC text lists `chainIdPath` / `chainId` for the `calldata` format ("Field formats > calldata": "Specifies the chain ID if it differs from the current contract's chain"). But `$format/calldataParameters` in `erc7730-v2.schema.json` (and v1) has only callee, selector, amount and spender, with `additionalProperties: false`. The pinned linter rejects `chainId` too. Both registry test runners already render it correctly.
- **Proposal:** add `chainId` (integer or map reference) and `chainIdPath` (string) to `calldataParameters`, as `tokenAmount` already has them. This is a MINOR schema release (2.2.0), because it only accepts more descriptors. The linter model (sourcifyeth/python-erc7730) needs the same change. A spec PR is being prepared; see `agent-instructions-erc7730-calldata-chainid.md` in this folder.
- **Status in our PRs:** #3174 and #3172 already use `chainId` as the ERC text describes (since 2026-10-29), so their schema validation and lint fail until this is released.
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
