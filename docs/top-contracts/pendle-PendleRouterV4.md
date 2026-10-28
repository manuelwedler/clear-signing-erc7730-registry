# Pendle RouterV4: clear-signing descriptor (mainnet)

> **Draft: not submitted by the Pendle team.** A language-model agent wrote this descriptor for the registry's top-contracts effort, using clear-signing-helper plus hand edits for the `calldata` format. Pendle did not write, review or approve it. Someone tied to Pendle should confirm the deployment and the wording before merge.

ERC-7730 spec limitations found for this contract: https://github.com/manuelwedler/clear-signing-erc7730-registry/blob/claude/nifty-euler-gwsa66/docs/spec-limitations/pendle-PendleRouterV4.md

## Summary

- Adds `registry/pendle/calldata-PendleRouterV4.json` and its testsv2 file, for Pendle RouterV4 at `0x888888888889758F76e7103c6CbF23ABbF58F946` on chain 1.
- **Proxy and ABI.** The router is a selector-to-facet proxy: `PendleRouterV4.sol:15-20` looks up `msg.sig` and delegatecalls the matching facet. Sourcify does not resolve this proxy type, so the ABI at the address holds only `fallback` and `receive`.
  - The ABI was rebuilt from all 246 `SelectorToFacetSet` events (the last facet per selector) and the Sourcify-verified ABIs of the 7 live facets: ActionMiscV3 `0x1266…8149`, ActionAddRemoveLiqV3 `0x664a…2d4f`, ActionSimple `0xf475…9ac4`, ActionStorageV4 `0x6a0e…64fc`, ActionSwapPTV3 `0x9d21…5379`, ActionSwapYTV3 `0xa685…8c31` and ActionCallbackV3 `0x997f…05d2`.
  - The map was confirmed with `selectorToFacet` calls at the latest block.
- 35 functions are described and 18 are excluded. Every amount on the screen is either an exact amount the router pulls, or a limit the router or the SY contract checks.
- **Aggregator swaps.** The router checks the final PT, YT, LP or SY amount after an aggregator swap in `TokenInput`, so those routes are shown in full. `TokenOutput.swapData.swapType` is pinned to 0, because the token of its minimum depends on `swapType`.
- Other chains were out of scope (Ethereum mainnet only).

## Coverage

**Described (35):**

- PT swaps: `swapExactTokenForPt`, `swapExactSyForPt`, `swapExactPtForToken`, `swapExactPtForSy`.
- YT swaps: `swapExactTokenForYt`, `swapExactSyForYt`, `swapExactYtForToken`, `swapExactYtForSy`.
- Add liquidity: `addLiquiditySingleToken`, `addLiquiditySingleSy`, `addLiquiditySinglePt`, `addLiquiditySingleTokenKeepYt`, `addLiquiditySingleSyKeepYt`, `addLiquidityDualTokenAndPt`, `addLiquidityDualSyAndPt`.
- Remove liquidity: `removeLiquidityDualTokenAndPt`, `removeLiquidityDualSyAndPt`, `removeLiquiditySinglePt`, `removeLiquiditySingleToken`, `removeLiquiditySingleSy`.
- Mint and redeem: `mintSyFromToken`, `redeemSyToToken`, `mintPyFromToken`, `redeemPyToToken`, `mintPyFromSy`, `redeemPyToSy`.
- Exits: `exitPreExpToToken`, `exitPreExpToSy`, `exitPostExpToToken`, `exitPostExpToSy`.
- Other: `swapTokenToTokenViaSy`, `redeemDueInterestAndRewards`, `boostMarkets`, `requestBurnQuota`, and `multicall`, whose actions use the `calldata` format.

**Excluded (18):**

| Function | Reason |
|---|---|
| `callAndReflect` | The Reflector rewrites the input amount of `reflectCall` (`Reflector.sol:54,72,78,90,102`), so any rendering of it would show a false amount. The reflector is caller-chosen (`ActionMiscV3.sol:423-432`). |
| `simulate` | Always reverts (`ActionMiscV3.sol:434-437`). |
| `redeemDueInterestAndRewardsV2` | Swaps rewards whose amounts are known only at execution (`ActionMiscV3.sol:134-175`). Its NatSpec says the interface may change. |
| `swapTokensToTokens` | Strict portability rejects it (`ARRAY_ORDER_PORTABILITY`): the minimum is in a multi-field tuple array, which Ledger Flex and Stax show by field. Its output is checked (`ActionMiscV3.sol:364-370`). |
| `swapCallback`, `limitRouterCallback` | Called by a Pendle market or the limit router (`ActionCallbackV3.sol:16,31`). |
| `transferOwnership`, `setSelectorToFacets` | `onlyOwner` (`ActionStorageV4.sol:21,39`). |
| `claimOwnership` | Pending owner only (`ActionStorageV4.sol:58`). |
| 8 × `…Simple` | NatSpec says "internal router use only" (`ActionSimple.sol:28,45,59,77,91,125,145,189`). The main functions delegate to them (`ActionDelegateBase.sol:121-126`). |
| `fallback()` | Reverts on unknown selectors (`PendleRouterV4.sol:15-20`). |

