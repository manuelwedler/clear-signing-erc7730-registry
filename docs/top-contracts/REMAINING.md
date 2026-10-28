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
