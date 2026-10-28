# Pendle RouterV4: clear-signing descriptor (mainnet)

> **Draft.** This descriptor was written for the registry's top-contracts effort. It was **not** submitted by the Pendle team. A language-model agent made the judgment choices with clear-signing-helper 0.6.0-preview.6. No human has reviewed it yet. The agent was stopped before it wrote its full report, so this short report was written from its files and the helper's records.

## Summary

- Descriptor `registry/pendle/calldata-PendleRouterV4.json` for the Pendle RouterV4 proxy `0x888888888889758F76e7103c6CbF23ABbF58F946` on Ethereum. Other chains were out of scope.
- 34 user functions are described: swaps between token, SY, PT and YT, liquidity add and remove, mint and redeem of SY and PY, exits before and after expiry, reward claims, `boostMarkets` and `requestBurnQuota`.
- 20 functions are excluded with a reason. See "Coverage".

## The key question from the handoff

The handoff asked whether the router checks the final output against the shown minimum after an aggregator swap in `TokenInput.swapData`. The agent concluded that it does. The router pulls exactly `netTokenIn` of `tokenIn` (ActionBase.sol lines 35, 38, 51) and checks the final output against the minimum. So the aggregator route fields are hidden with that reason, and the screens say "at least" for the minimum.

## Coverage

- **Pinned with `mustMatch`:**
  - `output.swapData.swapType` is pinned to `0` (no swap) on the outputs. A swap after the router's check would make "at least" false for the token the receiver gets.
  - `limit.limitRouter` is pinned to the zero address. Calls that fill Pendle limit orders are not clear-signed.
- **Hidden with a reason:** aggregator route data, approximation search hints (`ApproxParams`), and limit-order fields. Each reason says why the minimum still holds.
- **Excluded:** `multicall`, `callAndReflect` and `simulate` (nested or simulation calls), the `*Simple` internal entry points, the market and limit-router callbacks, owner-only facet administration, `fallback`, `redeemDueInterestAndRewardsV2` and `swapTokensToTokens`. The last two hold minimums inside multi-field tuple arrays, which strict portability rejects because a device could pair an amount with the wrong minimum.
- **Known gap:** PT, YT, SY and LP amounts are raw, labelled "(raw)", where the token is not an argument. See the spec-limitation notes.

## Tests

35 cases. 33 are real mainnet transactions with `txHash`. 2 are encoded.

## Checks

| Check | Result |
|---|---|
| Lint at the CI pin | 0 errors, 36 warnings (intent length and missing formats for excluded functions) |
| Schema and index | pass |
| Sourcify runner | 35 of 35 |
| Rust runner | 35 of 35 |
| Strict portability | pass |

**Claims replay is partial.** It ran on 30 of 36 fixtures with 0 findings. These six did not finish because the RPC endpoint failed or the agent was stopped: `addLiquiditySingleSyKeepYt`, `addLiquiditySingleTokenKeepYt`, `redeemPyToSy`, `removeLiquidityDualTokenAndPt`, `removeLiquiditySingleSy`, `swapExactPtForToken-limit`.
