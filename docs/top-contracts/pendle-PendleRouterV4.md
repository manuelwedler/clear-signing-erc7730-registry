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

## Update: token maps, `swapTokensToTokens` and `redeemDueInterestAndRewardsV2`

Add this to the PR #3176 description. It supersedes the earlier text on raw PT, YT and SY amounts, on the two excluded functions, and flags 4 and 5.

**Coverage**
- 37 functions are described and 16 are excluded. `swapTokensToTokens` and `redeemDueInterestAndRewardsV2` are now described. In blocks 26,200,000 to 26,276,221 (about 10.6 days) the router had 838 successful direct `swapTokensToTokens` calls and 151 direct V2 calls. In a sample of 990 successful multicalls, every inner call now has a description; the sample has 844 inner V2 calls.
- New `metadata.maps`: `marketPt`, `marketYt` and `marketSy` (664 entries each) and `ytSy` (YT to SY, 639 entries). They were built from all `CreateNewMarket` logs of Pendle's market factories: the five in Pendle's `deployments/1-core.json`, plus one unlisted factory created by Pendle's deployer with four test markets. The FiraMarketFactory fork is left out. Each market's `readTokens()` was called at the latest block: no failures, the PT matched the event every time, and `YT.SY()` matched every time. 604 of the markets are expired and are included, because the router can still redeem and exit through them.
- Entries never go stale (PT, SY and YT are immutables, PendleMarketV7.sol:49-51,73-75). New markets must be added; until then their transactions are blind, as the spec requires. Pendle created 37 markets in the last 90 days. The newest market in the maps is from block 26,231,611.

**What the screens say**

| Judgment | Source |
|---|---|
| PT, YT and SY amounts show the market's token through a map keyed on `market`. The "(raw)" labels are gone. | ActionSwapPTV3.sol:25,47,62,82; ActionSwapYTV3.sol:30,53,70,90; ActionAddRemoveLiqV3.sol:28,57,86,131,156,211,230,283,359,407; ActionMiscV3.sol:251,386 |
| The SY amounts of `mintPyFromSy` and `redeemPyToSy` show `YT.SY()` through the `ytSy` map. | ActionMiscV3.sol:61,69; ActionBase.sol:116,123-135 |
| `swapTokensToTokens`: a bundled group shows, per swap, the exact "Amount to Pay" and the "Minimum to Receive". Each input is pulled exactly, and native input needs `msg.value` equal to the amount. | ActionMiscV3.sol:185-187; TokenHelper.sol:14-17 |
| `swapTokensToTokens`: each minimum is checked per swap and paid to the signer; amounts are not rescaled. | ActionMiscV3.sol:190,353-370 |
| V2: every claim, redemption and swap output goes to `msg.sender`, shown as "Beneficiary". | ActionMiscV3.sol:114,118-119,124-126,130,145,151-152,158,326,370 |
| V2: "Minimum Interest" binds when interest is not 0, enforced by the SY of the named YT. | ActionMiscV3.sol:121-126,165-170,314-332; ActionBase.sol:107 |
| V2: each swap's minimum binds. The amount swapped is what the named contracts report, so it is not shown. | ActionMiscV3.sol:144-163,172-174,334-346,369-370 |
| Device concern: Ledger Flex and Stax show multi-field tuple arrays by field (`ARRAY_ORDER_PORTABILITY`), so the per-swap and per-YT pairing may be lost there. | strict-portability check |

**Tests**
- 46 cases: 43 real mainnet transactions and 3 encoded. New: `swapTokensToTokens` `0x808f19e46a8c480bfd0bbe61989de273ddf54d3f753f87c09376784086e9e6cf` (1 swap), `0x253209b2cc0f3f10adcb65eb291f74bef2f4fb574a7890e357492d07eb9a4316` (4 swaps to ETH), `0x7e619800e32aac2f836baebd0f878be5dc591b1bd98b0ca59e9b606a64064e50` (ETH in); `redeemDueInterestAndRewardsV2` `0xd5911ceb6973ff13ae5d5cd5fb9ab3ae3af5710a9ff9262608e45b35f0bcca78`; multicalls `0x6fdfc8cbfc2b6b025ddf5f3035fd55a9a5e4e120c9a717d2b4931be401f0e274`, `0x4b678dff86d212d5c5d8e6a9b2e7afbe3b8bd198d9436db3cf014a5f2eaec65c`, `0xbd63b85e79c8a3ca9ddd613a94a79643a6d119c1dc6d1e5765b891480db18d90` and `0xc7960e20aade8bcdadf8926cea1442456cd71ad1f0231ba6d9db56c8ad427d9d` (V2 with 4 YTs and 1 market). The nested multicall cases are now in the testsv2 file with their nested `interpolatedIntent`, as the test schema allows.
- One encoded V2 call with a reward swap (PENDLE to at least 10 USDC): HyperSync scans of all 85,651 direct V2 calls and 210,864 multicalls since the router's deployment found no V2 call with a non-empty `swaps` array.
- The expected screens of the 36 existing cases with PT, YT or SY amounts were regenerated. Token metadata in the data provider was read from the chain.

