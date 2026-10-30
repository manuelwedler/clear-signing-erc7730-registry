# Fixes for the PR descriptions (#3171 to #3176)

To apply in one pass with the external agent. Use the latest commit of `claude/nifty-euler-gwsa66` at that time if any linked file changed after this list was written.

## 1. Link to a commit, not to a branch (all PRs)

Each description links its spec-limitation notes through the branch `claude/nifty-euler-gwsa66`, which may be deleted later. Replace every link of the form `https://github.com/manuelwedler/clear-signing-erc7730-registry/blob/claude/nifty-euler-gwsa66/<path>` with a permalink to a commit. At commit `a4c52f7`, the links are:

| PR | Contract | Permalink |
|---|---|---|
| #3171 | SwftSwap | https://github.com/manuelwedler/clear-signing-erc7730-registry/blob/a4c52f7a86971f5af10963ed51913b55f7914e98/docs/spec-limitations/swft-SwftSwap.md |
| #3172 | Blast portal | https://github.com/manuelwedler/clear-signing-erc7730-registry/blob/a4c52f7a86971f5af10963ed51913b55f7914e98/docs/spec-limitations/blast-OptimismPortal.md |
| #3173 | Across SpokePool | https://github.com/manuelwedler/clear-signing-erc7730-registry/blob/a4c52f7a86971f5af10963ed51913b55f7914e98/docs/spec-limitations/across-Ethereum_SpokePool.md |
| #3174 | Base portal | https://github.com/manuelwedler/clear-signing-erc7730-registry/blob/a4c52f7a86971f5af10963ed51913b55f7914e98/docs/spec-limitations/base-OptimismPortal2.md |
| #3175 | Uniswap V3 NPM | https://github.com/manuelwedler/clear-signing-erc7730-registry/blob/a4c52f7a86971f5af10963ed51913b55f7914e98/docs/spec-limitations/uniswap-UniswapV3NonfungiblePositionManager.md |
| #3176 | Pendle RouterV4 | https://github.com/manuelwedler/clear-signing-erc7730-registry/blob/a4c52f7a86971f5af10963ed51913b55f7914e98/docs/spec-limitations/pendle-PendleRouterV4.md |

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
- **To do:** add those update sections to the three descriptions, together with items 2 and 5, and use the permalinks of item 1. The Base and Blast descriptions must say that schema validation passes since the registry spec sync (#3180) and that lint fails on `chainId` until the linter is updated, and Blast must name the two Rust runner failures.

## 7. Across (#3173): chain names and destination amount

Done in the code and in the docs; only the PR description is left.

- **Done:** `destinationChainId` uses the `chainId` format, and `outputAmount` is a `tokenAmount` on the destination chain, labelled "Relayer Must Send". Pushed to `claude/nifty-euler-gwsa66-across`.
- **Done:** the report ends with "Update: destination chain names and destination amount". The spec-limitation notes have a new body for "Output amount denominated in a token on another chain" and a new section "Chain id named from a registry that does not match the protocol's ids".
- **To do:** add the update section to the #3173 description, together with item 2, and use the permalinks of item 1. It must name the three Rust runner failures.

## 8. Base (#3174) and Blast (#3172): L2 token ticker

Done in the code and in the docs; only the PR descriptions are left.

- **Done:** the "Token on Base" and "Token on Blast" fields use `tokenTicker` with the L2 chain id, and the tests hold the L2 token metadata. Pushed to both PR branches.
- **Done:** each report ends with "Update: L2 token shown as a ticker".
- **To do:** add that update section to the #3174 and #3172 descriptions, together with items 2, 5 and 6.

## 9. Across (#3173): chain-name overrides, output token, depositor, tagged deposits

Done in the code and in the docs; only the PR description is left.

- **Done:** the override enum and complementary `ifNotIn` lists for the destination chain; `tokenTicker` with `chainIdPath` for the output token (on the full bytes32 value in the bytes32 variants); `addressName` on the bytes32 depositor; two encoded cases (HyperEVM, Solana) and three real tagged app deposits. Pushed to `claude/nifty-euler-gwsa66-across`.
- **Done:** the report ends with "Update: chain names, output token, depositor, and app deposits with an integrator tag". The spec-limitation notes are rewritten: the "Output amount denominated in a token on another chain" section is removed (it is the intended design, not a limitation), the bytes32 and chain-name sections describe the new workarounds, and the ABI-encoded message section points to wishlist items 2 and 5.
- **To do:** replace the Across parts of the #3173 description with this update, together with items 2 and 7, and use the permalinks of item 1. The description must name the seven Sourcify runner failures.

## 10. All PRs: upstream master merged (spec sync #3180)

- **Done:** the common branch and the PR branches of #3171, #3173, #3175 and #3176 include upstream master with the ERC-7730 spec sync (#3180). #3172 and #3174 include it since 2026-10-29 too.
- **Done:** the "Cross-chain embedded calldata is not schema-valid" sections are removed from the Base and Blast spec-limitation notes, because the schema now allows `chainId`. The Base and Blast reports say that schema validation passes and only lint fails on `chainId`.
- **To do:** in the #3174 and #3172 descriptions, drop any claim that `chainId` is not schema-valid, and link the spec-limitation notes with the permalinks of item 1.

## 11. Pendle (#3176): token maps and two more functions

Done in the code and in the docs; only the PR description is left.

- **Done:** maps from market to PT, YT and SY (664 markets) and from YT to SY; `swapTokensToTokens` and `redeemDueInterestAndRewardsV2` described; 46 test cases. Pushed to `claude/nifty-euler-gwsa66-pendle`.
- **Done:** the report ends with "Update: token maps, `swapTokensToTokens` and `redeemDueInterestAndRewardsV2`". The spec-limitation notes have a rewritten "Token that only an on-chain read of another argument can name" section and a new "Amount known only at execution, reported by caller-named contracts" section.
- **To do:** add the update section to the #3176 description, together with item 2, and use the permalinks of item 1. It must say that the Rust runner cannot run the file and that the descriptor is 392 KB.

## 12. Uniswap (#3175): spec-limitation notes cleaned up

Docs only; no descriptor change.

- **Done:** in `docs/spec-limitations/uniswap-UniswapV3NonfungiblePositionManager.md`, the two sections about the zero `collect` recipient ("No sentinel for a special address value" and "Zero address that stands for this contract") are merged into one, which also explains why the visibility rules cannot help. The storage-token section now says why a map cannot help (1,244,243 positions). The integer-sentinel and zero-address sections point to wishlist item 7 (`specialValues` on every format, extending ethereum/ERCs PR 2027).
- **To do:** use the permalinks of item 1 for the #3175 description, so it links the cleaned-up notes.

## 13. Pendle (#3176): nested-call limitation mapped to the wishlist

Docs only; no descriptor change.

- **Done:** the section "Nested call that the intermediary rewrites, or that is calldata only for some values of another field" in `docs/spec-limitations/pendle-PendleRouterV4.md` now splits the proposed fix by cause, says that prepending bytes does not help, and points to wishlist items 3 and 5.
- **To do:** use the permalinks of item 1 for the #3176 description, so it links the updated notes.


## 14. Pendle (#3176): two limitations added to the wishlist

Docs only; no descriptor change.

- **Done:** wishlist item 9 (embedded calls whose amounts the intermediary rewrites, `amountsSetAtExecution` on `calldata`) and item 10 (amounts known only at execution, and a `mustBeIn` map rule for address lists). `docs/spec-limitations/pendle-PendleRouterV4.md` now points to both items.
- **To do:** use the permalinks of item 1 for the #3176 description, so it links the updated notes.

## 15. Base (#3174) and Blast (#3172): L2 contracts added

- **Done:** Base gets the L2ToL1MessagePasser. Blast gets the L2ToL1MessagePasser, the BLAST Airdrop and the AirdropVesting proxy. Both L2ToL1MessagePassers decode the L1 call with the `calldata` format and `chainId: 1`. One Blast portal test case is replaced, because its L2 callee now has a descriptor and renders a nested call. Pushed to both PR branches, together with the upstream merge.
- **Done:** the Base and Blast reports end with a new "Update" section ("L2ToL1MessagePasser on Base", "L2ToL1MessagePasser and the BLAST airdrop contracts on Blast"). The Blast spec-limitation note on the share price mentions the L2ToL1MessagePasser sentence.
- **To do:** add those update sections to the #3174 and #3172 descriptions, list the new files, and use the permalinks of item 1.

## 16. Pendle (#3176): maps removed, PT, YT and SY amounts raw

- **Done:** the four maps are removed, because a market that is missing from a map makes the descriptor invalid, and new markets were blind until a refresh. The 35 PT, YT and SY amounts use the `raw` format with "(raw)" labels. The 5 nested multicall cases are moved out of the test file. Both runners pass 41/41. Pushed to the PR branch.
- **Done:** the report ends with "Update: PT, YT and SY amounts shown raw, maps removed". The spec-limitation section "Token that only an on-chain read of another argument can name" describes the new workaround.
- **To do:** in the #3176 description, drop the map text of item 11 and add this update section, with the permalinks of item 1. The description must no longer say that the Rust runner cannot run the file.

## 17. SwftSwap (#3171): BNB Chain deployment

- **Done:** SwftSwap on chain 56 is verified on Sourcify (runtime match). The descriptor has the chain 56 deployment and one real chain 56 test case. Both runners pass 10/10. The report ends with "Update: BNB Chain deployment".
- **To do:** add that update to the #3171 description, and change any text that says BNB Chain is not covered.

## 18. Review round 1 (#3172, #3173, #3174, #3176)

- **Done:** every thread of marcocastignoli's first review is addressed on the PR branches: Base `a5cd30b`, Blast `086ed51`, Across `d684482`, Pendle `75a427d` and `a0b7be5`. Each report ends with "Update: review round 1". `REVIEW-ROUND-1.md` holds one reply per thread and the agent instruction to post them.
- **To do:** post the replies, resolve the "Done" threads, append each "Update: review round 1" section to the PR description with the permalinks of item 1, and re-request the review.

## 19. Across (#3173): review round 2

- **Done:** the deposit sentence says "the relayer must send {outputAmount}" and the speed-up formats say "Request bridge deposit update" (commit `d890b5e`, upstream master merged; `043f71b` removes unused `metadata.constants`). The report ends with "Update: review round 2"; `REVIEW-ROUND-1.md` has the two replies.
- **To do:** post the two replies, resolve the threads, append the update section to the #3173 description with the permalinks of item 1, and re-request the review. #3172, #3174 and #3176 are merged; their descriptions need no further change.

