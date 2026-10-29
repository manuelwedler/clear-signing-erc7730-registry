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

## Embedded calls (`calldata` format), added 2026-10-28
- Done on PRs 3172 (Blast), 3173 (Across), 3174 (Base), 3175 (Uniswap) and 3176 (Pendle). SwftSwap has no embedded calls.
- Each report in this folder ends with an "Update: embedded calls" section, or for Pendle a full new report. Paste it into the PR description by hand.
- Real nested-call test cases are kept outside the testsv2 files because of the runner conflict (see above). Their txHashes are listed in each update section.
- Base and Blast also describe their L2ToL1MessagePasser (and Blast its airdrop contracts), so L2 calls and L1 calls are decoded in both directions.

## Open decisions for the user
- Decided: Pendle keeps the aggregator route data hidden.
- Decided: Uniswap keeps the `@.value` pins on ETH-paying multicalls.

## To do: runners and library limits (added 2026-10-29)
- **Fix the Rust runner ourselves when registry CI fails on it.** Two known gaps: it renders a byte slice past the end of the data as `<unresolved>` where the Sourcify runner renders 0 (Blast `_extraData.[0:32]`), and its `NestedExpected` rejects a nested `interpolatedIntent` that the Sourcify runner requires.
- **Features that were avoided because of a library or device limit are now implemented (2026-10-29):**
  - Base #3174 and Blast #3172: L2 calls use the `calldata` format with `chainId`. Schema validation passes since the registry synced the spec (#3180); lint fails on these fields until the linter change is released.
  - Blast #3172: `_extraData` is a DAI `tokenAmount` slice. The Rust runner fails two cases on empty data (`<unresolved>`); fix the runner.
  - Uniswap #3175: the `mint` ticks are shown. Both runners render them correctly.
  - Across #3173: `destinationChainId` uses the `chainId` format plus an override enum for 14 ids, `outputAmount` and the output token use the destination chain, and the bytes32 depositor uses `addressName`. The Sourcify runner fails seven cases (address formats on bytes32).
  - Pendle #3176: `swapTokensToTokens` and `redeemDueInterestAndRewardsV2` described. Maps were tried and removed, because a missing key makes new markets blind. Both runners pass.
  - All: clear-signing-helper does not support the `calldata` format, so those fields are added by hand.
- **Expected CI state:** Base and Blast show lint errors on `chainId` until the linter is updated, Blast shows two Rust runner failures, and Across shows seven Sourcify runner failures (address formats on bytes32). Everything else should pass.
- **Rust runner bugs to fix (found 2026-10-29):** its chain-name table has 16 entries and shows other chains as "Chain <id>" (render_shared.rs line 18); a chain id above 64 bits shows "Chain 0" and resolves the token on the signing chain (engine.rs lines 2307-2334); the byte-slice and nested `interpolatedIntent` gaps listed above.
- **Linter bug to report or fix (sourcifyeth/python-erc7730 at 964176e):** `resolve_token_amount_parameters` does not resolve a relative `chainIdPath` (parameters.py lines 219 and 285), so `"chainIdPath": "destinationChainId"` gives false errors. Across uses `#.destinationChainId` until it is fixed.
- **Across chain id 999: resolved.** An override enum names 999 "HyperEVM" and Solana "Solana", and also the ids the Rust runner cannot name.

## To do at the end: tooling must accept address formats on `bytes32`
- ERC-7730 tooling should allow `addressName` and `tokenTicker` on a `bytes32` value that holds an EVM address in its low 20 bytes. Across #3173 already uses this for the bytes32 `depositor` and `outputToken`.
- **Sourcify runner / `@ethereum-sourcify/clear-signing`:** rejects it with `ARGUMENT_TYPE_MISMATCH: "Format addressName expects address but got bytes"` (dist/index.js lines 993-995 and 1133-1141) and shows the raw 32 bytes. Fix the library, then bump the runner pin.
- **Linter and schema:** they accept it today; check again after any linter update.
- **Rust runner:** accepts it.

## ERC-7730 `chainId` in `calldata` (ethereum/ERCs PR 2124)
- The schema change is in ethereum/ERCs PR 2124 and was synced into the registry by #3180 (2026-10-29). The common branch and all six PR branches include upstream master with that sync, so schema validation passes.
- **To do:** the registry linter (sourcifyeth/python-erc7730) must accept `chainId` / `chainIdPath` in the `calldata` parameters. Until then, lint reports two errors per `chainId` field in the Base and Blast descriptors. After the linter change, bump the linter pin in the registry.
- Done: the registry synced `specs/` from ethereum/ERCs with the change (#3180).

## To do: Pendle maps and tooling (added 2026-10-29)
- Done: the Pendle maps are removed (new markets were blind until a refresh). PT, YT and SY amounts are raw.
- **Rust runner:** support spec map references in `tokenAmount` `token` (general fix; no PR of ours uses maps now) (it expects a string and its own `entries`/`mapReference` map model), in addition to the nested `interpolatedIntent` gap.
- **Linter (python-erc7730):** resolve map references instead of dropping them ("Unresolved map reference ... will be dropped"). Its Ledger conversion also drops map references. No PR of ours uses maps any more, so this is a general fix.

