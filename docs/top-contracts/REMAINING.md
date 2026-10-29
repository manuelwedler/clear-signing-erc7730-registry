# Remaining work (stopped on 2026-10-28 to save tokens)

## Pendle RouterV4
- Done: all 36 fixtures are accounted for in the claims replay (0 findings), the full report is written, and the two pins and the aggregator check are confirmed with source lines.

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
- Runner conflict: a nested call whose inner format has an `interpolatedIntent` cannot pass both runners (Sourcify requires the nested `interpolatedIntent`, the Rust runner rejects it). Real nested test cases are kept outside the testsv2 files. Report this to the runner maintainers.
- Uniswap V3 NPM: `mint` hides its tick range to pass strict portability. Decide if this is acceptable or if `mint` should be excluded.

## Embedded calls (`calldata` format), added 2026-10-28
- Done on PRs 3172 (Blast), 3173 (Across), 3174 (Base), 3175 (Uniswap) and 3176 (Pendle). SwftSwap has no embedded calls.
- Each report in this folder ends with an "Update: embedded calls" section, or for Pendle a full new report. Paste it into the PR description by hand.
- Real nested-call test cases are kept outside the testsv2 files because of the runner conflict (see above). Their txHashes are listed in each update section.
- The v2 schema has no `chainId` for embedded calldata, although the spec text lists it. Deposit call data that runs on L2 cannot be described. Report this to the spec and schema maintainers.

## Open decisions for the user
- Blast shows deposit call data raw. Base pins it out with `mustMatch ["0x"]`. Pick one approach for both.
- Pendle: the aggregator route data has the `calldata` format but stays hidden. `visible: "optional"` would show it and passes both runners.
- Uniswap: ETH-paying multicalls stay blind because of the `@.value` pins. Keep them, or drop the pins with a sentence about refundETH.

## To do: runners and library limits (added 2026-10-29)
- **Fix the Rust runner ourselves when registry CI fails on it.** Two known gaps: it renders a byte slice past the end of the data as `<unresolved>` where the Sourcify runner renders 0 (Blast `_extraData.[0:32]`), and its `NestedExpected` rejects a nested `interpolatedIntent` that the Sourcify runner requires.
- **Revisit features that were avoided because of a library or device limit, not the spec:**
  - Across #3173: the destination chain is an enum instead of the spec's `chainId` format, because the two runners disagree on chain names. `outputAmount` is raw instead of `tokenAmount` with `chainIdPath: destinationChainId`, because the spec has no normative fallback for an unknown token on another chain.
  - Uniswap #3175: the `mint` ticks are hidden, because the pinned runners misrender negative signed integers (strict portability).
  - Blast #3172: `_extraData` is raw instead of a `tokenAmount` slice, because the runners disagree on empty bytes (see wishlist item 3).
  - Pendle #3176: `swapTokensToTokens` and `redeemDueInterestAndRewardsV2` are excluded because strict portability rejects multi-field tuple arrays on Ledger devices.
  - All: clear-signing-helper does not support the `calldata` format, so those fields were added by hand. Nothing was dropped for that reason.
- **Decide on maps for Pendle #3176:** a map from market address to its PT, YT and SY token would let PT, YT and SY amounts show with tickers instead of raw. The trade-off: a market missing from the map makes the descriptor invalid for that transaction, so every new market would be blind until the map is updated.

