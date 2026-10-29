# Blast OptimismPortal (L1, Ethereum mainnet) — ERC-7730 calldata descriptor

> **Draft notice.** This descriptor was written for the registry's top-contracts effort. It was **not** submitted by the Blast team. It was authored from the verified source on Sourcify and from Blast's public deployment docs, by a language-model agent with the clear-signing-helper 0.6.0-preview.6. Every decision below is marked with the source line that justifies it. It is a draft for registry review; nobody from Blast has reviewed it.

## Summary

- **Contract:** `OptimismPortal` 1.10.0 (Blast's fork of the OP-stack portal), proxy `0x0Ec68c5B10F21EFFb74f2A5C61DFe6b08C0Db6Cb` on Ethereum (chain 1), EIP-1967 proxy to implementation `0xA280aEBF81c917DbD2aA1b39f979dfECEc9e4391`. Both are Sourcify full matches (compiler 0.8.15).
- **L2 chain identified as Blast (chain id 81457).** Evidence: the contract's live `systemConfig()` is `0x5531DcfF39EC1ec727C4c5D2fc49835368F805a9` and `l2Oracle()` is `0x826D1B0D4111Ad9146Eb8941D7Ca2B6a44215c76`; Blast's docs page https://docs.blast.io/building/contracts lists `OptimismPortal 0x0Ec68c5B10F21EFFb74f2A5C61DFe6b08C0Db6Cb` and `L2OutputOracle 0x826D1B0D4111Ad9146Eb8941D7Ca2B6a44215c76` under the mainnet L1 contracts; the verified source carries Blast-only files (`src/L2/Blast.sol`, `src/mainnet-bridge/ETHYieldManager.sol`, `src/mainnet-bridge/withdrawal-queue/WithdrawalQueue.sol`) and the portal's `yieldManager()` is `0x98078db053902644191f93988341E31289E1C8FE`. `cast chain-id` on https://rpc.blast.io returns 81457. The address is not in the Superchain registry (Blast is not a Superchain member), which is why the brief could not name it.
- **Entity:** `blast` (the chain's lowercase name, as the brief's entity note asks). `registry/blast/` does not exist in the clone yet.
- **Not already in the registry:** no file under `registry/` contains `proveWithdrawalTransaction`, `finalizeWithdrawalTransaction` or `depositTransaction(`; the address appears nowhere in the clone.
- **Files:** `bundle/registry/blast/calldata-OptimismPortal.json` and `bundle/registry/blast/testsv2/calldata-OptimismPortal.tests.json`.
- **Result:** erc7730 lint exit 0 (0 errors, 10 warnings); Sourcify runner 5/5; Rust runner 5/5; strict portability no findings; claims replay 445 runs, 0 findings.

## Coverage

### Described (3 functions)

| Function | Share of 7-day traffic | Intent |
|---|---|---|
| `proveWithdrawalTransaction((uint256,address,address,uint256,uint256,bytes),uint256,(bytes32,bytes32,bytes32,bytes32),bytes[])` | 2859 / 5845 | Prove Blast withdrawal |
| `finalizeWithdrawalTransaction(uint256,(uint256,address,address,uint256,uint256,bytes))` | 2978 / 5845 | Finalize Blast withdrawal |
| `depositTransaction(address,uint256,uint64,bool,bytes)` | 1 / 5845 (plus 13 plain ETH sends through `receive()`) | Deposit ETH to Blast |

`receive()` needs no entry. There is no `fallback()`.

### Excluded (3 functions)

| Function | Reason |
|---|---|
| `pause()` | `require(msg.sender == guardian, ...)` (OptimismPortal.sol line 172). Only the guardian (`0x4f72ee94B8ba3Be7F886565d3583A7F636c58B05`, a contract) can call it; it reverts for any other signer. |
| `unpause()` | Same guard, line 179. |
| `initialize(address,address,address,bool,address)` | `reinitializer(Constants.INITIALIZER)` (line 139). It runs once per upgrade, by the proxy admin; it reverts for everyone else. |

The lint also warns about the proxy's own `admin()`, `changeAdmin(address)`, `implementation()`, `upgradeTo(address)`, `upgradeToAndCall(address,bytes)`. They are the EIP-1967 `Proxy` contract's admin interface (`src/universal/Proxy.sol`), callable only by the proxy admin; they are not part of the OptimismPortal ABI the helper imports, so they are not in the decisions file and are not described.

### Hidden fields (all written as `visible: "never"`)

`proveWithdrawalTransaction` and `finalizeWithdrawalTransaction` take the withdrawal as a struct `_tx`. The contract hashes the whole struct (`Hashing.hashWithdrawal(_tx)`, lines 243 and 318) and accepts it only if that hash is proven in the L2 state (`SecureMerkleTrie.verifyInclusionProof`, lines 272-277) or was proven before (`provenWithdrawal.timestamp != 0`, line 324). A dapp cannot change any struct member without the call reverting, so the hidden members cannot make the screen false.

| Field | Where | Reason |
|---|---|---|
| `_tx.nonce` | both | Withdrawal nonce, part of the bound hash; the signer does not choose it. |
| `_tx.gasLimit` | both | Minimum gas the L1 call gets at finalization (`SafeCall.callWithMinGas`, line 385); bound by the hash; it does not change what moves. |
| `_tx.data` | both | Calldata of the L1 call; bound by the hash (see "What the screens say" for what it carries). |
| `_l2OutputIndex` | prove | Index of the L2 output the proof is checked against (line 235); a mismatch reverts (lines 238-240). |
| `_outputRootProof.{version,stateRoot,messagePasserStorageRoot,latestBlockhash}` | prove | Proof material; `hashOutputRootProof` must equal the oracle's root (lines 238-240). |
| `_withdrawalProof.[]` | prove | Merkle proof nodes; a wrong proof reverts (lines 272-277). |
| `hintId` | finalize | Checkpoint lookup hint for the yield manager. `WithdrawalQueue._calculateClaimableEther` reverts with `InvalidHint` unless `hintId` is exactly the checkpoint that contains the withdrawal's request (checks `_hintId == 0`, `_hintId > lastCheckpointId`, `_requestId < checkpoint.fromRequestId`, `_requestId >= nextCheckpoint.fromRequestId`). It can make the call fail; it cannot change the amount paid. |

### Pinned arguments (`mustMatch`)

None. Every argument that could switch a shown statement off is either shown (`depositTransaction`: all five arguments and `@.value` are visible) or cryptographically bound (the `_tx` struct, above). `hintId` only selects a checkpoint and reverts when wrong, so there is nothing to pin.

## What the screens say

### `depositTransaction(address _to, uint256 _value, uint64 _gasLimit, bool _isCreation, bytes _data)` — payable

Sentence: **"Deposit {@.value} to Blast and send {_value} on L2 to {_to}"**. Fields: Deposit Amount (`@.value`, `amount`), L2 Recipient (`_to`, `addressName` eoa/contract), ETH to Send on L2 (`_value`, `amount`), L2 Gas Limit (`_gasLimit`, raw), L2 Transaction (`_isCreation`, enum `depositKind`: true = "Contract creation", false = "Transfer or call"), L2 Call Data (`_data`, raw).

- `@.value` is what leaves the signer on L1. It is forwarded to the yield manager (lines 470-473) and encoded as the L2 mint (`opaqueData = abi.encodePacked(msg.value, _value, ...)`, line 466), so the mint equals `msg.value` exactly. The `_to == L2_BLAST_BRIDGE` branch (lines 459-467), where the mint is `_value` instead, reverts for every caller but the Blast bridge (line 460-463), so a wallet signer never reaches it.
- `_value` is the ETH value of the derived L2 call, paid from the depositor's L2 balance (which includes the mint). It is shown as its own amount, not merged with `@.value`, because the two can differ. The sentence says "send ... on L2" so the signer does not read it as a second L1 payment. It is exact: the L2 transaction carries exactly `_value` or fails.
- `_data` runs on Blast from the depositor's own L2 account against `_to`. That is an L2 transaction the signer authorizes, so it stays visible. The spec's `calldata` format (`calleePath: _to`, `chainId: 81457`, `amountPath: _value`) would describe it properly; the helper rejects it (`UNSUPPORTED_FORMAT: calldata is not a supported format`), which is a tool limitation, so the field is shown as raw bytes.
- `_isCreation = true` forces `_to == address(0)` (lines 424-426); the enum makes that case readable next to the zero recipient.
- `_gasLimit` must be at least `21000 + 16 * data.length` (line 430); it is shown raw because the L1 gas burned for it (`metered` modifier) is bounded by the transaction's own gas limit, which the wallet shows anyway.
- Caveat the spec cannot express: when the signer is a contract (a Safe), the mint is credited to the aliased address (lines 438-442). See SPEC-LIMITS.md.

### `proveWithdrawalTransaction(_tx, _l2OutputIndex, _outputRootProof, _withdrawalProof)`

Sentence: **"Prove withdrawal of {_tx.value} from {_tx.sender} to {_tx.target}"**. Fields: Requested Amount (`_tx.value`, `amount`), L1 Recipient (`_tx.target`), L2 Sender (`_tx.sender`).

- Proving is permissionless and moves nothing of the signer's. Its effect is to register the withdrawal and, on the first proof of a withdrawal with value, to request `_tx.value` from the ETH yield manager's queue (`yieldManager.requestWithdrawal(_tx.value)`, lines 282-283). The label "Requested Amount" names that effect.
- `_tx.target` is the L1 address that will be called with the ETH at finalization (line 385); `_tx.sender` is the L2 account that initiated the withdrawal (the L2CrossDomainMessenger `0x4200…0007` for every bridge withdrawal). Both get `addressName` with types `eoa`/`contract`, no `sources` restriction.
- Guards the sentence relies on: target may not be the portal (line 231) nor the yield manager (line 289); re-proving is allowed only after the output root changed (lines 252-256).

### `finalizeWithdrawalTransaction(uint256 hintId, _tx)`

Sentence: **"Finalize withdrawal of up to {_tx.value} from {_tx.sender} to {_tx.target}"**. Fields: Maximum Amount (`_tx.value`, `amount`), L1 Recipient, L2 Sender.

- The portal claims the ETH from the yield manager and forwards what it actually received: `txValueWithDiscount = address(this).balance - etherBalance` (lines 372-376), then `callWithMinGas(_tx.target, _tx.gasLimit, txValueWithDiscount, _tx.data)` (line 385). The claimed amount is `nominal * checkpoint.sharePrice / 1e27` (`WithdrawalQueue._calculateClaimableEther`), and `_finalize` reverts with `InvalidSharePrice` when `sharePrice > 1e27`; `YieldManager.sharePrice()` (lines 378-384) is `value / (value + accumulatedNegativeYields)`, so it is at most 1. The payout is therefore at most `_tx.value`, never more: the label says "Maximum" and the sentence says "up to".
- Finalization is permissionless; the finalizer's own assets do not move. The claims replay confirms it: in the real ETH finalization the finalizer was also the end beneficiary and "sender received 1050000000000000" while the screen said "at most 1050000000000000".

### The common case: bridge withdrawals show the messenger as recipient

Almost every withdrawal on this portal is a bridge message: `_tx.sender` = L2CrossDomainMessenger, `_tx.target` = L1CrossDomainMessenger (`0x5D4472f31Bd9385709ec61305AFc749F0fA8e9d0`, per Blast's docs), and the end beneficiary and token sit inside `_tx.data` → `relayMessage(...)` → `finalizeBridgeETH/ERC20(...)`, two levels down. The descriptor shows the portal-level truth (value and the messenger) and names the messengers in the tests' `addressNames` so the renderings read "from L2CrossDomainMessenger to L1CrossDomainMessenger". Decoding the inner message would need the spec's `calldata` format (one level, supported by the spec) plus descriptors for `L1CrossDomainMessenger.relayMessage` and the bridges; the helper does not support the format and the registry has no such descriptors. That is a tool and ecosystem limitation, recorded here, not in SPEC-LIMITS.md. Because both calls are permissionless and the struct is hash-bound, the gap cannot be used against the signer's own funds; the worst case is paying gas to prove or finalize someone else's withdrawal.

## Deployments

| Chain | Address | Evidence |
|---|---|---|
| 1 (Ethereum) | `0x0Ec68c5B10F21EFFb74f2A5C61DFe6b08C0Db6Cb` | Sourcify full match of proxy and implementation; Blast docs list it as the mainnet OptimismPortal; live `l2Oracle()`/`systemConfig()`/`version()` read as described above. |

**Candidates not added**

- **Blast Sepolia portal on Sepolia (chain 11155111), `0x2757E4430e694F27b73EC9C02257cab3a498C8C5`** (listed in Blast's docs, live `version()` = "1.10.0", `l2Oracle()` = `0x311fF72DfE214ADF97618DD2E731637E8F41bD8c`). Not added: its implementation `0x05167e2D02022AdBeE1f4F97aA9503F6848dC55c` is not verified on Sourcify (HTTP 404), so the verified source cannot be compared and the registry linter could not fetch an ABI for it; its runtime bytecode also differs from mainnet's (36188 vs 36464 hex characters), so it is not the same build. It is also a testnet.
- No other chain has this contract: an OptimismPortal is specific to one L2, and Blast has one mainnet portal.

## Tests

`bundle/registry/blast/testsv2/calldata-OptimismPortal.tests.json`, 5 cases, all on chain 1. `dataProvider.addressNames` names the three messenger/predeploy contracts (addresses from Blast's docs and the OP-stack predeploy table).

| Case | Kind | Transaction | What it shows |
|---|---|---|---|
| `proveWithdrawalTransaction - chain 1` | real | `0x9d2d0f0773011eab78383366d96545f3d16c01c4dfd4f4b7655000fa10c20645` | 0.001041 ETH bridge withdrawal, messenger to messenger |
| `finalizeWithdrawalTransaction-eth - chain 1` | real | `0xb1ac3b0e814465d8fb6ee8c16cb52dfc94e3a2a224287c78f823a32c8cfbe779` | ETH finalization, "up to 0.00105 ETH", `hintId` 708 hidden |
| `finalizeWithdrawalTransaction - chain 1` | real | `0x4ad03ceacd8c6d8eebe66efd55204bc43b96fd70ae711066d8ec51c04864722a` | ERC-20 (DAI) bridge finalization: value 0 ETH, token inside nested data |
| `depositTransaction - chain 1` | real | `0x655e2c9909ada76460329b3c9369f511f5bca6178cfb9d3f15d94201c59a7af0` | 0 ETH deposit that calls L2ToL1MessagePasser with 0.0000349 ETH of L2 value and raw call data |
| `depositTransaction-eth - chain 1` | encoded | none | 0.1 ETH deposit to the sender's own address, empty data. Encoded because none of the last 1000 portal transactions (blocks 26282314-26291418) is a direct `depositTransaction` with `msg.value > 0`; users deposit through the L1 bridges. Sender is a real portal user (`0x01eD5c94DE39E73C986b98B85C2c0A3d1BEDff7D`). |

Real transactions: 4. Encoded: 1.

## Checks

- **Helper:** clear-signing-helper 0.6.0-preview.6; Foundry cast 1.5.1.
- **Lint:** `erc7730 lint --require-verified` at the clone's pin (`sourcifyeth/python-erc7730@964176e28918299dfecb269e20a267a652ada475`): exit 0, **0 errors, 10 warnings**: 1 "Display intent too long" covering the three interpolated intents (59, 74 and 65 characters; kept because each states the amount and both parties), and 7 "Missing display format" for `initialize`, `pause`, `unpause` (excluded, see above) and the proxy's `admin`, `changeAdmin`, `implementation`, `upgradeTo`, `upgradeToAndCall`. The ABI was fetched (no "Could not fetch ABI").
- **Registry runners** (pins read from the clone at `d0f354b1721382206bfd03951042e4401caae727`): Sourcify `@ethereum-sourcify/clear-signing@0.3.0` (ref `9d6d2fe4715d53e002bb966f6593e1fbc44b53c7`) **5/5 pass**; Rust `llbartekll/clear-signing@0.1.0` (ref `65af2281aa1366e1d770f9ac445007e56dbe29ca`) **5/5 pass**. Logs under `bundle/review/runners/`.
- **Strict portability:** `--strict-portability` produced no findings (the `bytes[]` proof array is hidden). No function was dropped for it.
- **Claims replay:** `clear-signing claims` on `https://eth.drpc.org` failed on the first fixture with a transport error (`peer closed connection without sending TLS close_notify`); the rerun on `https://mainnet.gateway.tenderly.co` completed: depositTransaction 55 runs, finalizeWithdrawalTransaction-eth 165 runs, finalizeWithdrawalTransaction 110 runs, proveWithdrawalTransaction 115 runs, **0 findings**. The encoded deposit fixture is not replayed (no txHash). Notes from the run: "ETH to Send on L2" is reported "unmoved" on L1, which is expected because it is the L2 call value; "Maximum Amount" holds in the ETH finalization. Flashbots was not needed.
- **Helper check warnings:** 3 `INTENT_LENGTH` (same as lint). No `SENTENCE_OMITS`, `LIMIT_WORDING`, `TAIL_SLICE_TOKEN` or `PERMIT_GRANT_HIDDEN`.
- **Did not run / not performed:** wallet or device rendering; any Blast-team review; a Sepolia test case (candidate rejected, above). `registryMatches` from `init` was read indirectly: the clone has no descriptor with these selectors and no mention of the address.
- **Tool limitation:** the helper rejects the spec's `calldata` field format (`UNSUPPORTED_FORMAT`), so embedded calls (`_data` on deposit, `_tx.data` on withdrawals) cannot be described even one level deep.

## Flags for the integrator

- The three interpolated intents exceed 30 characters (lint warning only).
- For bridge withdrawals the screen names the L1CrossDomainMessenger as recipient; the end beneficiary is inside hidden, hash-bound call data. Both calls are permissionless and cannot move the signer's funds.
- Finalization pays at most `_tx.value`; the real amount is `value × sharePrice`, read from the yield manager at finalization.
- A contract-wallet depositor's ETH is credited on Blast to the aliased address, not to the wallet's own address.
- Traffic to selectors that are not in this ABI reverts: `0xfa92670c` = `depositTransaction(address,uint256,uint256,bool,bytes)` (the OP Mainnet signature with `uint256` gas limit), 6 failed calls in the last 1000 transactions; the brief's single legacy `finalizeWithdrawalTransaction((...))` call is the same kind of mistake. No descriptor can make those succeed.

## Update: embedded calls (`calldata` format) and three new descriptors

Paste this section into PR #3172. It supersedes the earlier text on `_tx.data` and on the partial screen for bridge withdrawals.

**Coverage.**
- **OptimismPortal:** the same functions as before. On prove and finalize, `_tx.data` is now a visible `calldata` field with callee `_tx.target`, amount `_tx.value` and spender the portal (OptimismPortal.sol line 385 calls the target from the portal). Finalize pays `txValueWithDiscount`, which is at most `_tx.value` (lines 371-376), so the "maximum" wording stays. On prove, the field shows the call that finalization will make; the data is bound by the withdrawal hash (lines 243, 272-277). `depositTransaction._data` stays raw, because the v2 schema has no cross-chain `chainId` for embedded calldata.
- **New `calldata-L1CrossDomainMessenger.json`:** proxy `0x5D4472f31Bd9385709ec61305AFc749F0fA8e9d0` (ResolvedDelegateProxy, implementation `0x84efcFCE2dEe08072d5D57BF232D379b6E92A836`, version 1.7.1). Describes `sendMessage` and `relayMessage`. `relayMessage._message` is a `calldata` field with callee `_target`, amount `_value` and spender the messenger (L1CrossDomainMessenger.sol line 148). `initialize` is excluded.
- **New `calldata-L1StandardBridge.json`:** proxy `0x697402166Fbf2F22E970df8a6486Ef171dbfc524` (L1ChugSplashProxy, implementation `0xD2C23A5A280AFF9182b953579f62EDdDF1c7ff22`, version 1.4.1). Describes the 8 deposit and bridge functions and the 4 finalize functions. `initialize` is excluded.
- **New `calldata-L1BlastBridge.json`:** proxy `0x3a05E5d33d7Ab3864D53aaEc93c8301C1Fa49115` (L1ChugSplashProxy, implementation `0x7A2075519Dd9598b62075FD397aF0Dd34b14619a`, version 1.0.0). Describes 4 bridge functions and 2 finalize functions. `initialize`, `setETHYieldToken` and `setUSDYieldToken` are excluded.
- All addresses come from Blast's docs and are full matches on Sourcify (solc 0.8.15). Each descriptor binds only the proxy on chain 1.
- **Hidden fields:** gas limits (a failed relay can be replayed), nonces (bound by the hash), opaque `_extraData` (only emitted), and the local token (it is the ticker of the amount).

**What the screens say.**
- A withdrawal now renders in three levels: the portal value, then the messenger "Relay up to X from <L2 bridge> on Blast to <L1 bridge>", then the bridge payout with Maximum Amount, Paid To and Withdrawn By. For USDB, the last level is "Queue DAI claim for Blast USDB", because the bridge calls `usdYieldManager.requestWithdrawal(_to, _amount)` (L1BlastBridge line 209) and the later claim is scaled by the share price.
- Every ETH amount after the portal is a maximum, because Blast pays a discounted value. The bridge pays `msg.value`, which is at most `_amount` (L1StandardBridge lines 180 and 190, L1BlastBridge lines 163 and 173).
- The finalize screens describe someone else's withdrawal. The signer's own funds do not move.
- Bridge deposits: "Bridge {amount} to your address on Blast" or "… to {_to} on Blast". The variants without `To` are `onlyEOA` (StandardBridge line 107), so the recipient is the same address on Blast. The ERC-20 amount is exact (lines 352-354). "Token on Blast" shows `_remoteToken` raw, because it is an L2 address.
- On L1BlastBridge, `_extraData` of a USDC or USDT bridge is a minimum output (USDConversions lines 138-142). It is shown raw as "Min Out (USDC/USDT)".

**Tests.**
- OptimismPortal 4 cases: real `0x655e2c99…7af0` (deposit with data), `0x177478d9d2f2391e649f941b441c4e4786679b109acee84a30698e62a27f8cab` (finalize to an EOA) and `0x5587fdcb02a0cfe0c93ef259c5b6cfe088371857e96b3cd2cbc89a9a2cb59632` (prove to an EOA), and one encoded ETH deposit.
- L1CrossDomainMessenger 3 cases: real `sendMessage` `0xf995205a372fbc76d4fe89bd1af2091432d04916bc0607f8e0c01967888c522e` and `0xf29204a885aa026222a1c6ef57593cf7477a1e4227aa18b6bb04ba9ce24e2922`, and one encoded `relayMessage` to an EOA. HyperSync found no successful direct `relayMessage` on the whole chain.
- L1StandardBridge 12 cases: 8 real deposits, and 4 encoded finalize calls whose arguments come from the inner messages of real withdrawals `0x9e471368…` and `0x760b0a26…`. The finalize functions are never called directly.
- L1BlastBridge 8 cases: 5 real (stETH, USDT, DAI, `bridgeETH`, `bridgeETHTo`), and 3 encoded (`bridgeERC20To`, never called directly, and the two finalize functions with arguments from `0xb1ac3b0e…` and `0x4ad03cea…`).
- Real nested withdrawals render correctly in both runners, down to the bridge payout, but cannot be committed because of the runner conflict on nested `interpolatedIntent`: `0xb1ac3b0e814465d8fb6ee8c16cb52dfc94e3a2a224287c78f823a32c8cfbe779`, `0x4ad03ceacd8c6d8eebe66efd55204bc43b96fd70ae711066d8ec51c04864722a`, `0x9d2d0f0773011eab78383366d96545f3d16c01c4dfd4f4b7655000fa10c20645`, `0x9e471368362428caa8d164d185a08afa759a5a204309978d29709ff771c786d3`, `0x760b0a2658e02bd71553b2ab47f92074f70463fd25aa83c493e6c0221179748d`, `0xc88535ff48b9e54ce265776794736e6ff75af7a4d81da17a2f83f6f024d64186`.

**Checks.**
- Lint at the registry pin: 0 errors in all four files. The warnings are intent length, missing formats for proxy-admin and excluded functions, and "Unknown selector", because the linter reads the unresolved proxy ABI from Sourcify.
- Both registry runners pass every case: OptimismPortal 4/4, L1CrossDomainMessenger 3/3, L1StandardBridge 12/12, L1BlastBridge 8/8.
- The new descriptors were built with clear-signing-helper 0.6.0-preview.6 (`--strict-portability --registry-runners`, no portability findings). Claims replayed 18 real fixtures with 0 findings. A language-model agent added the `calldata` fields by hand, because the helper does not support that format.

## Update: gas unit and aliasing note on `depositTransaction`

Add this to the PR description as well.

- **L2 gas limit:** `_gasLimit` now uses the ERC-7730 `unit` format with `base: "gas"`, instead of `raw`. It is a number of gas units, not an amount of ETH, so `amount` would be wrong. Both runners render it like the spec's `unit` example, without a space, for example `100000gas`.
- **Aliasing note:** `depositTransaction` now opens with a constant field, `{ "label": "Note", "value": "From a contract wallet, the ETH is credited to its aliased address on Blast.", "format": "raw" }`. A field with a literal `value` and no `path` is allowed by the spec to display a constant. The portal credits a non-EOA sender's ETH to its L1-to-L2 alias, the address plus `0x1111000000000000000000000000000000001111`, not to the same address on Blast. A Safe user who expects the ETH at the Safe's own address on Blast would otherwise be surprised.
- **Tests:** the expected screens of both `depositTransaction` cases include the note and the new gas format. The full CI check passes, and both runners pass every case.

