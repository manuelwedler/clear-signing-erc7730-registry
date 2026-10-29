# Improvements for clear-signing-helper

Limitations of [clear-signing-helper](https://github.com/portdeveloper/clear-signing-helper) (version `0.6.0-preview.6`) that we hit while writing the top-contracts descriptors. Each item says where it hit, how we worked around it, and what would fix it. Runner, linter and spec issues are tracked in `REMAINING.md` and `SPEC-WISHLIST.md`, not here.

## 1. No support for the `calldata` field format

- **Where it hit:** every PR with embedded calls: #3172 Blast and #3174 Base (portal withdrawal and deposit data, messenger `relayMessage` and `sendMessage`), #3173 Across, #3175 Uniswap and #3176 Pendle (`multicall`, aggregator route data). `apply` refuses the format with `UNSUPPORTED_FORMAT`.
- **Workaround:** all `calldata` fields were added to the descriptor JSON by hand after `export`, and checked with the registry CI checks instead of the helper's.
- **Improvement:** support `calldata` in the decisions file with `calleePath`/`callee`, `selectorPath`/`selector`, `amountPath`/`amount`, `spenderPath`/`spender` and `chainIdPath`/`chainId`. Render nested calls in `preview` and `test` by resolving the callee's descriptor from the project or the registry clone, on the field's chain. Offer the callee's address from the source when it is a constant or an argument.

## 2. Refuses calldata with bytes after the ABI arguments

- **Where it hit:** #3173 Across. Most Across app deposits append an integrator tag (`0x1dc0de…`) after the arguments: 213 of 229 recent `depositV3` calls and all 80 recent `deposit` calls. `fixture --tx` and `discover` refuse them as non-canonical calldata. (MetaMask's MetaSwap transactions also carry a trailing byte.)
- **Workaround:** real tagged deposits were added to the testsv2 file by hand, with their full calldata. Both registry runners decode them and ignore the trailing bytes, as ABI decoding does.
- **Improvement:** accept trailing bytes after a canonical ABI encoding, keep the full calldata in the fixture, and record the length of the extra bytes as a warning instead of refusing.

## 3. Proxy types that Sourcify does not resolve

- **Where it hit:** #3172 Blast and #3174 Base (`ResolvedDelegateProxy` for the L1CrossDomainMessenger, `L1ChugSplashProxy` for the bridges) and #3176 Pendle (a selector-to-facet proxy whose Sourcify ABI holds only `fallback` and `receive`). `init --address` on the proxy did not find the implementation, and `init` on the implementation bound the implementation address.
- **Workaround:** `init` on the implementation, then the deployment was rebound to the proxy by editing `abi/*.source.json` and the draft deployment. For Pendle, the ABI was rebuilt from all `SelectorToFacetSet` events and the verified facet ABIs.
- **Improvement:** an `init --address <proxy> --implementation <addr>` option that binds the proxy and reads the implementation's ABI; resolve these proxy types on-chain (`AddressManager.getAddress`, the EIP-1967 slot, a facet map); and a facet mode that merges the ABIs of all live facets.

## 4. No slot for a constant field

- **Where it hit:** #3171 SwftSwap (a "Note" that the payout is off-chain and the minimum is not enforced), #3172 Blast and #3174 Base (a "Note" about the L1-to-L2 address alias on `depositTransaction`). The spec allows a field with a literal `value` and no `path`.
- **Workaround:** added by hand to the descriptor and to every expected screen in the tests.
- **Improvement:** let the decisions file add constant fields (`label`, `value`, position), and render them in `preview` and the expectations.

## 5. No way to express bundled groups

- **Where it hit:** #3176 Pendle (`swapTokensToTokens` and `redeemDueInterestAndRewardsV2`, where amounts and minimums pair per swap or per YT). The agent skill already says the decisions file cannot express `{"iteration": "bundled"}`.
- **Workaround:** groups added to the descriptor by hand.
- **Improvement:** a group slot in the decisions file that lists the paired array paths and the iteration mode.

## 6. No support for `metadata.maps`

- **Where it hit:** #3176 Pendle (maps from market to PT, YT and SY, 664 markets each, and from YT to SY).
- **Workaround:** a separate script built the maps from on-chain logs and `readTokens()` calls and wrote them, and the map references in `tokenAmount`, into the descriptor.
- **Improvement:** map support in the decisions file (`token: {"map": …, "keyPath": …}`), a command that builds a map from event logs plus a view call, and a refresh command for maps that grow.

## 7. `claims` crashes on fixtures of excluded functions

- **Where it hit:** #3171 SwftSwap. `claims` stopped with `Cannot read properties of undefined (reading 'fields')` when it reached a fixture of an excluded function (`transferOwnership`).
- **Workaround:** the fixtures of excluded functions were deleted before running `claims`.
- **Improvement:** skip fixtures of excluded functions in `claims` with a notice.

## 8. `@.value` is required on payable functions that are reached only as nested calls

- **Where it hit:** #3172 Blast. The bridges' `finalizeBridgeETH` and the messenger's `relayMessage` are payable, but signers only see them nested inside a portal withdrawal. The helper required `@.value` on screen, so they show "Max ETH Attached" next to "Maximum Amount".
- **Workaround:** none; the field is shown.
- **Improvement:** allow hiding `@.value` with a reason on a function marked as nested-only, or when an embedding descriptor passes the value through `amountPath`.

## 9. Strict portability blocks spec features instead of flagging them per field

- **Where it hit:** #3175 Uniswap (`int24` ticks on `mint`) and #3176 Pendle (`swapTokensToTokens` and `redeemDueInterestAndRewardsV2`, with multi-field tuple arrays). `export --strict-portability` refuses the whole export, so these were first hidden or excluded. Both registry runners render the ticks correctly.
- **Workaround:** the fields and functions were added back by hand after the user asked for every spec feature, and the device concern is stated in the PR text.
- **Improvement:** keep strict portability as a report, but allow a per-field or per-function override with a recorded reason, so that a descriptor can use a spec feature knowingly and still export.

## 10. The lint warning count includes a uv notice

- **Where it hit:** every PR. The helper's lint count included uv's `UV_NATIVE_TLS` deprecation notice as a warning, so its counts were one higher than the linter's real warnings.
- **Improvement:** filter tool notices out of the lint output before counting.