**Checks**
- Lint at the registry pin: 0 errors and 40 warnings (37 "Unknown selector" because the linter fetches the proxy-only ABI, 1 intent too long, and "Unresolved map reference" because the linter cannot resolve maps). Map fields also carry `nativeCurrencyAddress: ["0x0000000000000000000000000000000000000000"]`, which has no effect on rendering (no map value is the zero address); it works around the linter rejecting the empty parameters that remain after it drops the map.
- Schema and index: pass, including the registry's synced spec (#3180).
- Sourcify runner `9d6d2fe4`: 46/46. It follows the spec rule for a missing key: a market not in the map gives `INVALID_DESCRIPTOR`.
- Rust runner `65af2281`: cannot run this file. It rejects a nested `interpolatedIntent` in the test file (cs-test/src/schema.rs:93-101), and it does not parse spec map references (`FormatParams.token` is a string, types/display.rs:386-387; its own map model uses `entries` and `mapReference`, types/metadata.rs:66-76). With both removed in a scratch copy, the 19 cases without map amounts pass, including every new case. The expected values follow the spec.
- The descriptor is 392 KB, the largest in the registry. The scripts that build and refresh the maps are kept outside the registry.
- Not done: claims replay of the new cases, and device tests.

**Flags (replace 4 and 5)**
4. PT, YT and SY tickers depend on the maps. A market created after block 26,231,611 is blind until it is added.
5. The Rust runner cannot run this file (see Checks).


## Update: PT, YT and SY amounts shown raw, maps removed

Add this to the PR #3176 description. It supersedes the map parts of the update above.

- **Why:** a map lookup that finds no key makes the descriptor invalid for that transaction (spec, "metadata.maps": "In case no values matches the wallet MUST consider the 7730 file invalid for the transaction"). Pendle creates new markets often (37 in 90 days), so each new market was blind until someone refreshed the maps.
- **Change:** the 35 PT, YT and SY amounts that used the maps now use the `raw` format, with "(raw)" in the label and the sentence, for example "Sell {exactPtIn} PT (raw) of {market} for at least {minSyOut} SY (raw) to {receiver}". The market stays visible by address. The four maps and the `nativeCurrencyAddress` workaround are removed. Amounts whose token is in the calldata keep `tokenAmount`: LP via `market`, PT and YT via `YT`, and the input and output tokens. `swapTokensToTokens` and `redeemDueInterestAndRewardsV2` are unchanged.
- **Size:** the descriptor is 115 KB instead of 392 KB.
- **Tests:** 41 cases in the testsv2 file. The 5 multicall cases with a nested `interpolatedIntent` are kept outside the file, as in the other PRs: `0x93dd22f2af45c7b331387b6292d869565934d1160013619c0ac89b133edd3fc0`, `0x6fdfc8cbfc2b6b025ddf5f3035fd55a9a5e4e120c9a717d2b4931be401f0e274`, `0x4b678dff86d212d5c5d8e6a9b2e7afbe3b8bd198d9436db3cf014a5f2eaec65c`, `0xbd63b85e79c8a3ca9ddd613a94a79643a6d119c1dc6d1e5765b891480db18d90` and `0xc7960e20aade8bcdadf8926cea1442456cd71ad1f0231ba6d9db56c8ad427d9d`.
- **Checks:** lint 0 errors (the "Unresolved map reference" warning is gone), schema and index pass, Sourcify runner 41/41, Rust runner 41/41. The Rust runner can run this file again.
