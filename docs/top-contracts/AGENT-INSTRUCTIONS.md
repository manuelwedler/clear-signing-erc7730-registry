# Agent instructions for the remaining work

Each section names the repository to run it on and holds one instruction to copy into an agent that has the right permissions there. The source files are on the public fork `manuelwedler/clear-signing-erc7730-registry`, branch `claude/nifty-euler-gwsa66`, commit `21a929df94ba4d26348ccec2f8b12d002a968f81`.

Order: run 1 and 6 now. Run 2, 3 and 4 in parallel. Run 5 after 2, 3 and 4 are merged and released.

## 1. PR descriptions and ready for review

Repository: `ethereum/clear-signing-erc7730-registry` (edit rights on PRs #3171 to #3176)

```text
Task: rewrite the descriptions of the six draft pull requests #3171 to #3176 in ethereum/clear-signing-erc7730-registry, then mark each one as ready for review. Do not change any code or branch.

Source material: the public fork manuelwedler/clear-signing-erc7730-registry at commit 21a929df94ba4d26348ccec2f8b12d002a968f81 (branch claude/nifty-euler-gwsa66). Read these files at that commit:
- docs/top-contracts/PR-BODY-FIXES.md: the fix list. Apply every "To do" line of items 1 to 16. The "Done" lines describe work that is already pushed; use them as facts.
- The report for each PR, in docs/top-contracts/:
  #3171 swft-SwftSwap.md
  #3172 blast-OptimismPortal.md
  #3173 across-Ethereum_SpokePool.md
  #3174 base-OptimismPortal2.md
  #3175 uniswap-UniswapV3NonfungiblePositionManager.md
  #3176 pendle-PendleRouterV4.md
- docs/top-contracts/REMAINING.md, section "Expected CI state".

For each PR:
1. Read the current description: gh pr view <N> --repo ethereum/clear-signing-erc7730-registry --json body,isDraft
2. Build the new description from the report. Keep its main sections. Fold every "Update: ..." section at the end into the main text: where an update replaces older text, keep only the new text. Remove the lines that start with "Add this to the PR ... description".
3. Keep the section headings of .github/pull_request_template.md in the registry if the current description uses them.
4. Link files on the fork only with commit permalinks of the form https://github.com/manuelwedler/clear-signing-erc7730-registry/blob/21a929df94ba4d26348ccec2f8b12d002a968f81/<path>. Never link a branch name. Item 1 of PR-BODY-FIXES.md lists the spec-limitation notes; give each PR the link to its own note.
5. State the expected CI result:
   - #3172 Blast and #3174 Base: lint reports two errors per chainId field in the calldata format. The schema allows chainId since the spec sync #3180; the pinned linter does not know it yet. A linter fix is in progress.
   - #3172 Blast: the Rust runner fails two cases (an empty byte slice renders as <unresolved>). A runner fix is in progress.
   - #3173 Across: the Sourcify runner fails seven cases (addressName and tokenTicker on bytes32). A library fix is in progress.
   - All other checks pass. #3176 Pendle passes both runners.
6. Write the body to a file and run: gh pr edit <N> --repo ethereum/clear-signing-erc7730-registry --body-file <file>
7. Mark it ready: gh pr ready <N> --repo ethereum/clear-signing-erc7730-registry

Rules: no Claude session links (https://claude.ai/code/session_...) and no model names in the text. Write plain, short sentences.

Report back: each PR URL, whether it is now ready for review, and one line on what changed in its description.
```

## 2. Rust test runner fixes

Repository: `llbartekll/clear-signing` (fork it and open a PR if you cannot push)

```text
Task: fix five bugs in the Rust clear-signing SDK and its cs-test runner in llbartekll/clear-signing, add a test for each, and open one pull request (or one per bug if the maintainers prefer small PRs). The ERC-7730 registry pins this runner at commit 65af2281aa1366e1d770f9ac445007e56dbe29ca. First check main: a bug may already be fixed there.

Reference: the ERC-7730 spec and the test schema in ethereum/clear-signing-erc7730-registry: specs/erc-7730.md and specs/erc7730-tests-v2.schema.json.

1. Nested interpolatedIntent in expected test output.
   The test schema allows interpolatedIntent and owner in a nested rendered output ("definitions.renderedOutput" is used for nested calldata values in "definitions.fields"). cs-test rejects it: NestedExpected in crates/cs-test/src/schema.rs has #[serde(deny_unknown_fields)] and no interpolatedIntent field (around lines 93-101). As a result, a test file with a nested call whose callee format has an interpolatedIntent cannot be parsed ("data did not match any variant of untagged enum TestCase"). Add optional interpolated_intent (rename "interpolatedIntent") and owner to NestedExpected and compare them in crates/cs-test/src/compare.rs when they are present.
   Test: the files in docs/top-contracts/nested-tests/ of manuelwedler/clear-signing-erc7730-registry at commit 21a929df94ba4d26348ccec2f8b12d002a968f81 (with the descriptors from that commit) must parse and pass.

2. Chain names for the chainId format.
   crates/clear-signing/src/render_shared.rs, chain_name(): a table of 16 chains. Every other chain shows "Chain <id>". The spec says the chainId format converts the value "to a Blockchain name using EIP-155 reference values". Generate the full table from https://chainid.network/chains.json (the "name" field), check it in as a generated file with the script that builds it, and keep a fallback for unknown ids that shows the decimal id.
   Test: 999 renders "Wanchain Testnet" (the registry name), 81457 renders "Blast", 59144 renders "Linea".

3. Chain ids above 64 bits.
   crates/clear-signing/src/engine.rs, around lines 2307-2334: a chain id that does not fit in u64 renders "Chain 0", and a tokenAmount with that chainIdPath resolves the token on the signing chain. Parse the value as U256. For the chainId format, show the decimal value with the fallback of bug 2. For tokenAmount and tokenTicker with such a chainIdPath, do not resolve the token on the signing chain: show the raw amount and mark the token as unknown.

4. Byte slice past the end of the data.
   A field path with a byte slice, for example "_extraData.[0:32]", renders "<unresolved>" when the bytes are empty or shorter than the slice (crates/clear-signing/src/engine.rs around line 1693). The Sourcify runner renders the empty slice as 0 for a tokenAmount. The spec does not define this case. Align with the Sourcify runner: a slice clamps to the available bytes, and an empty value decodes as 0 for integer formats. Write the rule in a comment and in the PR text, so that the spec can adopt it.
   Test: registry/blast/calldata-L1BlastBridge.json with registry/blast/testsv2/calldata-L1BlastBridge.tests.json from the commit above: the cases "bridgeERC20 - chain 1" and "bridgeERC20-steth - chain 1" must render "0 DAI".

5. Spec map references.
   The spec ("metadata.maps") lets a parameter be {"map": "$.metadata.maps.<name>", "keyPath": "<path>"}, and a map is {"$keyType": ..., "values": {...}}. The SDK expects a string in FormatParams.token (crates/clear-signing/src/types/display.rs around lines 386-387) and has its own map model with "entries" and "mapReference" (crates/clear-signing/src/types/metadata.rs around lines 66-76). Support the spec form for every parameter that takes a constant. A key that is not in the map makes the descriptor invalid for the transaction, as the spec requires.
   Test: the example files assets/eip-7730/example-maps.json and example-maps-pools.json of the ERC.

Run the repository's own checks (cargo fmt, cargo clippy, cargo test) before you push.

Report back: the PR URL(s), and the new commit to pin in the registry.
```

## 3. Linter fixes

Repository: `sourcifyeth/python-erc7730` (fork it and open a PR if you cannot push)

```text
Task: fix three gaps in the ERC-7730 linter sourcifyeth/python-erc7730, add tests, and open a pull request. The ERC-7730 registry pins it at commit 964176e28918299dfecb269e20a267a652ada475 (.github/requirements.txt in ethereum/clear-signing-erc7730-registry). First check main: a gap may already be fixed there; then say so and skip it.

1. chainId and chainIdPath in the calldata format.
   ethereum/ERCs PR 2124 added chainId (integer or map reference) and chainIdPath (string) to calldataParameters in the v2 schema, and forbids setting both. The registry synced it in its PR #3180 (specs/erc7730-v2.schema.json). The linter's v2 input model for calldata parameters rejects them ("Extra inputs are not permitted" at ...params.call_data.chainId). Add both to the input model, the resolved model and the resolver in src/erc7730/convert/resolved/v2/parameters.py (resolve chainIdPath relative to the field prefix, as for tokenAmount). Reject a descriptor that sets both.
   Test: registry/base/calldata-OptimismPortal2.json and registry/blast/calldata-L2ToL1MessagePasser.json of manuelwedler/clear-signing-erc7730-registry at commit 21a929df94ba4d26348ccec2f8b12d002a968f81 lint without errors.

2. Relative chainIdPath in tokenAmount and tokenTicker.
   resolve_token_amount_parameters returns params.chainIdPath unchanged (src/erc7730/convert/resolved/v2/parameters.py around line 285; the same for tokenTicker). A relative path such as "destinationChainId" is therefore not joined with the field prefix, and lint reports false errors. Resolve it with constants.resolve_path and data_or_container_path_concat, as the token path is resolved.
   Test: a copy of registry/across/calldata-Ethereum_SpokePool.json from the commit above, with "#.destinationChainId" changed to "destinationChainId", lints without errors.

3. Map references.
   Map references in parameters are dropped with the warning "Unresolved map reference ... will be dropped" (parameters.py around lines 85 and 115), and the Ledger conversion drops them too. Resolve them: check that the map exists in metadata.maps and that keyPath is a valid path, keep the reference in the resolved model, and keep it in conversions that can carry it. Use the ERC's assets/eip-7730/example-maps.json as the test.

Also add a regression test: addressName and tokenTicker on a bytes32 argument must keep linting without errors (the registry uses this for EVM addresses stored in bytes32, for example the Across depositor).

Run the repository's own checks (lint, type check, tests) before you push.

Report back: the PR URL, and the commit or release to pin in the registry.
```

## 4. Sourcify library and test runner: address formats on bytes32

Repositories: `sourcifyeth/clear-signing` first, then `sourcifyeth/clear-signing-test-runner` (fork and open PRs if you cannot push)

```text
Task: let the Sourcify ERC-7730 library render addressName and tokenTicker on a bytes32 value, release it, and bump it in the Sourcify test runner.

Part A, repository sourcifyeth/clear-signing (package @ethereum-sourcify/clear-signing, version 0.3.0):
- Today addressName and tokenTicker on a bytes32 argument fail with ARGUMENT_TYPE_MISMATCH "Format addressName expects address but got bytes" (in the published dist/index.js around lines 993-995 and 1133-1141; find the source in src/). Cross-chain contracts store EVM addresses in bytes32, for example the Across SpokePool depositor, recipient and outputToken.
- Accept a bytes32 value for both formats. When the top 12 bytes are zero, read the low 20 bytes as an address and render it as for the address type (checksummed, with name or ticker resolution; tokenTicker honours chainId and chainIdPath). When the top 12 bytes are not zero (for example a Solana key), do not fail: render the full 32-byte value as hex, and for tokenTicker show the value instead of a ticker.
- Tests: registry/across/calldata-Ethereum_SpokePool.json with registry/across/testsv2/calldata-Ethereum_SpokePool.tests.json from manuelwedler/clear-signing-erc7730-registry at commit 21a929df94ba4d26348ccec2f8b12d002a968f81: all 16 cases pass (today 7 fail).
- Run the repository's checks, open a PR, and after the merge publish a new version (or ask the maintainers to).

Part B, repository sourcifyeth/clear-signing-test-runner (pinned by the registry at 9d6d2fe4715d53e002bb966f6593e1fbc44b53c7):
- Bump @ethereum-sourcify/clear-signing to the new version, run its checks, and open a PR.

Report back: both PR URLs, the published version, and the runner commit to pin in the registry.
```

## 5. Registry pin bumps and nested test cases

Repository: `ethereum/clear-signing-erc7730-registry` for the pins, and the fork `manuelwedler/clear-signing-erc7730-registry` for the PR branches

```text
Task: after the fixes in llbartekll/clear-signing (Rust runner), sourcifyeth/python-erc7730 (linter) and sourcifyeth/clear-signing-test-runner (Sourcify runner) are merged, bump the three pins in ethereum/clear-signing-erc7730-registry, then add the nested-call test cases to the six descriptor PRs.

Part A, ethereum/clear-signing-erc7730-registry, one PR that changes only .github/:
- .github/requirements.txt: the erc7730 git commit (now 964176e28918299dfecb269e20a267a652ada475).
- .github/actions/run-rust-tests/action.yml: ref (now 65af2281aa1366e1d770f9ac445007e56dbe29ca) and its date comment.
- .github/actions/run-sourcify-tests/action.yml: ref (now 9d6d2fe4715d53e002bb966f6593e1fbc44b53c7) and its version comment.
- Check that the registry's CI passes on master descriptors with the new pins. If a new pin breaks existing descriptors, list them in the PR and stop.

Part B, after Part A is merged, on the fork manuelwedler/clear-signing-erc7730-registry:
- docs/top-contracts/nested-tests/ on branch claude/nifty-euler-gwsa66 holds real nested-call test cases. Each file is named <entity>-calldata-<Name>.nested.tests.json. Read its README.md.
- For the base, blast and pendle files: check out branch claude/nifty-euler-gwsa66-<entity>, merge upstream master (a merge commit, no rebase), append the file's tests to registry/<entity>/testsv2/calldata-<Name>.tests.json and merge its dataProvider entries. Run the registry checks (lint, schema, both runners, index). Commit and push to that branch. Then copy the same registry/<entity> folder to branch claude/nifty-euler-gwsa66 and push.
- Run the registry checks on #3171, #3173 and #3175 again after merging upstream master into their branches, and push the merge.

Commit messages end with this trailer line, after one empty line:
Co-Authored-By: Manuel Wedler <manuel@wedler.dev>
Do not add a Claude-Session trailer or a Claude session link.

Report back: the pin PR URL, and the CI result of each of #3171 to #3176.
```

## 6. SwftSwap on BNB Chain, and the spec wishlist issue

### 6a. Verify SwftSwap on BNB Chain and add the deployment

Repository: `manuelwedler/clear-signing-erc7730-registry` (branches `claude/nifty-euler-gwsa66-swft` and `claude/nifty-euler-gwsa66`)

```text
Task: verify the SwftSwap contract on BNB Chain on Sourcify, then add the BNB Chain deployment to the SwftSwap descriptor of PR ethereum/clear-signing-erc7730-registry#3171.

Facts: SwftSwap is at 0xc1d13492285eb664951E201BF7C80c7c6318a1b5 on chains 1, 10, 137, 42161, 43114 and 56. On chain 56 the runtime bytecode is identical to chain 1, but the contract is verified neither on Sourcify nor on BscScan.

1. Get the compiler input of the verified chain 1 contract from Sourcify: GET https://sourcify.dev/server/v2/contract/1/0xc1d13492285eb664951E201BF7C80c7c6318a1b5?fields=stdJsonInput,compilation
2. Submit it for chain 56: POST https://sourcify.dev/server/v2/verify/56/0xc1d13492285eb664951E201BF7C80c7c6318a1b5 with stdJsonInput, compilerVersion and contractIdentifier ("<source path>:<contract name>") from step 1. Poll the returned verificationId until it finishes. If it fails, report the error and stop.
3. Check out branch claude/nifty-euler-gwsa66-swft of manuelwedler/clear-signing-erc7730-registry. Merge upstream master (ethereum/clear-signing-erc7730-registry) with a merge commit if it is behind.
4. In registry/swft/calldata-SwftSwap.json, add {"chainId": 56, "address": "0xc1d13492285eb664951E201BF7C80c7c6318a1b5"} to context.contract.deployments, in chain id order.
5. Find one recent successful swap or swapEth transaction to that address on chain 56 and add a case "swap - chain 56" (or "swapEth - chain 56") to registry/swft/testsv2/calldata-SwftSwap.tests.json, in the same shape as the other chains' cases, with rawTx, txHash, from, and the expected screen. Read token metadata (symbol, name, decimals) from chain 56 for the data provider.
6. Run the registry checks: lint (python-erc7730 at the commit in .github/requirements.txt), schema (.github/scripts/validate-json-schemas.sh), both test runners (the commits in .github/actions/run-*-tests/action.yml), and node tools/scripts/generate-index.js --validate. All must pass.
7. Commit and push to claude/nifty-euler-gwsa66-swft. Copy registry/swft to branch claude/nifty-euler-gwsa66, commit and push. In docs/top-contracts/swft-SwftSwap.md on that branch, change the chain 56 row to "yes" with the Sourcify verification and the test transaction, and add a "Update: BNB Chain deployment" section at the end.

Commit messages end with this trailer line, after one empty line:
Co-Authored-By: Manuel Wedler <manuel@wedler.dev>
Do not add a Claude-Session trailer or a Claude session link.

Report back: the Sourcify verification result, the test transaction hash, and the pushed commits.
```

### 6b. Open the spec wishlist issue

Repository: `ethereum/clear-signing-erc7730-registry`

```text
Task: open one issue in ethereum/clear-signing-erc7730-registry with the ERC-7730 spec wishlist that came out of six descriptor PRs (#3171 to #3176).

Source: docs/top-contracts/SPEC-WISHLIST.md in the public fork manuelwedler/clear-signing-erc7730-registry at commit 21a929df94ba4d26348ccec2f8b12d002a968f81.

1. Search the open issues of the registry for an existing spec wishlist or for the same items, so that you do not open a duplicate. If one exists, add the items as a comment there instead.
2. Title: "ERC-7730 spec wishlist from the top-contracts descriptors (#3171 to #3176)".
3. Body: a two-sentence introduction (what the list is and where it comes from), then the items of SPEC-WISHLIST.md. Keep item numbers and all text. Item 2 is done (ethereum/ERCs PR 2124, registry #3180): keep it as one line under a "Done" heading at the end, not as an open item. Refer to PRs as ethereum/clear-signing-erc7730-registry#3171 and ethereum/ERCs#1925 so that GitHub links them. Link files on the fork only with commit permalinks (blob/21a929df94ba4d26348ccec2f8b12d002a968f81/...).
4. Do not add a Claude session link or a model name.

Report back: the issue URL.
```

The runner conflict on a nested `interpolatedIntent` needs no separate report: section 2, bug 1 fixes it in the Rust runner, which is the runner that disagrees with the test schema.
