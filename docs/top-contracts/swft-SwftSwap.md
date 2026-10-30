# SwftSwap (SWFT / Bridgers) — ERC-7730 clear-signing descriptor

> **Draft notice.** This descriptor was written for the registry's top-contracts effort. It is **not** submitted by the SWFT / Bridgers team. The authoring choices below were made by a language-model agent with the clear-signing-helper CLI and are tagged as such in the helper's local provenance record. Maintainers: please ask SWFT to confirm the wording before merge, in particular the custodial trust assumption in "Summary".

## Summary

- Entity `swft`, file `registry/swft/calldata-SwftSwap.json`, tests `registry/swft/testsv2/calldata-SwftSwap.tests.json`.
- Contract `SwftSwap` at `0xc1d13492285eb664951E201BF7C80c7c6318a1b5`, Sourcify runtime match on chain 1 (compiler 0.8.0, `SwftSwap.sol:SwftSwap`, deployer `0xa91EA6E5F9CbAe55396Fb6E3aEB2234B5952CE0C`). Not a proxy. No existing registry descriptor deploys this address or matches its non-standard selectors (`init --registry` reported only the generic `Ownable` priors).
- Two user-facing functions are described: `swap` and `swapEth`. Four `onlyOwner` functions are excluded.
- **Trust assumption, stated plainly:** this is a custodial service. `swap` moves `fromAmount` of `fromToken` from the signer into the contract (`SwftSwap.sol` line 55) and `swapEth` keeps `msg.value` (line 64). Nothing else happens on-chain: `toToken`, `destination` and `minReturnAmount` are only written to the `Swap` / `SwapEth` events (lines 59 and 66). SWFT's off-chain operator reads those events and pays the destination from its own reserves; the owner key withdraws the deposits with `withdraw` / `withdrawETH` (lines 69–84). There is no on-chain check of `minReturnAmount`, no refund path and no deadline. The screens therefore say "Send … to SWFT", label the minimum "Requested Min (raw)", never "at least", and open with a constant "Note" field: "Paid out off-chain by SWFT. The minimum is not enforced on-chain."
- The contract's on-chain `name()` / `symbol()` return `Bridgers1.1` / `Bridgers` on every chain (SWFT's current product name is Bridgers, https://bridgers.ai/, listed by DefiLlama as a SWFT Blockchain product). `metadata.owner` is `SWFT` as the brief asked; `info.url` is https://www.swft.pro/ (live, titled "SWFT Blockchain — One-Stop Cross-Chain Platform"). The maintainers may prefer `Bridgers` as the displayed owner; it is a one-word change.

## Coverage

### Described

| Function | Intent | Fields shown |
|---|---|---|
| `swap(address fromToken,string toToken,string destination,uint256 fromAmount,uint256 minReturnAmount)` | `Send to SWFT for swap` | Note (constant value, no path), Amount (`fromAmount`, tokenAmount by `fromToken`), Order Details (`toToken`, raw), Payout Address (`destination`, raw), Requested Min (raw) (`minReturnAmount`, raw) |
| `swapEth(string toToken,string destination,uint256 minReturnAmount)` | `Send to SWFT for swap` | Note (constant value, no path), Amount (`@.value`, amount), Order Details, Payout Address, Requested Min (raw) |

Interpolated intents: `Send {fromAmount} to SWFT to swap for {toToken}, paid to {destination}, requested minimum {minReturnAmount} (raw units)` and the same with `{@.value}`. They exceed 30 characters because they name every shown amount, the payout address and the requested minimum; the linter warns (`INTENT_LENGTH`), as it does for most merged sentences.

### Excluded (with reason recorded in `bundle/review/validation.json`)

| Function | Reason |
|---|---|
| `withdraw(address,address,uint256)` | `onlyOwner` (`SwftSwap.sol` line 77). The SWFT operator key drains tokens from custody. Every mainnet call found is sent by the owner `0x04d6f7027aE7Ce52654aa21Bfb67802F0c9Ea303` (checked: `owner()` on chain 1 returns that address; the discovered call `0x318f8392e49bfd98e3adcbb5241609e739b497bdf71b2e31e56ca44a2546ab5d` is from it). Users cannot call it. |
| `withdrawETH(address,uint256)` | `onlyOwner` (`SwftSwap.sol` line 69), same operator key; discovered call `0x14f00a6600137ee4c40d9da790f042fe148f03bfa2a5408d80408dad94841958` is from the owner. |
| `transferOwnership(address)` | `onlyOwner` (`Ownable.sol` line 61). One mainnet call ever (`0x02df8616cf6b2b7015794d12fcb235700d4b5d7ad3dfcd23554411cf72f5cddc`, from the deployer `0xa91E…CE0C` to the current owner). |
| `renounceOwnership()` | `onlyOwner` (`Ownable.sol` line 53). Never called on mainnet (HyperSync searched the whole chain). |

