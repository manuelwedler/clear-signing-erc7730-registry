# Fixes for the PR descriptions (#3171 to #3176)

To apply in one pass with the external agent. Use the latest commit of `claude/nifty-euler-gwsa66` at that time if any linked file changed after this list was written.

## 1. Link to a commit, not to a branch (all PRs)

Each description links its spec-limitation notes through the branch `claude/nifty-euler-gwsa66`, which may be deleted later. Replace every link of the form `https://github.com/manuelwedler/clear-signing-erc7730-registry/blob/claude/nifty-euler-gwsa66/<path>` with a permalink to a commit. At commit `cba3b04`, the links are:

| PR | Contract | Permalink |
|---|---|---|
| #3171 | SwftSwap | https://github.com/manuelwedler/clear-signing-erc7730-registry/blob/cba3b043e26b3e3691e98e2332f347f760b21e48/docs/spec-limitations/swft-SwftSwap.md |
| #3172 | Blast portal | https://github.com/manuelwedler/clear-signing-erc7730-registry/blob/cba3b043e26b3e3691e98e2332f347f760b21e48/docs/spec-limitations/blast-OptimismPortal.md |
| #3173 | Across SpokePool | https://github.com/manuelwedler/clear-signing-erc7730-registry/blob/cba3b043e26b3e3691e98e2332f347f760b21e48/docs/spec-limitations/across-Ethereum_SpokePool.md |
| #3174 | Base portal | https://github.com/manuelwedler/clear-signing-erc7730-registry/blob/cba3b043e26b3e3691e98e2332f347f760b21e48/docs/spec-limitations/base-OptimismPortal2.md |
| #3175 | Uniswap V3 NPM | https://github.com/manuelwedler/clear-signing-erc7730-registry/blob/cba3b043e26b3e3691e98e2332f347f760b21e48/docs/spec-limitations/uniswap-UniswapV3NonfungiblePositionManager.md |
| #3176 | Pendle RouterV4 | https://github.com/manuelwedler/clear-signing-erc7730-registry/blob/cba3b043e26b3e3691e98e2332f347f760b21e48/docs/spec-limitations/pendle-PendleRouterV4.md |

Apply the same rule to any other link into the fork in the descriptions.

## 2. Add the embedded-calls updates (#3172 to #3176)

- #3176: replace the whole description with `docs/top-contracts/pendle-PendleRouterV4.md`.
- #3172, #3173, #3174, #3175: apply the "Update: embedded calls" section at the end of each report in `docs/top-contracts/`. It supersedes the older text it names, such as the Base "Tool limitation" line about the `calldata` format.

## 3. SwftSwap (#3171): state the trust assumption with a constant field

This needs a descriptor change, not only a description change.

- **Descriptor:** add a field with a literal `value` and no `path` to both `swap` and `swapEth`, as the first field. The spec allows a literal `value` instead of a `path` "to display a constant" (ERC-7730, field format specification, `path` / `value`):
  ```json
  { "label": "Note", "value": "Paid out off-chain by SWFT. The minimum is not enforced on-chain.", "format": "raw" }
  ```
  A trial on a scratch copy showed that both registry runners render it the same way, as the first field. The pinned linter reports 0 errors for it.
- **Tests:** update the expected fields of all 9 cases in `registry/swft/testsv2/calldata-SwftSwap.tests.json`, then re-run both runners and the full CI check.
- **Spec-limitation notes:** remove the section "No way to state that a value is a request the contract does not enforce" from `docs/spec-limitations/swft-SwftSwap.md`. The spec can express it. Then regenerate the permalinks of item 1 for the new commit.
- **PR description:** in "What the screens say", add that the screen now shows the note, and remove the claim that the trust assumption is stated only for reviewers.
- **Push:** the descriptor and test change go to `claude/nifty-euler-gwsa66-swft`, which updates PR #3171, and to `claude/nifty-euler-gwsa66`.
