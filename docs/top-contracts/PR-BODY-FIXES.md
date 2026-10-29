# Fixes for the PR descriptions (#3171 to #3176)

To apply in one pass with the external agent. Use the latest commit of `claude/nifty-euler-gwsa66` at that time if any linked file changed after this list was written.

## 1. Link to a commit, not to a branch (all PRs)

Each description links its spec-limitation notes through the branch `claude/nifty-euler-gwsa66`, which may be deleted later. Replace every link of the form `https://github.com/manuelwedler/clear-signing-erc7730-registry/blob/claude/nifty-euler-gwsa66/<path>` with a permalink to a commit. At commit `8f79208`, the links are:

| PR | Contract | Permalink |
|---|---|---|
| #3171 | SwftSwap | https://github.com/manuelwedler/clear-signing-erc7730-registry/blob/8f792084b861829bbc2340bc6542b36b5002f20e/docs/spec-limitations/swft-SwftSwap.md |
| #3172 | Blast portal | https://github.com/manuelwedler/clear-signing-erc7730-registry/blob/8f792084b861829bbc2340bc6542b36b5002f20e/docs/spec-limitations/blast-OptimismPortal.md |
| #3173 | Across SpokePool | https://github.com/manuelwedler/clear-signing-erc7730-registry/blob/8f792084b861829bbc2340bc6542b36b5002f20e/docs/spec-limitations/across-Ethereum_SpokePool.md |
| #3174 | Base portal | https://github.com/manuelwedler/clear-signing-erc7730-registry/blob/8f792084b861829bbc2340bc6542b36b5002f20e/docs/spec-limitations/base-OptimismPortal2.md |
| #3175 | Uniswap V3 NPM | https://github.com/manuelwedler/clear-signing-erc7730-registry/blob/8f792084b861829bbc2340bc6542b36b5002f20e/docs/spec-limitations/uniswap-UniswapV3NonfungiblePositionManager.md |
| #3176 | Pendle RouterV4 | https://github.com/manuelwedler/clear-signing-erc7730-registry/blob/8f792084b861829bbc2340bc6542b36b5002f20e/docs/spec-limitations/pendle-PendleRouterV4.md |

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

## 4. SwftSwap (#3171): raw label for the requested minimum

Done in the code and in the docs; only the PR description is left.

- **Done:** the `minReturnAmount` field is now labelled "Requested Min (raw)", and the sentence reads "… requested minimum {minReturnAmount} (raw units)". This tells the signer that the number is unscaled. It matches the "(raw)" labels in #3173 and #3175. The 9 test expectations are updated, and the full CI check passes. Pushed to `claude/nifty-euler-gwsa66-swft`, so PR #3171 already shows it.
- **Done:** `docs/top-contracts/swft-SwftSwap.md` (Summary, Coverage table, interpolated intents, "What the screens say" item 4) and `docs/spec-limitations/swft-SwftSwap.md` (workaround line) use the new label.
- **To do:** the PR #3171 description still names the old label "Requested Minimum". Replacing the description as in item 3 covers this.

## 5. Base (#3174) and Blast (#3172): gas unit and aliasing note

Done in the code and in the docs; only the PR descriptions are left.

- **Done:** `depositTransaction._gasLimit` uses the `unit` format with `base: "gas"` instead of `raw`. `depositTransaction` opens with a constant Note field about the L1-to-L2 address alias for contract-wallet signers. Tests are updated and the full CI check passes. Pushed to both PR branches, so the PRs already show it.
- **Done:** the reports end with an "Update: gas unit and aliasing note on `depositTransaction`" section. The aliasing sections of `docs/spec-limitations/base-OptimismPortal2.md` and `docs/spec-limitations/blast-OptimismPortal.md` name the new workaround.
- **To do:** add that update section to the descriptions of #3174 and #3172, together with item 2, and use the permalinks of item 1.

## 6. Base (#3174), Blast (#3172) and Uniswap (#3175): features now implemented

Done in the code and in the docs; only the PR descriptions are left.

- **Done:** Base and Blast decode `depositTransaction._data` and `sendMessage._message` with the `calldata` format and `chainId`. Base drops the `_data` pin, and Blast pins `_isCreation`. Blast shows the `_extraData` DAI minimum. Uniswap shows the `mint` ticks. All pushed to the PR branches.
- **Done:** each report ends with a new "Update" section ("L2 calls decoded with `chainId`" for Base and Blast, "`mint` tick range shown" for Uniswap). The spec-limitation notes have new workaround lines (Base: cross-chain calldata and aliasing; Blast: cross-chain calldata and the bytes argument; Uniswap: price ranges given as ticks).
- **To do:** add those update sections to the three descriptions, together with items 2 and 5, and use the permalinks of item 1. The Base and Blast descriptions must say that schema validation and lint fail on `chainId` until the schema change is released, and Blast must name the two Rust runner failures.

## 7. Across (#3173): chain names and destination amount

Done in the code and in the docs; only the PR description is left.

- **Done:** `destinationChainId` uses the `chainId` format, and `outputAmount` is a `tokenAmount` on the destination chain, labelled "Relayer Must Send". Pushed to `claude/nifty-euler-gwsa66-across`.
- **Done:** the report ends with "Update: destination chain names and destination amount". The spec-limitation notes have a new body for "Output amount denominated in a token on another chain" and a new section "Chain id named from a registry that does not match the protocol's ids".
- **To do:** add the update section to the #3173 description, together with item 2, and use the permalinks of item 1. It must name the three Rust runner failures.