The 7-day traffic figures in the brief (about 17k `withdraw`/`withdrawETH` calls) are the operator sweeping deposits, not users; excluding them loses no user-facing screen.

### Hidden fields

| Function | Field | Reason |
|---|---|---|
| `swap` | `fromToken` | Shown as the ticker of "Amount" (`tokenAmount` with `tokenPath: fromToken`). Written as `visible: "never"` by `apply`; the reason is kept in the review record. |

No other field is hidden. `toToken`, `destination` and `minReturnAmount` are ignored by the contract's logic but are what SWFT acts on off-chain, so the signer must see them (see "What the screens say").

### Pinned arguments (`mustMatch`)

None. No argument switches off a check that the screen states: the only on-chain claims are the two exact amounts, and no argument changes what `safeTransferFrom(fromToken, msg.sender, this, fromAmount)` or `msg.value` moves.

## What the screens say

Each judgment call, with the source that justifies it (files under `bundle/review/` and the verified source at https://repo.sourcify.dev/1/0xc1d13492285eb664951e201bf7c80c7c6318a1b5):

1. **Intent `Send to SWFT for swap`, not `Swap`.** `swap` performs no swap: `SwftSwap.sol` lines 51–59 check the inputs, pull `fromAmount` into the contract and emit an event. `swapEth` (lines 62–67) keeps `msg.value` and emits. The payout happens off-chain. Calling the screen "Swap" would describe an atomic exchange that the transaction does not perform. The intent names the counterparty the funds go to, which is what the signer is trusting.
2. **The same intent for both functions, chain-neutral.** An earlier draft said `Send ETH to SWFT for swap` for `swapEth`; with the Polygon and Avalanche deployments the native amount renders as `88 POL` and `221.57 AVAX`, so the word ETH was dropped. The "Amount" field carries the ticker.
3. **`Amount` is exact, not a limit.** For `swap`, the signer pays exactly `fromAmount` (`TransferHelper.safeTransferFrom(fromToken, msg.sender, address(this), fromAmount)`, line 55). For a fee-on-transfer token the signer still pays `fromAmount`; the contract only checks that it received something (`_inputAmount > 0`, line 58). The `claims` replay confirmed the exact claim on both real mainnet transactions ("sender paid 110000000 USDC", "sender paid 40000000000000000 wei"). For `swapEth`, `@.value` is what leaves the wallet (line 64).
4. **`Requested Min (raw)`.** `minReturnAmount` appears only in the event (line 59 / 66). No `require` reads it. It is a request to the operator, so the label says "Requested" and the sentence says "requested minimum", never "at least". "(raw)" in the label and "(raw units)" in the sentence tell the signer that the number is unscaled: it has no decimal point and counts the smallest unit of the destination token. It is denominated in the destination token's own smallest unit on the destination chain (the mainnet fixtures show `107859983` for USDT on TRON, 6 decimals, and `93148668000000000000` for USDT on BSC, 18 decimals). The destination token is given only as a string, so no ERC-7730 format can scale it (see `SPEC-LIMITS.md`). Showing the raw integer was preferred to hiding it: hiding would remove the signer's only view of what they asked for, and the brief's decision was to show it as requested. The field is last on the screen and labelled so that the number is not read as an amount of the sent token.
5. **`Order Details` for `toToken`.** The dapp does not pass a bare token name. Every real transaction found carries a pipe-packed string, for example `USDT(TRON)|zvcm92|0.015|bridgers|0`, `TRX|zvcm92|0.02|bridgers|0`, `USDT(ARB)|6nu8wra5|0.010000000|bridgers|0`: destination token with its chain in brackets, an identifier, a rate and the channel name. The contract treats it as opaque (line 59). The label "To Token" would misdescribe four of the five segments, so the field is labelled "Order Details" and the sentence reads "to swap for {toToken}". I could not reach SWFT's API documentation from this session to cite the exact field list; the format above is observed from on-chain calls, not documented.
6. **`Payout Address` for `destination`.** It is the address on the destination chain where SWFT pays out (TRON `T…` addresses and EVM `0x…` addresses in the fixtures). It is a string, so it is shown raw. It is the most important thing for the signer to check after the amount, so it is in the sentence.
7. **No `nativeCurrencyAddress`, no `threshold`.** `swap` requires `fromToken != 0` (line 51) and reads it as an ERC-20; there is no native-token path through `swap`. No sentinel value has special meaning.
8. **`fromToken` hidden.** It is displayed as the ticker of "Amount". If a wallet cannot resolve the ticker it shows the raw amount with an "Unknown token" warning; the mainnet preview did that before the fixture carried USDC metadata.
9. **A constant "Note" field states the trust assumption on screen.** Both functions open with `{ "label": "Note", "value": "Paid out off-chain by SWFT. The minimum is not enforced on-chain.", "format": "raw" }`. The field has a literal `value` and no `path`, which ERC-7730 allows to display a constant (field format specification, `path` / `value`). It tells the signer what the contract cannot guarantee: the payout happens off-chain (lines 55, 64), and no `require` reads `minReturnAmount` (lines 59, 66). Both registry runners render it as the first field.

## Deployments

All deployments are the same address, deployed by the same key (`0xa91EA6E5F9CbAe55396Fb6E3aEB2234B5952CE0C`) and are not proxies (Sourcify `proxyResolution.isProxy: false`). Evidence collected in this session:

| Chain | Added | Evidence |
|---|---|---|
| 1 Ethereum | yes (brief) | Sourcify runtime match (`match: "match"`, `creationMatch: null`), `SwftSwap.sol:SwftSwap`, solc 0.8.0+commit.c7dfd78e. `owner()` = `0x04d6…a303`. |
| 10 Optimism | yes | `cast code` byte-identical to chain 1 (9272 hex chars, including the CBOR metadata hash `…f37fab0b…`). Sourcify runtime match as `BridgersSwap.sol:BridgersSwap`, same compiler, same deployer; the source differs from the mainnet file only in the contract name, whitespace / line endings and the constructor strings, which do not reach the runtime bytecode. Two real-transaction tests pass both runners. |
| 137 Polygon | yes | Same bytecode check and the same Sourcify `BridgersSwap` match. Two real-transaction tests pass both runners (native renders as `POL` in both runners). |
| 42161 Arbitrum One | yes | Same bytecode check and Sourcify `BridgersSwap` match. One real-transaction test (`swap`). |
| 43114 Avalanche C-Chain | yes | Same bytecode check and Sourcify `BridgersSwap` match. Two real-transaction tests. |
| 56 BNB Chain | yes | Bytecode at the address is byte-identical to chain 1. Sourcify runtime match (`match: "match"`, `creationMatch: null`, matchId `57551322`), verified on 2026-10-29 from the chain 1 standard-JSON input as `SwftSwap.sol:SwftSwap`, solc 0.8.0+commit.c7dfd78e. One real-transaction test (`swap - chain 56`, `0x743753cbddfa06347c589f5fb4dc5574dd5840811f20d6335f0627081e781be3`). See "Update: BNB Chain deployment". |
| 8453, 100, 59144, 25, 66 | no | No code at the address. |
| 250, 324, 1284, 128 | no | The endpoint returned no matching code at the address (empty or a short non-code response); not pursued. |

On every added chain `name()` returns `Bridgers1.1` and `symbol()` `Bridgers`, which differs from both verified constructors (`SWFT Swap1.1`/`SSwap` on mainnet, `Bridgers Swap1.1`/`BridgersSwap` elsewhere). Both Sourcify records are runtime matches with no creation match, which is consistent with a constructor-string change that does not affect the runtime code. The runtime bytecode, which is what the signer calls, is identical on all five chains.

Protocol-side deployment documentation was not reachable from this session (`docs.bridgers.xyz` does not resolve here; GitHub code search is not available in this session), so the evidence is bytecode and Sourcify, not a docs page.

## Tests

All 9 test cases are real mined transactions sent directly to the contract (none encoded). `tests.real = 9`, `tests.encoded = 0`. Every expected screen starts with the constant "Note" field.

| Case | Chain | txHash | What it renders |
|---|---|---|---|
| `swap - chain 1` | 1 | `0x8358b4cdd503e020f0e05ac81e19193efc01e3f8df943d930b44aa7690848350` | 110 USDC → USDT(TRON), payout `TTci…3ntg`, requested minimum 107859983 |
| `swapEth - chain 1` | 1 | `0x55215a0254d7285b07c076c156325a1b854db0291c25097421e99dec5639e780` | 0.04 ETH → USDT(BSC) |
| `swap-optimism - chain 10` | 10 | `0x33a4b6c60d594c187f4ea16c76801da1e48be7b0e446642e7c22fdbd029cf4d8` | 2236.540972 OP → USDT(BSC) |
| `swapEth-optimism - chain 10` | 10 | `0x417293ce3ea268ce38850638897b3fba839085fb58aa354517372b722ec7c6d1` | 1.1871347 ETH → ETH |
| `swap-polygon - chain 137` | 137 | `0x9374b44701d0eb9552563310e96bfcbe1580ae96d6dad7c7d070ad55b1177d42` | 2905 USDT0 → USDT(TRON) |
| `swapEth-polygon - chain 137` | 137 | `0x6f407f4a993c300ee66f54a4750a6c3fdbe1725c6a152349cc50db2f5037f556` | 88 POL → TRX |
| `swap-arbitrum - chain 42161` | 42161 | `0x69695dc26c47376be056ef6ed9861c9f4e973f30ae7c7208f4007468cfa19986` | 1000 ARB → USDT(ARB) |
| `swap-avalanche - chain 43114` | 43114 | `0xbe61101afecaa999022b9796ddf042a698b2bae4269640aec653fbda3b9b9cf0` | 15 USDt → BNB(BSC) |
| `swapEth-avalanche - chain 43114` | 43114 | `0xd00b08322264bcd7cdc91050043b70a020a8f794af374e0294b72119032cc7e8` | 221.5744625248992 AVAX → ETH |

Token metadata in `dataProvider.tokens` was read from each chain by `fixture --tx --rpc-url` (USDC, OP, USDT0, ARB, USDt). The mainnet fixtures came from `discover` (HyperSync, whole chain); the Optimism, Arbitrum and Avalanche ones from `discover --chain-id`; the Polygon ones from `fixture --tx` with hashes from the Etherscan V2 transaction list. Fixtures for the excluded functions (`withdraw`, `withdrawETH`, `transferOwnership`) were discovered too and then removed; the registry needs no test for an excluded function.

## Checks

- **Helper:** clear-signing-helper `0.6.0-preview.6`; renderer `@ethereum-sourcify/clear-signing@0.2.2+signed-int-fix.1`. `clear-signing check`: no warnings besides the two `INTENT_LENGTH` sentences. `review --accept` and `test --update` were run after reading every preview.
- **Lint:** `erc7730 lint --require-verified` at the registry's pin `git+https://github.com/sourcifyeth/python-erc7730@964176e28918299dfecb269e20a267a652ada475` (from `.github/requirements.txt` / `descriptor-lint.yml`): exit 0, **0 errors, 6 warnings** as counted by the helper. The output lists one "Display intent too long" warning (both interpolated intents) and four "Missing display format" warnings, one per excluded admin function; the sixth counted line is uv's `UV_NATIVE_TLS` deprecation notice. No "Could not fetch ABI" warning: the linter fetched the reference ABI from Sourcify.
- **Registry runners** at the clone's CI pins: Sourcify runner `@ethereum-sourcify/clear-signing@0.3.0` (ref `9d6d2fe4715d53e002bb966f6593e1fbc44b53c7`) **9/9 pass**; Rust runner `llbartekll/clear-signing@0.1.0` (ref `65af2281aa1366e1d770f9ac445007e56dbe29ca`) **9/9 pass**. No `--accept-runner-failure` was needed; both runners render `POL` on Polygon and `AVAX` on Avalanche identically.
- **Strict portability:** `--strict-portability` raised no finding (`bundle/review/portability.json`: `findings: []`); nothing was excluded for portability. The ABI has only `address`, `string` and `uint256` arguments.
- **Claims replay:** `clear-signing claims --rpc-url https://mainnet.gateway.tenderly.co` on the two mainnet real-transaction fixtures: `swap` 41 runs, `swapEth` 39 runs, **0 findings**; the exact "Amount" claims hold on the baseline replay (sender paid 110000000 of USDC / 40000000000000000 wei; received 0). `https://eth.drpc.org` was tried first and failed with HTTP 408 "Request timeout on the free plan" on `eth_getTransactionReceipt`. Two things to note about the replay:
  - It did not flag `toToken`, `destination` and `minReturnAmount` as ignored arguments, although the contract ignores them on-chain. I read them as what the operator acts on off-chain and kept them visible on purpose; this is a judgment, not something the replay measured.
  - Tool limitation: `claims` crashed (`Cannot read properties of undefined (reading 'fields')`) when it reached a fixture of an excluded function (`transferOwnership`). Removing the excluded functions' fixtures let it complete. The other-chain fixtures were not replayed (the brief's historical-state endpoints are for mainnet); their screens are the same formats on byte-identical code.
