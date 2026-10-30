# Across Protocol — Ethereum SpokePool (calldata-Ethereum_SpokePool.json)

> **Draft.** Written for the registry's top-contracts effort, not submitted by the Across team. The Across team has not reviewed the wording. An account tied to Across Protocol should open the PR; maintainers check ownership.

## Summary

- Contract: `Ethereum_SpokePool` behind an `ERC1967Proxy` at `0x5c7BCd6E7De5423a257D81B442095A1a6ced35C5` on Ethereum (chain 1). The descriptor binds the proxy. Implementation at export time: `0x456Ac26E5ec083EE9889eBa0d1a0A582502B8e84`, Sourcify exact match, solc 0.8.30, `contracts/spoke-pools/Ethereum_SpokePool.sol`. The proxy is UUPS and the owner (the Across HubPool) can upgrade it; an attestation should pin the implementation.
- Traffic (erc7730.sourcify.dev, 7 days to 2026-10-27): 21,425 transactions, of which 6,345 `depositV3`, 1,601 `deposit`, 13,443 `fillRelay` (relayers).
- Described: the five deposit entry points a user calls (`deposit`, `depositV3`, `depositNow`, `depositV3Now`, `unsafeDeposit`) and the two speed-up functions (`speedUpDeposit`, `speedUpV3Deposit`). Excluded: 28 functions for relayers, settlement bots and the HubPool owner, plus removed and nested-calldata functions.
- The screen says what the signer pays (exact), to which chain, to which recipient, and which account controls the deposit. The output amount and output token are shown raw, labelled as raw, because they are denominated on the destination chain. Deposits that carry a `message` (destination-side contract calls) are refused by `mustMatch`, so they fall back to blind signing instead of showing a misleading recipient.
- Entity folder: `registry/across/`, new. Registry search (`init --registry`) found no descriptor whose functions this contract shares.

## Coverage

### Described functions

| Function | Intent | Sentence |
|---|---|---|
| `deposit(bytes32 …)` | Bridge tokens | Bridge {inputAmount} to {recipient} on {destinationChainId}; depositor {depositor} |
| `depositV3(address …)` | Bridge tokens | same |
| `depositNow(bytes32 …)` | Bridge tokens | same (Fill Window instead of Fill Deadline) |
| `depositV3Now(address …)` | Bridge tokens | same |
| `unsafeDeposit(bytes32 …)` | Bridge tokens | same |
| `speedUpDeposit(bytes32 …)` | Update bridge deposit | Update deposit {depositId} of {depositor}: {updatedOutputAmount} raw units to {updatedRecipient} |
| `speedUpV3Deposit(address …)` | Update bridge deposit | same |

Fields of a deposit, in display order: Amount to Bridge (`inputAmount`, tokenAmount in `inputToken`), Native Value Sent (`@.value`), Destination Chain (`destinationChainId`, enum), Recipient, Output Amount (raw), Output Token (dest.) (raw), Depositor, Fill Deadline (date) or Fill Window (duration). Fields of a speed-up: Deposit ID, New Output (raw), New Recipient, Depositor.

### Excluded functions

Relayer and settlement path, called by bots with funds or proofs the signer does not hold:
- `fillRelay`, `fillV3Relay`: pay a deposit's output tokens to its recipient from the relayer's balance (SpokePool.sol:986, 1007).
- `fillRelayWithUpdatedDeposit`: fills with the depositor's signed update (SpokePool.sol:1108).
- `requestSlowFill`: asks the protocol to fill from LP funds in the next bundle; moves no funds of the caller (SpokePool.sol:1157).
- `executeSlowRelayLeaf`, `executeRelayerRefundLeaf`: execute Merkle leaves of a root bundle relayed by the HubPool (SpokePool.sol:1242, 1276).
- `claimRelayerRefund`: claims a refund credited to the caller as a relayer (SpokePool.sol:1324).
- `fill(bytes32,bytes,bytes)`: deprecated ERC-7683 settler entry point; `originData`/`fillerData` are nested bytes (SpokePool.sol:1197).
- `executeAcrossV5`: reverts `V5NotGateway` unless `msg.sender` is the Gateway (SpokePool.sol:1045). `adapterExecuteAcrossV5`: callable only by the executor of a live Gateway execution (SpokePool.sol:1072).

Admin: `relayRootBundle`, `emergencyDeleteRootBundle`, `pauseDeposits`, `pauseFills`, `setCrossDomainAdmin`, `setWithdrawalRecipient`, `setOftMessenger`, `executeExternalCall` are `onlyAdmin`; on Ethereum `_requireAdminSender` is `onlyOwner` (Ethereum_SpokePool.sol:55) and the owner is the HubPool. `upgradeTo`, `upgradeToAndCall`: `_authorizeUpgrade` is `onlyAdmin` (SpokePool.sol:325). `renounceOwnership`, `transferOwnership`: Ownable. `initialize`, `__SpokePool_init`: initializers.

