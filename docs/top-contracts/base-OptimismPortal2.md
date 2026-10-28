> **Draft.** A registry contributor wrote this descriptor for the registry's top-contracts effort. The Base team and Optimism did not submit it. It stays a draft until maintainers decide how to review and label descriptors for contracts the submitter does not own. It was generated with clear-signing-helper. A language-model agent filled in the judgment choices. No human has reviewed it yet.

# Base Portal (OptimismPortal2): clear-signing descriptor

## Summary

This adds `registry/base/calldata-OptimismPortal2.json` and its `testsv2` file for the Base OptimismPortal on Ethereum mainnet, `0x49048044D57e1C92A77f79988d21Fa8fAF74E97e`.

- The address is an EIP-1967 proxy. Its implementation is `OptimismPortal2` 6.0.1 at `0x03863Ab7F64B733cFF85C8fF44a86601C568Ca70`. Sourcify has a full match, and `version()` returns `"6.0.1"` on chain.
- The portal handles about 5k transactions a week: proofs and finalizations of Base-to-Ethereum withdrawals, and direct ETH deposits to Base.
- The registry had no descriptor for it. `init --registry` reported no `registryMatches`, and no file in the clone (at `b70998c`) mentions the address or `OptimismPortal`.
- Five user functions are described and one admin function is excluded.
- Two `depositTransaction` arguments are pinned with `mustMatch`.
- All 11 test cases are real mainnet transactions.

## Coverage

### Described functions

| Function | Intent | interpolatedIntent |
|---|---|---|
| depositTransaction(address,uint256,uint64,bool,bytes) | Deposit ETH to Base | Bridge {@.value} to Base, send {_value} to {_to} |
| donateETH() | Donate ETH to portal | Donate {@.value} to Base portal, not bridged |
| proveWithdrawalTransaction(...) | Prove Base withdrawal | Prove Base withdrawal of {_tx.value} to {_tx.target} |
| finalizeWithdrawalTransaction(...) | Finalize Base withdrawal | Finalize Base withdrawal of {_tx.value} to {_tx.target} |
| finalizeWithdrawalTransactionExternalProof(...) | Finalize Base withdrawal | Finalize Base withdrawal of {_tx.value} to {_tx.target} |

### Excluded functions

| Function | Reason |
|---|---|
| initialize(address,address) | A reinitializer that only the ProxyAdmin or its owner can call (`_assertOnlyProxyAdminOrProxyAdminOwner`, OptimismPortal2.sol line 231). It is an upgrade step, not a user call. HyperSync found no direct call to it in the whole chain history. |
| Proxy ABI: admin(), changeAdmin(address), implementation(), upgradeTo(address), upgradeToAndCall(address,bytes) | These are functions of the EIP-1967 proxy, and only its admin can call them. They are not in the implementation ABI the descriptor describes. Lint lists them as "Missing display format". |
| receive() | It has no calldata. A plain ETH transfer deposits to the sender's own L2 address (lines 318-320). |

### Hidden fields (`visible: "never"`)

| Function(s) | Field | Reason |
|---|---|---|
| prove, finalize, finalizeExternalProof | `_tx.nonce` | Bookkeeping value of the L2 withdrawal. It is part of the withdrawal hash, and the signer does not choose it. |
| prove, finalize, finalizeExternalProof | `_tx.gasLimit` | The minimum gas the portal forwards to the target (`SafeCall.callWithMinGas`, line 480). It is set on L2 and fixed by the withdrawal hash. |
| prove, finalize, finalizeExternalProof | `_tx.data` | The call data the target receives. It is fixed by the withdrawal hash that the L2 inclusion proof commits to (lines 385-410), and the signer cannot change it. The wallet cannot decode it (see "Partial screen for bridge withdrawals"). |
| prove | `_disputeGameIndex`, `_outputRootProof.*`, `_withdrawalProof.[]` | Proof data. A wrong game index or output root proof reverts (lines 354-382). A wrong Merkle proof reverts (lines 401-410). None of these moves funds. |
| finalizeExternalProof | `_proofSubmitter` | Selects whose earlier proof the finalization uses (line 465, `checkWithdrawal`). It does not change the recipient or the amount, which come from `_tx` (line 480). |