- **Note field:** added by hand after the helper export, because the helper's decisions file has no slot for a constant field. After the change, the registry checks still pass: lint 0 errors with the same warnings, schema ok, index buildable, both runners 9/9.
- **Not run / not verified:** no physical-device rendering; no wallet verification; no attestation. SWFT's own API documentation and deployment list were not reachable from this session, so the `toToken` string format is described from observed calls only. The BSC deployment was not added (see "Deployments").
- **No git actions:** nothing was committed, pushed or written into the registry clone.

## Update: BNB Chain deployment

The BNB Chain deployment (chain 56) is now in the descriptor.

- **Verification.** The chain 56 contract had no Sourcify record and no BscScan source. I fetched the standard-JSON input of the verified chain 1 contract from Sourcify (`GET /server/v2/contract/1/0xc1d1…a1b5?fields=stdJsonInput,compilation`) and submitted it unchanged for chain 56 (`POST /server/v2/verify/56/0xc1d1…a1b5`, `compilerVersion` `0.8.0+commit.c7dfd78e`, `contractIdentifier` `SwftSwap.sol:SwftSwap`). Verification job `ee447e37-368b-40bb-a1d0-9a76e3ba37d9` finished with a runtime match (`match: "match"`, `runtimeMatch: "match"`, `creationMatch: null`, matchId `57551322`, verified at 2026-10-29T14:44:08Z). There is no creation match, as on chain 1. Sourcify also forwarded the source to BscScan; I could not check the BscScan status, because its status endpoint needs an API key.
- **Descriptor.** `context.contract.deployments` now has `{ "chainId": 56, "address": "0xc1d13492285eb664951E201BF7C80c7c6318a1b5" }`, between chains 10 and 137.
- **Test.** New case `swap - chain 56`: transaction `0x743753cbddfa06347c589f5fb4dc5574dd5840811f20d6335f0627081e781be3` (block 130491231, status 1), sent directly to the contract by `0x7861A82E7Cd688199EC416982EdEA37f31ac165F`. It sends 771.4 USDT (BSC-USD `0x55d398326f99059ff775485246999027b3197955`) for `USDT(TRON)|zvcm92|0.015|bridgers|0`, payout `TVekziJNDzBAu2FNuqYQb5NnwK9Lu112BW`, requested minimum 764500200. I found it with `eth_getLogs` on the contract address and read the token metadata (`Tether USD`, `USDT`, 18 decimals) with `eth_call` on chain 56 (`https://bsc-rpc.publicnode.com`). The `rawTx` is the unsigned type-2 form that the other cases use (nonce 0, fees 0, gas limit 1000000), with chain ID 56 and the original calldata and value.
- **Checks.** The test file now has 10 real-transaction cases (the 9 in "Tests" and the new one).
  - Lint `erc7730 lint --require-verified` at `964176e28918299dfecb269e20a267a652ada475`: exit 0, 0 errors, the same 5 warnings (one "Display intent too long", four "Missing display format" for the excluded admin functions).
  - Schema: `.github/scripts/validate-json-schemas.sh` passes for the descriptor and the test file.
  - Sourcify runner (ref `9d6d2fe4715d53e002bb966f6593e1fbc44b53c7`): 10/10 pass. Rust runner (ref `65af2281aa1366e1d770f9ac445007e56dbe29ca`): 10/10 pass.
  - `node tools/scripts/generate-index.js --validate`: the index is buildable.