Other: `multicall`, `tryMulticall`: nested `bytes[]` cannot be decoded statically. `depositDeprecated_5947912356`, `depositFor`: always revert with `RemovedFunction()` (SpokePool.sol:450, 469).

### Hidden fields (reasons recorded in the bundle's provenance and `clear-signing.toml`)

- `inputToken`: shown as the ticker of Amount to Bridge.
- `quoteTimestamp` (deposit, depositV3, unsafeDeposit): the contract accepts only a time within `depositQuoteTimeBuffer` before now (SpokePool.sol:1398-1400). It sets the LP fee that the relayer pays out of the input amount; it changes neither what the signer pays nor what the recipient gets.
- `exclusiveRelayer`, `exclusivityParameter`: decide only which relayer may fill first and until when (SpokePool.sol:1417-1427; the parameter is an offset when at most `MAX_EXCLUSIVITY_PERIOD_SECONDS` = 1 year, SpokePool.sol:181, else a timestamp). They change neither what the signer pays nor the output amount nor the recipient. If nobody fills, the deposit expires at the Fill Deadline shown.
- `depositNonce` (unsafeDeposit): caller-chosen nonce that forms the deposit ID with the sender and depositor (SpokePool.sol:695); no effect on amounts or recipient.
- `depositorSignature` (speed-ups): EIP-712 signature by the depositor over the deposit ID and the shown updated values (SpokePool.sol:1560-1590, 1593-1606). It authorizes the update and carries nothing else to show.

### Pinned arguments (`mustMatch`)

- `message` in all five deposits and `updatedMessage` in both speed-ups: `mustMatch: ["0x"]`. A non-empty message makes the fill call `handleV3AcrossMessage` on the recipient, which must then be a contract (SpokePool.sol:1818-1821; NatSpec SpokePool.sol:531). "to {recipient}" then names a handler that runs arbitrary logic on arrival, not where the funds end up. The wallet hides the field when it is empty and refuses to clear-sign any other value, so deposits with destination actions fall back to blind signing. Both historical `speedUpDeposit` calls on mainnet carry a message, so this pin also covers that path (see Tests).

## What the screens say

Each item names the source that justifies it. File: `contracts/spoke-pools/SpokePool.sol` of the verified implementation unless noted.

1. **Amount to Bridge is exact.** `_depositV3` either requires `msg.value == inputAmount` and wraps it (lines 1433-1434) or requires `msg.value == 0` and pulls exactly `inputAmount` of `inputToken` from `msg.sender` (lines 1440-1441). No argument weakens either check. The `claims` replay confirms the moved amount (see Checks).
2. **Ticker from `inputToken`.** `tokenAmount` with `tokenPath: inputToken` (address variants) or `inputToken.[12:32]` (bytes32 variants). The slice is safe: the bytes32 is either compared whole to the wrapped native token (line 1432) or converted with `toAddress()` (line 1441), which reverts when the top 12 bytes are not zero (`AddressConverters.sol:10-28`). `nativeCurrencyAddress` is not used: when `msg.value` is 0 and `inputToken` is WETH, WETH itself is pulled, so the amount is in WETH; the ETH case is visible through Native Value Sent, which equals the amount.
3. **Native Value Sent** is `@.value` (payable). It is 0 for ERC-20 deposits and equal to Amount to Bridge for ETH deposits (line 1433).
4. **Destination Chain** is an `enum` over Across's own destination chain ids, named by their EIP-155 names shortened to 20 characters. Evidence: Across's live route list (`https://app.across.to/api/available-routes`, 1,041 routes on 2026-10-28, destinations 1, 10, 56, 130, 137, 143, 324, 480, 999, 1868, 4217, 4326, 4663, 5042, 8453, 9745, 42161, 43114, 57073, 59144, 728126428), chainid.network names, and `eth_chainId` on the public RPCs of HyperEVM (999 = 0x3e7), Plasma (9745) and Tron (728126428). Solana (34268394551451) and Blast (81457) come from the Across docs "Supported Chains" page. An id outside the enum renders as its decimal value in both registry runners (verified in the runner sources). The spec's `chainId` format was not used: the Rust runner names 16 chains and prints "Chain N" otherwise, the Sourcify runner reads chainid.network, where 999 is "Wanchain Testnet" although Across routes to HyperEVM under 999; the two would disagree on most Across destinations and mislabel one.
5. **Recipient.** In the `address` variants, `addressName` with types eoa/wallet/contract and sources local/ens. In the `bytes32` variants the value is shown raw (full 32 bytes): the contract does not check it (it lives on the destination chain, NatSpec lines 494-496), and for Solana it is a 32-byte key, so a `[12:32]` slice would show a Solana key as a fake EVM address. See SPEC-LIMITS.md.
6. **Output Amount (raw) and Output Token (dest.).** `outputAmount` is in the units of `outputToken` on the destination chain (NatSpec lines 501-506). A wallet resolving `outputToken` on Ethereum could scale by the wrong decimals (USDC: 6 on Ethereum, 18 on BNB Smart Chain), so both are shown raw and labelled as such. `outputToken` uses `raw`, not `addressName`, for the same reason: a name lookup on chain 1 would name a different contract. `chainIdPath` exists in the spec but the registry runners' test metadata is keyed by address only, and a wallet that ignores the parameter would scale wrongly; see SPEC-LIMITS.md.
7. **Depositor** is always shown and named in the sentence. The contract requires it to be an EVM address (line 1385) and gives it two rights: it alone can sign a speed-up that changes the output amount, recipient and message (lines 853-880, 907-934, 1560-1606), and per the protocol's own NatSpec it receives the refund of `inputAmount` when the deposit is not filled by the fill deadline (lines 650-651). If a dapp sets it to another account, that account can redirect the funds.
8. **Fill Deadline / Fill Window.** `fillDeadline` as a timestamp (bounded by line 1405); `fillDeadlineOffset` of the `*Now` variants as a duration added to the block time (lines 767, 827).
9. **Speed-ups.** The call verifies the depositor's signature over (depositId, chain, updatedOutputAmount, updatedRecipient, hash(updatedMessage)) and emits an event (lines 861-880, 915-934). No funds move in this transaction; the relayer may use the update. The screen shows the four signed values; "raw units" says that the new output amount is in destination units.
10. **Intent wording.** "Bridge tokens" (13 characters) rather than the NatSpec "Deposit", which a signer could read as a deposit into a vault. The sentences exceed 30 characters (82 and 96) because they name the amount, the recipient, the destination and the depositor; the linter warns (`Display intent too long`), as it does for about half of the merged descriptors.
11. **Labels** are all 20 characters or fewer; "Output Token (dest.)" is exactly 20.

