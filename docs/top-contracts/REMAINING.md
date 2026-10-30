# Remaining work (state of 2026-10-30)

## Pull requests

| Contract | PR | State |
|---|---|---|
| SwftSwap | https://github.com/ethereum/clear-signing-erc7730-registry/pull/3171 | merged |
| Uniswap V3 NPM | https://github.com/ethereum/clear-signing-erc7730-registry/pull/3175 | merged |
| Blast OptimismPortal | https://github.com/ethereum/clear-signing-erc7730-registry/pull/3172 | open, changes requested (2 changes, 5 suggestions) |
| Across SpokePool | https://github.com/ethereum/clear-signing-erc7730-registry/pull/3173 | open, changes requested (1 change, 3 suggestions) |
| Base OptimismPortal2 | https://github.com/ethereum/clear-signing-erc7730-registry/pull/3174 | open, changes requested (2 changes, 3 suggestions) |
| Pendle RouterV4 | https://github.com/ethereum/clear-signing-erc7730-registry/pull/3176 | open, commented (2 suggestions) |

Each open PR's head is the branch `claude/nifty-euler-gwsa66-<entity>` on the fork. The common branch `claude/nifty-euler-gwsa66` holds the same registry files plus these docs. The reviewer is marcocastignoli; approval stays with a maintainer.

## Now: review round 1 on the four open PRs

- One agent per PR addresses every review thread, the required changes and the suggestions, checks each claim against the verified source, re-runs the registry checks and pushes to the PR branch.
- After the agents report: copy `registry/<entity>` to the common branch, append an "Update: review round 1" section to each report, and write `REVIEW-ROUND-1.md` with one reply per thread and the description changes.
- Then the local agent with GitHub rights: post the replies, resolve the threads that are fixed, update the four PR descriptions (fix list items in `PR-BODY-FIXES.md`), and re-request the review.

## Open items after that

- **Scripts:** `verify-entity.sh`, `regen-expected.py`, `rlp_swap.py` and the HyperSync query scripts live only in this session's scratch folder. Put them in a tools folder of the fork if they are still needed after the PRs merge.
- **Wishlist question for the user:** a map fallback (for example `"onMissing": "raw"`), so that Pendle could use ticker maps again and a market missing from the map renders raw instead of blind. Not added; the user decides what goes on the wishlist.
- **Across:** `chainIdPath` is written as `#.destinationChainId` because the old linter did not resolve a relative path. Check whether the linter at `ccd51ad` resolves `destinationChainId`; if it does, the relative form is the simpler one.
- **General tooling, not needed by our PRs:** spec map references in the Rust runner and the linter (python-erc7730 drops them, also in its Ledger conversion). Check whether the fixes of 2026-10-29 covered them.
- **Pendle:** PT, YT and SY amounts are raw because the calldata names only the market. A spec change (`tokenFrom`, see the spec-limitation note) or the map fallback above would give them tickers.

## Decisions that hold

- Mainnet focus; no new deployments on other chains (the BNB Chain SwftSwap deployment was added because the bytecode is identical and the contract is now verified).
- Every spec feature is used where it fits; tool bugs are fixed or reported, not hidden.
- Embedded calls use the `calldata` format everywhere, with `chainId` where the call runs on another chain.
- `addressName` and `tokenTicker` on `bytes32` only when the value is always an EVM address.
- Pendle keeps the aggregator route data hidden. Uniswap keeps the `@.value` pins on ETH-paying multicalls. Pendle PT, YT and SY amounts are raw (maps removed: a missing key makes the descriptor invalid, and Pendle creates markets often).
- The spec wishlist only gets items the user approves. It was filed as an issue in the registry repository, not in ethereum/ERCs.

## Done

- 2026-10-28: six descriptors built with clear-signing-helper plus hand-written spec features; six draft PRs opened.
- 2026-10-29: embedded calls described with `calldata`; L2 contracts added for Base (L2ToL1MessagePasser) and Blast (L2ToL1MessagePasser, Airdrop, AirdropVesting); `chainId` in `calldata` adopted after ethereum/ERCs PR 2124 and registry #3180; Pendle maps removed; SwftSwap verified on Sourcify for chain 56 and the deployment added; PR descriptions rewritten with commit permalinks and the PRs marked ready; the wishlist issue and the clear-signing-helper issue opened (`SPEC-WISHLIST.md`, `HELPER-IMPROVEMENTS.md`).
- 2026-10-29: tooling fixed upstream and the registry pins bumped in #3182 (linter `ccd51ad`, Rust runner `8bfe6b49`, Sourcify runner `277965de` with library 0.3.1). This covered the nested `interpolatedIntent` in test files, `chainId` in `calldata` for the linter, address formats on `bytes32` in the Sourcify library, the empty byte slice in the Rust runner, and the chain names. The nested-call test cases from `nested-tests/` are now in the Base, Blast and Pendle test files. All four open PRs pass every registry check.
- 2026-10-30: #3171 and #3175 merged.

## Local tooling of this session

- Full check: `REPO=<worktree> verify-entity.sh <entity> <Name>...` runs the pinned lint, the schema check, both runners (`/root/.cache/clear-signing-helper/runners/rust-8bfe6b49`, `sourcify-277965de`) and the index check.
- Worktrees `wt-<entity>` per PR branch, under the scratch folder `work/`.
