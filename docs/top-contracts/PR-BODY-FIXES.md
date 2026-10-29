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