## Deployments

- Chain 1: `0x5c7BCd6E7De5423a257D81B442095A1a6ced35C5` (proxy, Sourcify exact match `ERC1967Proxy`; implementation `0x456Ac26E5ec083EE9889eBa0d1a0A582502B8e84`, exact match `Ethereum_SpokePool`).
- No other deployment added. Across SpokePools on other chains are different contracts, checked on Sourcify through the proxies' `proxyResolution`:
  - Arbitrum One `0xe35e9842fceaCA96570B734083f4a58e8F7C5f2A` → implementation `0xcfCDA84333431BCC9155f2368B8362F0d1dfF8c9` = `Arbitrum_SpokePool` (exact match): different contract.
  - OP Mainnet `0x6f26Bf09B1C792e3228e5467807a900A503c0281` → `0x60674c53a4cC4ED350659C95fb8020B5AC61cA1D` = `OP_SpokePool`: different contract.
  - Polygon `0x9295ee1d8C5b022Be115A2AD3c30C72E34e7F096` → `0x304BEd95DaeCD3e680073eab385193da711D59d4` = `Polygon_SpokePool`: different contract.
  - Base `0x09aea4b2242abC8bb4BB78D537A67a245A7bEC64` → `0xf23C6C04A2B88e8651FE99bbDccbB5C9D306e6B0`, and Linea `0x7E63A5f1a8F0B4d0934B2f2327DAED3F6bb2ee75` → `0x263c0E973fd0Ca9dE57bb22a91C57Fc367A81915`: implementations not verified on Sourcify, so no source comparison was possible; not added.
  Each would need its own descriptor file (same formats, different contract name and chain-specific behaviour).

## Tests

`registry/across/testsv2/calldata-Ethereum_SpokePool.tests.json`, 9 cases, one or two per described function.

Real transactions (`txHash` in the test case; found with `discover` over Envio HyperSync or on Etherscan, re-read from `https://ethereum-rpc.publicnode.com`):
- `deposit-1`: `0x13466d69dbdf6d86371244186e7688eb1a30bc7d95e6d2ec9a10e30ab88e1c38` — 0.003242593 WETH to Robinhood Chain.
- `deposit-eth`: `0x027d543572be7bdb3f6cbcaff6094384ca6847845f0f3ae03f7fe155d6b6e512` — ETH paid as `msg.value` (Native Value Sent = Amount to Bridge).
- `depositV3-1`: `0x22538a64c926ecffb6507351467a59c885545108c4018233516a337f8b4b32dc` — 177.892664 USDC to Polygon.
- `depositV3-eth`: `0x3ef5ad53efb4dfc87a613e3ad2be36a0ea7c87f233796e6db6d70f850c4239e2` — ETH paid as `msg.value`.
- `depositV3Now`: `0xd1126e52fee1954a441d885cf10101fd6e19fcf2d39d44f93a263f44c418a93c` — 0.0035 ETH to Linea, Fill Window 05:00:00.
- `speedUpV3Deposit`: `0x79c4bc7eefea2f2cbd23f03fd584873c37f313f702723ac67b2ae4a363774b70` — deposit 4037263, empty message.