Every amount and recipient stays visible:

- **Withdrawals:** `_tx.value`, `_tx.target`, `_tx.sender`
- **Deposits:** `@.value`, `_value`, `_to`, `_gasLimit`

### Pinned arguments (`mustMatch`)

| Function | Argument | Pin | Why |
|---|---|---|---|
| depositTransaction | `_data` | `"0x"` | With call data, the L2 deposit calls `_to` with a payload the wallet cannot decode. That payload could, for example, move the signer's L2 tokens. "send {_value} to {_to}" is complete only for a plain value transfer. A deposit with data is not clear-signed; the wallet falls back to blind signing. In the latest 5,000 portal transactions, 1 of 40 successful deposits carried data. |
| depositTransaction | `_isCreation` | `false` | A creation deposit deploys a contract on L2 and sends `_value` to that contract, not to `_to` (`_to` must be zero, line 570). The screen would then be false. No creation deposit was in the sample. |

Both pins were checked with throwaway encoded fixtures. The renderer refused each with `MUSTMATCH_VIOLATION`. The throwaway fixtures were deleted.

## What the screens say

- **Deposit: two amounts on two chains.**
  - `msg.value` leaves Ethereum and is minted on Base to the depositor's L2 account.
  - `_value` is what the derived L2 transaction sends from that account to `_to` (NatSpec lines 546-547; both go into `opaqueData`, line 597).
  - They can differ: 5 of 40 sampled deposits had `_value != msg.value`.
  - The screen shows both amounts, "ETH to Bridge" (`@.value`) and "ETH Sent on L2" (`_value`), plus "L2 Recipient" (`_to`).
  - The split-value test (tx `0xb3cd54e8…`) shows 0.00017 ETH bridged and 0.00004 ETH sent to another address. The remainder stays on the sender's L2 account.
  - L1 places no limit on `_value`. On L2 it is paid from the depositor's L2 balance. Because it is shown in full, a dapp cannot drain the signer's existing L2 balance unseen.
- **Deposit: `_gasLimit` is shown raw as "L2 Gas Limit".** It is L2 gas bought by burning L1 gas (`metered`, line 562). The minimum is `21000 + 40 * data length` (line 576).
- **The currency is ETH on both chains.** `SystemConfig(0x73a79Fab…).isFeatureEnabled("CUSTOM_GAS_TOKEN")` returned `false` on chain. The custom-gas-token branches (lines 349-351, 445-447, 564-566) are therefore inactive. The spec cannot name the chain of an `amount` (see the spec-limitation notes), so the label says "on L2".
- **Withdrawals are worded around the withdrawal, not the signer.**
  - Most prove and finalize calls are sent by relayers.
  - Finalizing pays `_tx.value` to `_tx.target` with `_tx.data` (line 480), whoever signs.
  - The sentence therefore names the amount and the L1 recipient, never "you receive".
  - `_tx.sender` is shown as "L2 Sender".
- **Withdrawal values cannot be spoofed.**
  - `_tx` is hashed (lines 385 and 462).
  - Prove requires the hash to be in the L2ToL1MessagePasser storage (lines 401-410).
  - Finalize requires a matured proof of the same hash (`checkWithdrawal`, lines 506-540).
  - A `_tx` that L2 did not create reverts.
