# Remaining work (stopped on 2026-10-28 to save tokens)

## Pendle RouterV4
- The claims replay did not finish for 6 of 36 fixtures: `addLiquiditySingleSyKeepYt`, `addLiquiditySingleTokenKeepYt`, `redeemPyToSy`, `removeLiquidityDualTokenAndPt`, `removeLiquiditySingleSy`, `swapExactPtForToken-limit`. Run `clear-signing claims --fixture <file>` for each against an endpoint with historical state.
- The full report was not written. `pendle-PendleRouterV4.md` is a short version. Expand it with the source lines for each judgment call, as in the other reports.
- Review the two `mustMatch` pins (`output.swapData.swapType`, `limit.limitRouter`) and the conclusion that the router checks the final output after aggregator swaps.

## Upstream draft pull requests
- Not opened from this session: the upstream repository has the same name as the fork, so it cannot be attached here. One branch per contract is on the fork, ready to open: `claude/nifty-euler-gwsa66-<entity>` for swft, blast, across, base, uniswap and pendle.
- Use the matching file in this folder as the pull request description.

## Smaller follow-ups
- SwftSwap on BNB Chain (56): identical bytecode but not verified on Sourcify. Verify it, then add the deployment.
- Uniswap V3 NPM: `mint` hides its tick range to pass strict portability. Decide if this is acceptable or if `mint` should be excluded.