Encoded (`fixture --function`, realistic sender and values):
- `depositNow`: no call to this selector exists on mainnet (HyperSync searched blocks 0-26291452). Encoded as 250 USDC to Arbitrum One from a real depositor address.
- `unsafeDeposit`: no call on mainnet (same search). Encoded as 0.005 ETH to Base with `msg.value`.
- `speedUpDeposit`: the only two mainnet calls (`0xb5c29df6eabb8462e9847ce8295868fea2cb58f50d488955abb006496f97e4a5`, `0x3f0a6b236b3f5a5fc2e5ced1fb24821d405f241423ee64f8db2836b6cd4989b3`, same deposit) carry a non-empty `updatedMessage`, which the `mustMatch` pin refuses, so neither renders. The encoded case re-uses the arguments and the real depositor signature of the `speedUpV3Deposit` transaction above: both functions hash with `UPDATE_BYTES32_DEPOSIT_DETAILS_HASH` (lines 861-870 vs 915-924), so the signature is valid for the bytes32 variant with the same values.

Why most real deposits were not usable: the Across app appends an integrator tag after the ABI-encoded arguments (delimiter `0x1dc0de`, 3 to 32 extra bytes; 236 of the 245 recent `depositV3` calls in one Etherscan page). The helper refuses such calldata as non-canonical and never trims it, so the fixtures use calls with canonical length (empty `message`). See Flags.

## Checks