**Hidden fields (each with a reason):**

- `tokenIn` and `tokenRedeemSy`: they are the tickers of the shown amounts.
- TokenInput route fields (`tokenMintSy`, `pendleSwap`, `swapData.*`): the router pulls exactly `netTokenIn` (`ActionBase.sol:35,38,50-51`; `TokenHelper.sol:14-17`) and checks the final output.
- `input.swapData.extCalldata`: it carries the `calldata` format (callee `input.swapData.extRouter`, spender `input.pendleSwap`, since PendleSwap makes the call, `PendleSwap.sol:41-45`) but stays hidden. See "Embedded calls".
- `ApproxParams`: search hints only. The final output is checked against the minimum.
- `epsSkipMarket`: the rest goes to the market or back to the receiver (`ActionBase.sol:168-172,208-212,358`).
- Limit-order fills and `optData`: they are filled by the pinned limit router.
- `TokenOutput` fields left unused under the pin (`ActionBase.sol:73-74`).
- `SY` and `YT` arguments: they are the tickers of the shown amounts.
- Claim selectors: proceeds go to the shown `user` (`ActionMiscV3.sol:79-89`).
- `requestBurnQuota` data: the call only emits an event (`:439-441`).
- No recipient, amount or limit is hidden.

**Pinned arguments (`mustMatch`):**

| Field | Values | Why |
|---|---|---|
| `limit.limitRouter` (16 functions) | `0x0`, `0x000000000000c9B3E2C3Ec88B1B4c0cD853f4321` | Approved without limit and trusted for fill amounts (`ActionBase.sol:326-359`). Never read when the fill arrays are empty (`:373-375`). |
| `output.swapData.swapType` (8 functions) | `0` | The minimum is in `tokenRedeemSy` only with NONE (`ActionBase.sol:71-91`). |
| `calls.[].allowFailure` (`multicall`) | `false` | A skipped action would still be shown (`ActionBase.sol:401-407`). All 301 sampled items were `false`. |

## Embedded calls (`calldata` format)

- **`multicall`:** `calls.[].callData` uses the `calldata` format with callee `@.to`, `amountPath: @.value` and `spenderPath: @.from`. Each item is a delegatecall into the router itself, so `msg.value` and `msg.sender` stay the outer ones (`ActionMiscV3.sol:413-420`, `ActionBase.sol:397-409`). The pins of the inner functions still apply inside a batch.
- **Aggregator route data (`input.swapData.extCalldata`):** it has the `calldata` format but stays hidden. With it visible, both runners render a nested KyberSwap or Velora screen for Kyber and Paraswap routes, for example "Swap 31.927166 USDC for at least 23.949533 USD3 to recipient 0x8888…F946" (the router). They render raw hex for 0x routes and OKX routes, and `0x` for the 218 of 361 sampled calls with no route. It stays hidden because:
  - PendleSwap rewrites its amounts when `needScale` is true (`PendleSwap.sol:43`).
  - It is not calldata at all for 0x routes (`abi.encode`, `PendleSwap.sol:57-59`), and it is empty for direct routes.
  - It is executed by a caller-chosen `pendleSwap`, not by the signer.
  - The router's final minimum check is what protects the signer.
  - If it must be shown, `visible: "optional"` renders the same in both runners.
- **`output.swapData.extCalldata`:** no format, hidden. `swapType` is pinned to NONE, so the router never forwards it (`ActionBase.sol:73-74`).
- **`callAndReflect`:** stays excluded. Its two self-calls could use `calldata`, but its reflected call would always show a false input amount.

## What the screens say

| Judgment | Source |
|---|---|
| "Amount to Pay" is exact. Native ETH maps from `address(0)`, and `msg.value` must equal the amount. | `ActionBase.sol:35,38,50-53`; `TokenHelper.sol:11,15` |
| "Native Value Sent" is shown on every payable function. | `TokenHelper.sol:14-17` |
| PT, YT and SY amounts are raw ("(raw)"), next to the market, because the token is read with `readTokens()` and is not in the calldata. LP amounts carry the market ticker. | `ActionSwapPTV3.sol:25,62`; `ActionSwapYTV3.sol:30,70` |
| Every minimum is checked after all swaps and fills. | `ActionBase.sol:91,120,135,183,225,274,322`; `ActionAddRemoveLiqV3.sol:43,67,111,198,269,270,289,309,310,344,400`; `ActionMiscV3.sol:235,309` |
| The router checks the final output after the aggregator swap in `TokenInput`. With a route, the input goes to `pendleSwap` and the router measures its own `tokenMintSy` balance. The intermediate SY mint is only checked against 1; only the final check binds. | `ActionBase.sol:41-43`; `ActionSwapPTV3.sol:26`; `ActionSwapYTV3.sol:32`; Simple path `ActionSimple.sol:118,185,209,229,256` |
| The minimums of `mintSyFromToken` and `swapTokenToTokenViaSy` are enforced by the shown SY. | `ActionBase.sol:64,107` |
| Dual add liquidity: the token amount is exact and PT is "up to". | `ActionAddRemoveLiqV3.sol:33-40,60-64` |
| Exits pull exact PT, YT and LP amounts. | `ActionMiscV3.sol:255-282,390-397` |
| Redeem PT/YT: PT is always pulled, and YT only before expiry ("of PT, and of YT before expiry"). | `ActionBase.sol:127-132` |
| `boostMarkets` moves 0 tokens. | `ActionMiscV3.sol:407-411` |
| `multicall` shows each action with its own descriptor, under the caller's `msg.value` and `msg.sender`. | `ActionMiscV3.sol:413-420` |
| `limitRouter` pin: with fills and a zero address the call reverts. Any other address gets an unlimited approval and its fill amounts are trusted. The Pendle limit router is an upgradeable proxy to `PendleLimitRouter`, so trusting it means trusting Pendle's upgrade key. | `ActionBase.sol:166,206,250,298,336-356,373-375`; `ActionAddRemoveLiqV3.sol:92,179` |