- **Prove moves no funds.** The intent says "Prove". The claims replay saw no balance change on prove.
- **A failed target call still finalizes.** If the target call fails and the target is not a 7702-delegated EOA, the withdrawal is still marked finalized, and the ETH is not delivered (lines 468, 480-493). The screen states the withdrawal that is executed, not a promise of delivery. This is protocol behaviour.
- **Partial screen for bridge withdrawals.**
  - Nearly all sampled withdrawals target the Base L1CrossDomainMessenger (`0x866E82a6…`) from L2CrossDomainMessenger (`0x4200…0007`). That covers all but 1 of 54 `finalizeWithdrawalTransaction` calls, and all prove and external-proof calls.
  - Their `_tx.data` is a `relayMessage` call. It holds the final recipient, and for tokens a further `L1StandardBridge` call.
  - The screen shows the ETH amount and "Base L1CrossDomainMessenger". That is true, but it is not the final user.
  - The ERC-7730 `calldata` format could express this (`calleePath: "_tx.target"`, `amountPath: "_tx.value"`). But the helper rejects that format, and no messenger descriptor exists (tool limitation).
  - The names "Base L1CrossDomainMessenger" and "L2CrossDomainMessenger" come from Base's contract list on docs.base.org. They exist only in the tests' data provider.
- **Donation.** `donateETH` adds ETH to the portal without a deposit (lines 322-325). "not bridged" warns a signer who expected a deposit.
- **Smart-contract signers.** If a contract (for example a Safe) deposits, the L2 `from` is the aliased address (lines 589-592). The bridged remainder belongs to that alias, not to the same address on L2. The screen does not show this.

## Deployments

| Chain | Address | Evidence |
|---|---|---|
| 1 | 0x49048044D57e1C92A77f79988d21Fa8fAF74E97e | Listed as Base's OptimismPortal on docs.base.org. Sourcify match for the proxy, with implementation OptimismPortal2 `0x03863Ab7…` (`cast implementation` agrees). `version()` returns 6.0.1. Lint fetched the ABI with `--require-verified`. |

No extra deployments were added. The same address has code elsewhere, but it is a different contract:

| Candidate | Why not added |
|---|---|
| Base 8453 | `ERC1967Proxy` whose implementation is a `Recovery` contract `0xd6Cd8A71…` (Sourcify). `version()` reverts. This is an address collision, not a portal. |
| OP Mainnet 10 | Same implementation `0xd6Cd8A71…`. Not on Sourcify, and `version()` reverts. |
| Arbitrum 42161 | `ERC1967Proxy` with a `Recovery` implementation `0xb2a7C279…` (Sourcify). `version()` reverts. |
| Polygon 137, BNB 56 | No code at the address. |

## Tests

All 11 cases are real, successful mainnet transactions. None is encoded.

| Case | txHash | Covers |
|---|---|---|
| depositTransaction | 0x33ee24f93ce20c818eeff2b7e77e93e8950de00a71bda607acdb3fa5fb036afd | `_value == msg.value`, to self |
| depositTransaction-split-value | 0xb3cd54e86f1d0d2a754ecffd8761e14aa1b3a42a708f0bc0e09aa1a6d03874a2 | `_value` < `msg.value`, other recipient |
| donateETH | 0x6568dd3e85ab50fd17c26f46237a2714ef6c547207102b26af034f7b53a73dc3 | 0.02 ETH donation (block 17689679, an earlier implementation behind the same proxy; same argument-free selector) |
| proveWithdrawalTransaction | 0x6856507ed80fb7713e4580dd8dfd1abbe913bbf72ef2cb26a56c8e8488a4c368 | Messenger withdrawal, 0 ETH |
| proveWithdrawalTransaction-eth-bridge | 0x02ba2ec7144a9fb0c8e9c13ec3e7cb23a81b126d1d1b24f33a67643b67eadbf2 | Messenger withdrawal, 4150 ETH |
| proveWithdrawalTransaction-eth-direct | 0xbd96e6028b559068442c31846acf05626ee7c3c8c7ec6b9498b137c6a7f5f8fc | Direct ETH withdrawal to an EOA, 11.889528 ETH |
| finalizeWithdrawalTransaction | 0xd823f4f0426f64698217a908be92f1b0251db28c5eb06b6070567fd75bfe5880 | Messenger withdrawal, 0 ETH |
| finalizeWithdrawalTransaction-eth-bridge | 0x9cb27abb93496e7236b533f358c14214ada63ba8b2f04395f9bb34cebb402ea2 | Messenger withdrawal, 236.79 ETH |
| finalizeWithdrawalTransaction-eth-direct | 0xffbbfdca6ab2398d1c9855731072c9efa1383c36fb4562eea9c51b6904764cd4 | Direct withdrawal, 0.0094 ETH, empty data |
| finalizeWithdrawalTransactionExternalProof | 0x2d20e4b800cb4fec50f078113fdb7a1740742885856571a154aa16ba3b2c7313 | Messenger withdrawal, 0 ETH |
| finalizeWithdrawalTransactionExternalProof-eth-bridge | 0xacb91a2fe358193d7096ffcf30e249fa187a5f781eb841dafd7771326882ce89 | Messenger withdrawal, 4000 ETH |