- Helper: `clear-signing-helper 0.6.0-preview.6`; the decisions file was filled by a language-model agent, and the helper records every value and reason in its local provenance record.
- `erc7730 lint --require-verified` at the registry's pin (`python-erc7730@964176e28918299dfecb269e20a267a652ada475`): exit 0, **0 errors, 30 warnings** — 28 "Missing display format" (one per excluded function the reference ABI exposes), 1 "Display intent too long", 1 `UV_NATIVE_TLS` environment notice from uv. The linter fetched the ABI (the warnings reference `repo.sourcify.dev/1/0x5c7b…`), so field paths were validated.
- Registry runners at the clone's CI pins: Sourcify runner `9d6d2fe4715d53e002bb966f6593e1fbc44b53c7` (`@ethereum-sourcify/clear-signing@0.3.0`) **9/9 pass**; Rust runner `65af2281aa1366e1d770f9ac445007e56dbe29ca` (`llbartekll/clear-signing@0.1.0`) **9/9 pass**. Logs in `bundle/review/runners/`.
- `--strict-portability`: no findings (`bundle/review/portability.json`); no signed integers, nested arrays or tuple arrays in the described functions.
- `claims` replay: ran against `https://eth.drpc.org` (served state at the fixtures' blocks; `https://mainnet.gateway.tenderly.co` also did, `https://rpc.flashbots.net` refused with 403 `rpc method is not whitelisted`). All 6 real-transaction fixtures checked, 621 runs in total (depositV3-1 129, depositV3-eth 128, deposit-1 117, deposit-eth 117, depositV3Now 53, speedUpV3Deposit 77), **0 findings**. Measured: Amount to Bridge holds exactly in all five deposits (sender paid exactly `inputAmount`), and Native Value Sent holds (0 on the ERC-20 deposits, equal to Amount to Bridge on the three ETH deposits). The hidden and raw arguments were varied with no run that succeeded and made a shown amount false. What claims cannot measure: the recipient, output amount and output token take effect on the destination chain, so no fork of Ethereum can test them; their wording rests on the source reading above. speedUpV3Deposit moves no funds, so it had no amount claim to test. The three encoded fixtures (depositNow, unsafeDeposit, speedUpDeposit) have no txHash and are not replayed by design.
- Not run: device testing on Ledger hardware; the Across team's review.

### Tool limitations (not spec limitations)

- The decisions file cannot express `addressName` on a byte slice of a `bytes32` (`depositor.[12:32]` would be exact, since the contract checks the top bytes are zero) nor an `ifNotIn` rule; hand-editing the descriptor was out of scope, so `depositor` is raw in the bytes32 variants.
- The registry test schema keys token metadata by address only, so a `tokenAmount` with `chainIdPath` cannot be tested per chain; the Rust runner resolves the chain but the test data provider cannot distinguish it.
- The runners disagree on the spec's `chainId` format (16-entry table vs chainid.network), which forced the enum.
- The helper refuses calldata with trailing bytes, which most Across app transactions carry.

### Flags for the integrator

- Trailing integrator tag: most Across app deposits have `0x1dc0de…` bytes after the ABI arguments. Whether a wallet applies the descriptor to such calldata depends on its decoder; if it requires canonical length, those transactions stay blind-signed. The registry runners were not exercised on them.
- Deposits and speed-ups with a non-empty `message` are deliberately refused (`mustMatch`), including Across V5 witness messages and swap-on-destination flows.
- `outputAmount` and `outputToken` are raw destination-chain values; the wallet cannot verify the destination amount.
- `Native Value Sent` renders "0 ETH" on ERC-20 deposits.
- The `destinationChain` enum needs updating when Across adds chains; an unknown id renders as a number.

## Update: embedded calls (`calldata` format)

Paste this section into PR #3173. It supersedes the earlier text on `multicall`, `tryMulticall` and the "nested calldata" exclusions.

**Coverage.** 9 functions are described: the 7 deposit and speed-up functions, plus `multicall(bytes[])` and `tryMulticall(bytes[])`. Each batch element uses the ERC-7730 `calldata` format with callee `@.to` and `amountPath: @.value`. Both functions delegatecall into this contract (MultiCallerUpgradeable.sol lines 38, 68), so `msg.sender` is kept. Neither is payable, so an inner deposit always sees `msg.value = 0` and takes the ERC-20 path (SpokePool.sol line 1440).

26 functions are excluded:
- **Relayer and settlement:** `fillRelay`, `fillV3Relay`, `fillRelayWithUpdatedDeposit`, `requestSlowFill`, `executeSlowRelayLeaf`, `executeRelayerRefundLeaf`, `claimRelayerRefund`, and `fill`. `fill` is relayer-only: it fills a deposit and pays the output tokens from the caller (lines 1197-1218).
- **Gateway and executor only:** `executeAcrossV5` reverts unless the sender is the Gateway (line 1045). `adapterExecuteAcrossV5` reverts unless the sender is the Gateway's current executor (line 1079).
- **Admin:** `relayRootBundle`, `emergencyDeleteRootBundle`, `pauseDeposits`, `pauseFills`, `setCrossDomainAdmin`, `setWithdrawalRecipient`, `setOftMessenger` and `executeExternalCall` are `onlyAdmin`, which is `onlyOwner` on Ethereum (Ethereum_SpokePool.sol line 55). `upgradeTo` and `upgradeToAndCall` are admin-only through `_authorizeUpgrade` (line 325). `renounceOwnership` and `transferOwnership` are Ownable. `initialize` is an initializer.
- **Removed:** `depositDeprecated_5947912356` and `depositFor` always revert.

**Pins.** `message` and `updatedMessage` stay pinned with `mustMatch ["0x"]`, and the pins also apply inside batches. The message is not calldata of a function call. It is the 4th argument of the recipient's `handleV3AcrossMessage` (SpokePool.sol lines 1818-1825). Across's MulticallHandler decodes it as `abi.encode(Instructions{Call[] calls, address fallbackRecipient})` and runs the calls on the destination chain. So the `calldata` format does not apply to it.

**What the screens say (additions).**
- `multicall`: "Run every action below in one transaction; if one action fails, the whole transaction reverts" (MultiCallerUpgradeable.sol lines 41-49).
- `tryMulticall`: "…an action that fails is skipped and the others still run" (lines 63-70). An inner deposit may then not happen, and the intent "Batch, skip failed actions" says so.
- Inside a batch, a deposit shows "Native Value Sent 0 ETH" and the amount in the token. That is true, because `msg.value == 0` makes the deposit pull `inputToken`.

**Tests.** 11 cases: the 9 earlier ones, plus two real empty batches sent by relayers: `multicall` `0x219dd27132aab142346a9fa7178e1997f0381f3611797b47831e7de22fb603c6` and `tryMulticall` `0x1cc3f068548e0e812df856b9afbe582253ed45f1cb1184c3df0fa8d8c94606c8`. HyperSync searched the whole chain. It found 5,794 successful `multicall` and 29 `tryMulticall` transactions, and every one is a relayer fill, a slow-fill request or an empty batch. No real user batch exists. An encoded user batch, a `depositV3` and a `depositV3Now` taken from real transactions, renders correctly in both runners. It cannot be committed because of the runner conflict on nested `interpolatedIntent` (see PR #3175).

**Checks.** Lint at the registry pin: 0 errors, 27 warnings (26 missing formats for excluded functions, 1 intent too long). Sourcify runner `9d6d2fe4` 11/11, Rust runner `65af2281` 11/11. A language-model agent added the `calldata` fields and tests by hand. `claims` was not run again, because neither function moves funds by itself.

## Update: destination chain names and destination amount

Add this to the PR #3173 description. It supersedes the earlier text on `destinationChainId`, `outputAmount` and the destination-chain enum, including items 4 and 6 of "What the screens say" and the related flags and tool limitations.

**Coverage.** No function is added or removed. In the five deposit functions, two fields change:
- **Destination Chain** (`destinationChainId`) uses the ERC-7730 `chainId` format. The wallet names the chain from the EIP-155 chain registry. The `destinationChain` enum is removed.
- **Relayer Must Send** (`outputAmount`, earlier "Output Amount (raw)") uses `tokenAmount`. The token is `outputToken` (`outputToken.[12:32]` in the `bytes32` variants), and `chainIdPath` is `#.destinationChainId`, so the wallet scales the amount with the token's decimals on the destination chain, not on Ethereum.

Output Token (dest.) stays raw. In `speedUpDeposit` and `speedUpV3Deposit`, New Output stays raw: their arguments contain no destination chain id and no output token, because both are fixed in the original deposit, and the signed hash uses the origin chain id (SpokePool.sol lines 861-870).

**What the screens say (changes).**
- **Destination Chain.** The name comes from the EIP-155 registry, for example "Polygon Mainnet", "Arbitrum One", "Robinhood Chain". The contract does not check `destinationChainId`; it only emits it (line 1453). Known gaps of the registry: Across uses 999 for HyperEVM, but the registry lists 999 as "Wanchain Testnet", and Across's Solana id 34268394551451 has no registry entry (see the spec-limitation notes).
- **Relayer Must Send.** The origin chain does not check `outputAmount`: `_depositV3` checks only that `outputToken` is not zero (line 1388), then emits the amount (line 1452). On the destination chain, a fill sends exactly this amount of `outputToken` from the relayer to the recipient (lines 996, 1798, 1808-1813). The relay hash covers every deposit argument (line 1376), so a relayer is refunded only for a fill of exactly this deposit. The amount is not a guarantee to the recipient: the depositor can sign a lower amount with a speed-up (lines 1122-1133), and a slow fill pays an amount set by the root bundle (lines 1236-1238, 1256). When the output token is wrapped native, an EOA recipient gets native token (lines 1803-1809).
- If a wallet does not implement `chainIdPath`, it resolves `outputToken` on Ethereum. None of the five output tokens in the tests has code on Ethereum, so such a wallet shows the raw amount with an "unknown token" warning.

**Tests.** The same 11 cases. The test data now holds the five destination tokens, each read on its own chain: WETH on Robinhood Chain, USDC on Arbitrum One, USDC on Polygon, WETH on Linea, WETH on Base. The expected values are the spec renderings: the destination chain's registry name and the output amount scaled with the destination token's decimals. Logging added to both runners showed that each output token is looked up with the destination chain id.

**Checks.**
- Lint at the registry pin: 0 errors, 27 warnings. `chainIdPath` is written as `#.destinationChainId`. The relative form `destinationChainId` means the same, but the pinned linter does not resolve it for `tokenAmount` and reports false "field does not exist" errors.
- Sourcify runner `9d6d2fe4`: 11/11. Rust runner `65af2281`: 8/11. It fails `deposit-1`, `deposit-eth` and `depositV3-eth`, because it renders chain 4663 as "Chain 4663" instead of "Robinhood Chain": its chain-name table has only 16 entries. This is a runner bug, and the tests keep the spec value. Also found in the Rust runner: when a chain id does not fit in 64 bits, it shows "Chain 0" and resolves the token on the signing chain.
- A language-model agent made these changes by hand. `claims` was not run again: the changed fields take effect on the destination chain, which a fork of Ethereum cannot test.

## Update: chain names, output token, depositor, and app deposits with an integrator tag

Add this to the PR #3173 description. It supersedes the earlier text on Destination Chain, Output Token, the bytes32 Depositor, the interpolated sentence, Tests, Checks and "Tool limitations", including the earlier "Update: destination chain names and destination amount" where they differ.

**Coverage.** No function is added or removed. Changed fields:
- **Destination Chain** is two fields on `destinationChainId`, both labelled "Destination Chain".
  - For the 9 Across destinations that wallet libraries name the same way (1, 10, 56, 137, 324, 8453, 42161, 43114, 59144), the field uses the ERC-7730 `chainId` format: the name comes from the EIP-155 chain registry.
  - For the other 14 Across ids, an `enum` field (`metadata.enums.destinationChainOverride`) shows the name. The labels are the registry names, except 999 = "HyperEVM" (the registry lists 999 as "Wanchain Testnet") and 34268394551451 = "Solana" (not in the registry).
  - The two `ifNotIn` lists split the 23 Across ids, so each Across id shows exactly one name. An id Across does not use shows both: the registry name, if any, and the number.
- **Output Token (dest.)** uses `tokenTicker` with `chainIdPath: #.destinationChainId`, so the wallet looks the ticker up on the destination chain. The bytes32 variants apply it to the full `outputToken` value: an EVM token shows its ticker, and a Solana mint, which no lookup finds, shows its full 32-byte key.
- **Depositor** in the bytes32 variants (`deposit`, `depositNow`, `unsafeDeposit`, `speedUpDeposit`) uses `addressName` on the bytes32 value itself. The contract accepts only an EVM address there: all three bytes32 deposits run `_depositV3`, which starts with `params.depositor.checkAddress()` (SpokePool.sol line 1385), and `speedUpDeposit` calls `depositor.toAddress()` (line 862). Both revert unless the top 12 bytes are zero (AddressConverters.sol).
- **Recipient**, Exclusive Relayer and New Recipient stay raw in the bytes32 variants, because they live on the destination chain, which can be Solana.
- **Relayer Must Send** stays as in the previous update: `tokenAmount` of `outputToken` with `chainIdPath`.

**What the screens say (changes).**
- The deposit sentence is now "Bridge {inputAmount} to {recipient} on the destination chain; depositor {depositor}". ERC-7730 allows a sentence to refer only to always-visible fields, and Destination Chain now depends on the value, so the field carries the chain name.
- "Output Token (dest.)" shows the ticker of the destination-chain token, for example "USDC" on Polygon or "WBTC" on Arbitrum One. When the token is unknown on that chain, the wallet shows its address, or the full 32-byte key for a Solana mint.
- "Depositor" shows the EVM address, or its local or ENS name, in all deposit and speed-up functions.

**Tests.** 16 cases:
- The 11 earlier cases.
- Two encoded cases for destinations that need the override: a `depositV3` to HyperEVM (999) with HyperEVM USDC as output token, and a `depositNow` to Solana with the Solana USDC mint as output token.
- Three real Across app deposits from 2026-10-29 that carry an integrator tag after the ABI arguments, each with its full calldata: `depositV3` `0xc1385ffafa7166f198fc2b904031644ce7419fc74323658d08bef1693aab5089` (WBTC to Arbitrum One), `depositV3` with ETH `0x331be81f20e6d7d8a8289cffe951b3b679e3d29d34034f749e50b17429410e35` (to Robinhood Chain), and `deposit` (bytes32) `0x3f0f21b13273e15e202c640d91256e56ca3e14df7ffa199270fc259316d1e8d2` (USDC to Polygon). In a sample of the last 1,000 calls, 213 of 229 successful `depositV3` calls and all 80 `deposit` calls carry such a tag. Both registry runners decode these and ignore the trailing bytes, as ABI decoding requires.

Destination-chain token metadata was read on each destination chain. A language-model agent made these changes by hand.

**Checks.**
- Lint at the registry pin: 0 errors, 27 warnings (26 missing formats for excluded functions, 1 intent too long). The linter and the schema accept `addressName` and `tokenTicker` on `bytes32`.
- Rust runner `65af2281`: 16/16.
- Sourcify runner `9d6d2fe4`: 9/16. It fails the 7 cases with a bytes32 Depositor or Output Token (`deposit-1`, `deposit-eth`, `depositNow`, `speedUpDeposit`, `unsafeDeposit`, the Solana case and the tagged `deposit`). The library rejects address formats on `bytes32` (`ARGUMENT_TYPE_MISMATCH: "Format addressName expects address but got bytes"`) and shows the raw 32 bytes. This is a tooling to-do; the tests keep the spec value.
- `claims` was not run again: the changed fields take effect on the destination chain, or they do not change what is paid.

**Tool limitations.**
- **Worked around: chain names.** The Rust runner names only 16 chains and prints "Chain N" for the rest, while the Sourcify runner reads the EIP-155 registry. Every Across id where the two differ, plus HyperEVM and Solana, uses the override enum, so both runners show the same names for all 23 Across ids.
- **Worked around: trailing bytes.** The helper refuses calldata with bytes after the ABI arguments. Real tagged deposits were added to the tests by hand, and both runners render them correctly.
- **Removed:** the earlier point that test token metadata is keyed by address only. Tokens on different chains have different addresses, so this limits nothing.
- **Open, Sourcify:** address formats on `bytes32` (see Checks).
- **Open, linter:** the pinned linter does not resolve a relative `chainIdPath` in `tokenAmount`, so the descriptor writes `#.destinationChainId`, which the spec defines as the same path.
- **Open, Rust:** a chain id of 2^64 or more renders as "Chain 0", and the token is then resolved on the signing chain. The contract does not check `destinationChainId`, so a dapp could encode such a value.

**Flags for the integrator.**
- The `destinationChainOverride` enum and the `ifNotIn` lists need updating when Across adds a destination. Until then, a new id shows both fields: the registry name, if any, and the number.
- Most Across app deposits carry the integrator tag. The descriptor renders them in both registry runners.


## Update: review round 1

Add this to the PR #3173 description as well. Commit `d684482` answers the first maintainer review. Source lines refer to the verified implementation `0x456Ac26E5ec083EE9889eBa0d1a0A582502B8e84`, `contracts/spoke-pools/SpokePool.sol`.

- **Depositor label.** The five deposit formats label the field "Depositor (gets refund, can change recipient and amount)". `speedUpDeposit` (lines 853-870) and `speedUpV3Deposit` (907-924) let the depositor set a new output amount, recipient and message; `_verifyUpdateV3DepositMessage` (1560-1584) hashes them and `_verifyDepositorSignature` (1593-1606) requires a valid signature from `depositor`. The relayer applies the update through `fillRelayWithUpdatedDeposit` (1110-1135). The NatSpec names the depositor as "the account credited with the deposit who can request to speed up this deposit by modifying the output amount, recipient, and message" (492-493) and says the depositor receives `inputAmount` of `inputToken` back on the origin chain after the fill deadline (650-651); the refund is paid by `executeRelayerRefundLeaf` (1276) and `_distributeRelayerRefunds` (1467-1500) from a root bundle the HubPool verifies. The speed-up formats keep "Depositor". The label is longer than the 20 characters the linter wants for Ledger devices; it adds one warning.
- **Deposit sentence.** "Bridge {inputAmount} to {recipient}, who gets {outputAmount}; depositor {depositor}". The output amount is what the relayer sends to the recipient (NatSpec 483-484, 508). The referenced fields have no `visible` rule, as the spec requires (erc-7730.md line 313). The depositor stays in the sentence because a wallet may show only the sentence (spec line 937). The destination chain is still not in the sentence (two complementary fields show it). For a Solana destination the amount is raw in the sentence, as in the field; for the `bytes32` formats the recipient is the raw 32 bytes.
- **`unsafeDeposit`.** `depositNonce` is shown ("Deposit Nonce", `raw`, after Fill Deadline). The intent is "Bridge tokens with a chosen deposit nonce" and the sentence ends with "; deposit nonce {depositNonce}". The deposit id is `uint256(keccak256(abi.encodePacked(msg.sender, depositor, depositNonce)))` (`getUnsafeDepositId`, 1363-1369, called at 695), and a reused nonce lets a speed-up signature be reused (650-653, 834-837), so the signer must see the nonce.
- **Tests.** 18 cases (16 before). Two encoded batches, built with `cast calldata` from the calldata of real deposits already in the file, `value` 0, no `txHash`:
  - `multicall, two deposits (encoded) - chain 1`: `depositV3` from `0x22538a64c926ecffb6507351467a59c885545108c4018233516a337f8b4b32dc` (177.892664 USDC to Polygon) and `deposit` from `0x3f0f21b13273e15e202c640d91256e56ca3e14df7ffa199270fc259316d1e8d2` (5527.457409 USDC to Polygon, integrator tag kept). Both runners decode the tagged inner call.
  - `tryMulticall, one deposit (encoded) - chain 1`: `depositV3Now` from `0xd1126e52fee1954a441d885cf10101fd6e19fcf2d39d44f93a263f44c418a93c` (0.0035 WETH to Linea). The batch sends no ETH, so the screen shows "Native Value Sent 0 ETH"; inside a batch the inner deposit pulls WETH as an ERC-20 (lines 1440-1441), which is what the screen says.
  - Why encoded: HyperSync over the whole chain to block 26,304,381 returns 7,883 successful `multicall`/`tryMulticall` transactions to the SpokePool; every batch is made of fills, slow-fill requests, or is empty. No real batch carries a deposit. The two real empty batches stay. The nested expected screens carry `interpolatedIntent` and `owner`; both runners at the current pins accept this.
- **Checks** (registry pins of master at #3182): lint 0 errors, 28 warnings (26 missing formats for excluded functions, 1 intent too long, 1 label too long). Schema ok. Sourcify runner 18/18, Rust runner 18/18. Index buildable.

## Update: review round 2

Add this to the PR #3173 description as well. Commit `d890b5e` answers the second maintainer review (two changes, no suggestions). The branch also includes upstream master as of `029f1a3`.

- **Deposit sentence.** "Bridge {inputAmount} to {recipient} on the destination chain; the relayer must send {outputAmount}; depositor {depositor}" (plus "; deposit nonce {depositNonce}" in `unsafeDeposit`). The old "who gets {outputAmount}" was wrong when the output token is the destination chain's wrapped native token: a fill calls `_transferTokensToRecipient` (SpokePool.sol lines 1791-1810), which for `outputToken == wrappedNativeToken` calls `_unwrapwrappedNativeTokenTo` (lines 1630-1637); that function sends native currency to a recipient that is not a contract or is an EIP-7702 delegated wallet, and the wrapped token only to a contract. The new wording matches the field label "Relayer Must Send" and is true for both cases. 12 deposit expectations and the 3 nested deposits of the batch cases are updated.
- **Speed-up formats.** The intent is "Request bridge deposit update" and the sentence "Request update of deposit {depositId} of {depositor}: {updatedOutputAmount} raw units to {updatedRecipient}". `speedUpDeposit` and `speedUpV3Deposit` verify the depositor's signature and emit `RequestedSpeedUpDeposit` (lines 853-879 and 907-933); the NatSpec says the relayer "has the option but not the obligation to use this updated information" (line 839). The two speed-up expectations are updated.
- **Checks** (registry pins of master at #3182): lint 0 errors, 29 warnings; schema ok; Sourcify runner 18/18, Rust runner 18/18; index buildable.