## Deployments

- Chain 1, `0x888888888889758F76e7103c6CbF23ABbF58F946`: Sourcify `exact_match` for `PendleRouterV4` (solc 0.8.24, block 19759272). It is listed as `router` in Pendle's `deployments/1-core.json`.
- Other chains were out of scope.

## Tests

37 cases: 35 real mainnet transactions and 2 encoded.

- 32 were found by `discover` (Envio HyperSync over the whole chain).
- 1 came from `fixture --tx`: `removeLiquiditySingleToken` `0xfff290233002a11144c5e28a921970fd81c8bc99f8d995f32a292004eca8bccd`. The first one found used an aggregator exit, which the pin refuses.
- 1 is `swapExactPtForToken-limit` `0x5fc9a2d819fd8db7fe95feda2aec95cdcb666c634d2791b839abb4f243e7ba2c`, which fills orders through the pinned limit router.
- 2 are real multicalls: `0x93dd22f2af45c7b331387b6292d869565934d1160013619c0ac89b133edd3fc0` (with an excluded V2 inner call, shown as raw calldata) and `0xfb696fd8092d7ae1a6493ecc1e5db365414b0f0b528e69d876231653348f3172` (no calls).
- The 2 encoded cases are `exitPreExpToSy` and `requestBurnQuota`. Neither has ever been called directly.
- Three real multicalls with a described inner call render correctly in both runners, but cannot be in the testsv2 file: `0x6fdfc8cbfc2b6b025ddf5f3035fd55a9a5e4e120c9a717d2b4931be401f0e274`, `0x4b678dff86d212d5c5d8e6a9b2e7afbe3b8bd198d9436db3cf014a5f2eaec65c`, `0xbd63b85e79c8a3ca9ddd613a94a79643a6d119c1dc6d1e5765b891480db18d90`. The Rust runner rejects the nested `interpolatedIntent` that the Sourcify runner requires.

## Checks

- clear-signing-helper `0.6.0-preview.6` with `--strict-portability` and `--registry-runners`, then hand edits for `calldata`, verified with the registry CI checks.
- Lint (pin `python-erc7730@964176e2`): 0 errors and 36 warnings.
  - 35 × "Unknown selector": the linter fetches the proxy-only ABI, so **its ABI path check was effectively skipped**. The selectors were checked against the facet map instead.
  - 1 × "Display intent too long".
- Runners: Sourcify `@ethereum-sourcify/clear-signing@0.3.0` (`9d6d2fe4`) 37/37; Rust `llbartekll/clear-signing@0.1.0` (`65af2281`) 37/37.
- Claims (anvil forks of eth.drpc.org and mainnet.gateway.tenderly.co, up to 60 runs each), on the fixtures from before the `calldata` work:
  - 33 replayed real transactions with **0 findings**.
  - `exitPreExpToSy` and `requestBurnQuota`: skipped, encoded, no transaction to replay.
  - `removeLiquidityDualSyAndPt` (`0x8498c0e09fd30737c1c5e7232b8beed897eb7e508c185e70863f17173e8ac8ef`): skipped, because it reverts when replayed at the start of its block (it depends on an earlier transaction in the same block).
  - Timeouts (HTTP 408 or transport errors) were retried on the other endpoint until each fixture ran.
- Not done:
  - No device tests.
  - The AI review unit will likely hold only the 4 proxy source files, not the facets.
  - The Rust runner's nested-`interpolatedIntent` gap is a tool limitation to report upstream.

## Flags

1. The ABI was rebuilt from the on-chain facet map. A later `setSelectorToFacets` call can change behaviour at this address.
2. The lint ABI check is effectively skipped.
3. In a sample of one day and 19 hours, the `swapType` pin refuses 59 of 167 `TokenOutput` exits.
4. PT, YT and SY amounts are raw.
5. Most real multicalls (about 230 of 262 sampled) contain the excluded `redeemDueInterestAndRewardsV2`, which renders as raw calldata. Describing V2 would make them fully readable.