How the cases were found:

- `discover` (Envio HyperSync, blocks 0-26291416) gave one case per function.
- The extra cases come from the latest 5,000 portal transactions (Etherscan API, blocks 26246761-26291421). They cover withdrawals that carry ETH, direct withdrawals, and a split-value deposit.
- The donation that `discover` found carried 0 ETH. It was replaced with a 0.02 ETH donation found on HyperSync.

## Checks

- **Tool:** clear-signing-helper 0.6.0-preview.6 (renderer `@ethereum-sourcify/clear-signing@0.2.2+signed-int-fix.1`).
  - Export ran with `--strict-portability --registry-runners --registry <clone b70998c> --entity base`.
  - The portability check has no findings.
- **Lint:** `erc7730 lint --require-verified`, pinned to `sourcifyeth/python-erc7730@964176e28918299dfecb269e20a267a652ada475`.
  - Exit 0, **0 errors, 7 warnings**:
    - 1 "Display intent too long", covering the four sentences above 30 characters (they name every shown amount and recipient).
    - 6 "Missing display format", for `initialize` and the five proxy-admin functions.
  - Lint fetched the ABI: no "Could not fetch ABI" warning.
- **Runners** (revisions pinned in the registry CI):
  - Sourcify `@ethereum-sourcify/clear-signing@0.3.0` @ `9d6d2fe4715d53e002bb966f6593e1fbc44b53c7`: **11/11 pass**
  - Rust `llbartekll/clear-signing@0.1.0` @ `65af2281aa1366e1d770f9ac445007e56dbe29ca`: **11/11 pass**
- **Claims replay** (anvil fork of https://eth.drpc.org, 11 fixtures, 801 runs): **4 findings, all on `depositTransaction._value`.** All resolved as expected behaviour; the wording is kept.
  1. Baseline split-value case: "recipient received 0". `_value` is transferred by the derived L2 transaction (line 597, NatSpec 546-547), which an L1 fork cannot observe.
  2. Varying `_gasLimit` to 50000: the same observation as 1.
  3. and 4. "exact `_value`": a doubled `_value` still succeeds on L1. That is correct, because L1 does not check `_value`. On L2 it is paid from the depositor's L2 balance, or the L2 call fails and the funds stay with the depositor. The screen shows the exact L2 send amount and does not claim a bound by `msg.value`.

  No findings for:
  - `@.value`: the bridged amount and the donation hold exactly.
  - Withdrawals: the replay varied every hidden field (`_tx.nonce`, `_tx.gasLimit`, `_tx.data`, the proof fields, `_proofSubmitter`). No variation succeeded with a false screen.
  - `_to` and `_tx.target`.

  "Unmoved" results:
  - Prove: correct, because prove moves no ETH.
  - Finalizations to the messenger: the replay measures the sender, while the ETH moves portal → messenger → final user.
  - `finalizeWithdrawalTransaction-eth-direct` did deliver to a measured account, and it matched the screen exactly (0.0094 ETH).
- **Tool limitation:** the helper and the registry runners do not support the ERC-7730 `calldata` format, and no L1CrossDomainMessenger descriptor exists. That is why `_tx.data` stays hidden on bridge withdrawals.
- **Did not run:**
  - No physical-wallet or Ledger test.
  - No registry CI or AI review, because no PR was opened.
- **Spec limitation:** see `docs/spec-limitations/base-OptimismPortal2.md` (the chain of a native `amount`).
