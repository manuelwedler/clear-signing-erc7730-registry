# Remaining work (stopped on 2026-10-28 to save tokens)

## Pendle RouterV4
- The claims replay did not finish for 6 of 36 fixtures: `addLiquiditySingleSyKeepYt`, `addLiquiditySingleTokenKeepYt`, `redeemPyToSy`, `removeLiquidityDualTokenAndPt`, `removeLiquiditySingleSy`, `swapExactPtForToken-limit`. Run `clear-signing claims --fixture <file>` for each against an endpoint with historical state.
- The full report was not written. `pendle-PendleRouterV4.md` is a short version. Expand it with the source lines for each judgment call, as in the other reports.
- Review the two `mustMatch` pins (`output.swapData.swapType`, `limit.limitRouter`) and the conclusion that the router checks the final output after aggregator swaps.

## Upstream draft pull requests (opened 2026-10-28)

| Contract | PR |
|---|---|
| SwftSwap | https://github.com/ethereum/clear-signing-erc7730-registry/pull/3171 |
| Blast OptimismPortal | https://github.com/ethereum/clear-signing-erc7730-registry/pull/3172 |
| Across SpokePool | https://github.com/ethereum/clear-signing-erc7730-registry/pull/3173 |
| Base OptimismPortal2 | https://github.com/ethereum/clear-signing-erc7730-registry/pull/3174 |
| Uniswap V3 NPM | https://github.com/ethereum/clear-signing-erc7730-registry/pull/3175 |
| Pendle RouterV4 | https://github.com/ethereum/clear-signing-erc7730-registry/pull/3176 |

Each PR head is the branch `claude/nifty-euler-gwsa66-<entity>` on the fork. A push to that branch updates the PR. The PR description must be edited by hand.

## Smaller follow-ups
- SwftSwap on BNB Chain (56): identical bytecode but not verified on Sourcify. Verify it, then add the deployment.
- Uniswap V3 NPM: `mint` hides its tick range to pass strict portability. Decide if this is acceptable or if `mint` should be excluded.
