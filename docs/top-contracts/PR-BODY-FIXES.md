# Fixes for the PR descriptions (#3171 to #3176)

To apply in one pass with the external agent. Use the latest commit of `claude/nifty-euler-gwsa66` at that time if any linked file changed after this list was written.

## 1. Link to a commit, not to a branch (all PRs)

Each description links its spec-limitation notes through the branch `claude/nifty-euler-gwsa66`, which may be deleted later. Replace every link of the form `https://github.com/manuelwedler/clear-signing-erc7730-registry/blob/claude/nifty-euler-gwsa66/<path>` with a permalink to a commit. At commit `ca1df7c`, the links are:

| PR | Contract | Permalink |
|---|---|---|
| #3171 | SwftSwap | https://github.com/manuelwedler/clear-signing-erc7730-registry/blob/ca1df7c4c06f7ce6acf1f5460633428f45b30d0d/docs/spec-limitations/swft-SwftSwap.md |
| #3172 | Blast portal | https://github.com/manuelwedler/clear-signing-erc7730-registry/blob/ca1df7c4c06f7ce6acf1f5460633428f45b30d0d/docs/spec-limitations/blast-OptimismPortal.md |
| #3173 | Across SpokePool | https://github.com/manuelwedler/clear-signing-erc7730-registry/blob/ca1df7c4c06f7ce6acf1f5460633428f45b30d0d/docs/spec-limitations/across-Ethereum_SpokePool.md |
| #3174 | Base portal | https://github.com/manuelwedler/clear-signing-erc7730-registry/blob/ca1df7c4c06f7ce6acf1f5460633428f45b30d0d/docs/spec-limitations/base-OptimismPortal2.md |
| #3175 | Uniswap V3 NPM | https://github.com/manuelwedler/clear-signing-erc7730-registry/blob/ca1df7c4c06f7ce6acf1f5460633428f45b30d0d/docs/spec-limitations/uniswap-UniswapV3NonfungiblePositionManager.md |
| #3176 | Pendle RouterV4 | https://github.com/manuelwedler/clear-signing-erc7730-registry/blob/ca1df7c4c06f7ce6acf1f5460633428f45b30d0d/docs/spec-limitations/pendle-PendleRouterV4.md |

Apply the same rule to any other link into the fork in the descriptions.

## 2. Add the embedded-calls updates (#3172 to #3176)

- #3176: replace the whole description with `docs/top-contracts/pendle-PendleRouterV4.md`.
- #3172, #3173, #3174, #3175: apply the "Update: embedded calls" section at the end of each report in `docs/top-contracts/`. It supersedes the older text it names, such as the Base "Tool limitation" line about the `calldata` format.

## 3. SwftSwap (#3171): state the trust assumption with a constant field

Done in the code and in the docs; only the PR description is left.

- **Done:** both `swap` and `swapEth` now open with `{ "label": "Note", "value": "Paid out off-chain by SWFT. The minimum is not enforced on-chain.", "format": "raw" }`. The 9 test expectations are updated, and the full CI check passes. Pushed to `claude/nifty-euler-gwsa66-swft`, so PR #3171 already shows it.
- **Done:** the section "No way to state that a value is a request the contract does not enforce" is removed from `docs/spec-limitations/swft-SwftSwap.md`.
- **Done:** `docs/top-contracts/swft-SwftSwap.md` describes the Note field (Summary, Coverage table, "What the screens say" item 9, Tests, Checks).
- **To do:** replace the description of PR #3171 with the updated `docs/top-contracts/swft-SwftSwap.md`, using the permalinks of item 1. The current description still lists the removed limitation.
