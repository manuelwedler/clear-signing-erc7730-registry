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
- **Features that were avoided because of a library or device limit are now implemented (2026-10-29):**
  - Base #3174 and Blast #3172: L2 calls use the `calldata` format with `chainId`. Registry schema validation and lint fail on these fields until the ERC-7730 schema change (2.2.0) and the linter change are released.
  - Blast #3172: `_extraData` is a DAI `tokenAmount` slice. The Rust runner fails two cases on empty data (`<unresolved>`); fix the runner.
  - Uniswap #3175: the `mint` ticks are shown. Both runners render them correctly.
  - Across #3173: `destinationChainId` uses the `chainId` format plus an override enum for 14 ids, `outputAmount` and the output token use the destination chain, and the bytes32 depositor uses `addressName`. The Sourcify runner fails seven cases (address formats on bytes32).
  - Pendle #3176 (maps, `swapTokensToTokens`, `redeemDueInterestAndRewardsV2`): in progress.
  - All: clear-signing-helper does not support the `calldata` format, so those fields are added by hand.
- **Expected CI state:** Base and Blast will show schema and lint errors on `chainId`, and Blast will show two Rust runner failures, until the items above are fixed upstream. Everything else should pass.
- **Rust runner bugs to fix (found 2026-10-29):** its chain-name table has 16 entries and shows other chains as "Chain <id>" (render_shared.rs line 18); a chain id above 64 bits shows "Chain 0" and resolves the token on the signing chain (engine.rs lines 2307-2334); the byte-slice and nested `interpolatedIntent` gaps listed above.
- **Linter bug to report or fix (sourcifyeth/python-erc7730 at 964176e):** `resolve_token_amount_parameters` does not resolve a relative `chainIdPath` (parameters.py lines 219 and 285), so `"chainIdPath": "destinationChainId"` gives false errors. Across uses `#.destinationChainId` until it is fixed.
- **Across chain id 999: resolved.** An override enum names 999 "HyperEVM" and Solana "Solana", and also the ids the Rust runner cannot name.

## To do at the end: tooling must accept address formats on `bytes32`
- ERC-7730 tooling should allow `addressName` and `tokenTicker` on a `bytes32` value that holds an EVM address in its low 20 bytes. Across #3173 already uses this for the bytes32 `depositor` and `outputToken`.
- **Sourcify runner / `@ethereum-sourcify/clear-signing`:** rejects it with `ARGUMENT_TYPE_MISMATCH: "Format addressName expects address but got bytes"` (dist/index.js lines 993-995 and 1133-1141) and shows the raw 32 bytes. Fix the library, then bump the runner pin.
- **Linter and schema:** they accept it today; check again after any linter update.
- **Rust runner:** accepts it.

