# Review round 1: replies and description changes

Reviewer: marcocastignoli. For each open PR: the pushed commit, one reply per thread (to post on that thread, then resolve it when it says "Done"), and the description change. All replies are plain text; post them as they are.

Agent instruction for the local agent with GitHub rights, repository `ethereum/clear-signing-erc7730-registry`:

```text
Task: on pull requests #3172, #3173, #3174 and #3176 of ethereum/clear-signing-erc7730-registry, post the replies below on the matching review threads, resolve every thread whose reply starts with "Done", append the "Update: review round 1" section of each report to the PR description, and re-request a review from marcocastignoli. Do not change code.

Source: docs/top-contracts/REVIEW-ROUND-1.md (this file) and the reports in docs/top-contracts/ on the fork manuelwedler/clear-signing-erc7730-registry, branch claude/nifty-euler-gwsa66, at the commit named in the fix list item 18 of PR-BODY-FIXES.md. Link files on the fork only with commit permalinks. No Claude session links and no model names.
```

## #3174 Base, commit `a5cd30b`

| Thread | Kind | Reply |
|---|---|---|
| `calldata-L2ToL1MessagePasser.json`, `initiateWithdrawal` intent | required | Done in a5cd30b. The intent is now "Start ETH withdrawal to Ethereum" and the sentence "Start withdrawal of {@.value} to {_target} on Ethereum". The three `initiateWithdrawal` cases and the new nested renderings use the new texts. |
| `calldata-OptimismPortal2.json`, deposit Note | required | Done in a5cd30b, with your wording: "From a contract wallet, the deposit runs from its aliased address on Base. The L2 Call and the ETH not sent to the L2 Recipient use that address." It matches OptimismPortal2.sol lines 589-592, where a non-EOA sender becomes the aliased `from` of the L2 transaction. `spenderPath "@.from"` stays, because an EOA is not aliased. Both deposit cases and the new deposit case show the new Note. |
| `calldata-OptimismPortal2.json`, prove label | suggestion | Done in a5cd30b. The prove format's data field is now "L1 Call at Finalization"; the finalize formats keep "L1 Call". The four prove cases are updated. The pinned linter now warns that the label is longer than 20 characters; it is a warning, not an error, and we kept your label. |
| nested cross-chain tests | suggestion | Added in a5cd30b, one per format. Portal: an encoded deposit whose `_to` is the L2ToL1MessagePasser and whose data is `initiateWithdrawal`; it renders the Base descriptor nested (and the nested `L1 Call` back on chain 1 as `0x`). Messenger: an encoded `sendMessage` to the L2ToL1MessagePasser with `burn()`. Message passer: a real Base transaction, `0xc5548f01be0a52408333c406bb1ea654ef30a16e3c669231c8d94b9a1966fd91`, the only direct `initiateWithdrawal` in Base history whose target is the L1CrossDomainMessenger; its L1 call is `sendMessage`, so the screen shows chain 8453 → 1 → 8453. Both runners render all three identically, so we found no runner gap. No real mainnet deposit or `sendMessage` targets the message passer, so those two cases are encoded. |
| `calldata-L1CrossDomainMessenger.json`, Sourcify | suggestion | Done. The messenger implementation `0xb686F13AfF1e427a1f993F29ab0F2E7383729FE0` is now verified on Sourcify (matchId 57654163, creation and runtime match, from Etherscan's standard JSON input, solc 0.8.15). The bridge implementation `0x61525EaaCDdB97D9184aFc205827E6A4fd0Bf62A` was already verified (matchId 43602318). The two proxies remain unresolved by Sourcify's proxy detection; a verification cannot change that. |

Description: append "Update: review round 1" of `base-OptimismPortal2.md`. The test count is 33.

## #3172 Blast, commit `086ed51`

| Thread | Kind | Reply |
|---|---|---|
| `calldata-L2ToL1MessagePasser.json`, `initiateWithdrawal` intent | required | Done in 086ed51. The intent is "Start ETH withdrawal to Ethereum" and the sentence is "Start withdrawal of {@.value} to {_target} on Ethereum; the L1 payout can be lower". The three message passer cases and the nested rendering in the portal case `depositTransaction-nested-call` are updated. We kept the short payout clause, because finalization is permissionless and need not be done by the signer; tell us if you prefer your wording. |
| `calldata-OptimismPortal.json`, deposit Note | required | Done in 086ed51. The Note now reads: "From a contract wallet, the deposit runs from its aliased address on Blast. The L2 Call and the ETH not sent to the L2 Recipient use that address." The `L2 Call` field keeps `spenderPath "@.from"`: the portal aliases only when `msg.sender != tx.origin` (OptimismPortal.sol lines 438-442), so EOAs and EIP-7702 EOAs are shown correctly. The three deposit cases are updated. |
| `calldata-L1BlastBridge.json`, `_remoteToken` label | suggestion | Done in 086ed51. The spec's `tokenTicker` has only `chainId`/`chainIdPath`; it has no `nativeCurrencyAddress` like `tokenAmount`, so the label now says "Token on Blast (zero address = ETH)". The proxy now runs implementation `0xeDEC6e12b067DaDdBa9Fb555BB02b208116Fa392` with `DEPOSIT_CUTOFF_BLOCK = 26298276`; `bridgeERC20` and `bridgeETH` revert with "L1BlastBridge: deposits are disabled". The finalize functions are unaffected. |
| `calldata-L1BlastBridge.json`, bridge sentences | suggestion | Done in 086ed51: "Bridge {_amount} as {_remoteToken} to your address on Blast" and "Bridge {_amount} as {_remoteToken} to {_to} on Blast". Both registry runners interpolate the `tokenTicker` field as the ticker ("Bridge 100 USDT as USDB to your address on Blast"). For stETH, where `_remoteToken` must be the zero address (L1BlastBridge.sol line 273), both runners print the raw zero address in the sentence; the field right below it says "zero address = ETH", and a wallet that treats the failed lookup as an interpolation failure falls back to the intent "Bridge token to Blast", as the spec requires. That path reverts since block 26298276 anyway. |
| `calldata-L1StandardBridge.json`, sentences | suggestion | Done in 086ed51. `bridgeERC20`/`bridgeERC20To` say "as {_remoteToken}" and `depositERC20`/`depositERC20To` say "as {_l2Token}". The four test expectations now read, for example, "Bridge 11730445 BLAST as BLAST to your address on Blast". No other blast tests file nests these deposit sentences. |
| `testsv2/calldata-L2ToL1MessagePasser.tests.json`, DAI | suggestion | Done in 086ed51. DAI (`0x6B17...1d0F`, 18 decimals) is in the file's `dataProvider`, and the nested claim renders "795000 DAI" in the field and in the sentence. |
| `calldata-AirdropVesting.json` / `calldata-Airdrop.json`, recipient types | suggestion | Done in 086ed51. Both fields now have `types: ["eoa", "wallet", "contract"]`. The contracts accept any non-zero address (Airdrop.sol lines 175-177, AirdropVesting.sol lines 128-130). We kept `wallet` because the spec lets the wallet treat it as an account it controls, which is the common case, and added `contract` so a Safe recipient passes the type check. |

Description: append "Update: review round 1" of `blast-OptimismPortal.md`. The test count stays 46. The spec-limitation note has a new section ("A sentinel address that means the native currency cannot be shown as a ticker").

## #3173 Across, commit `d684482`

| Thread | Kind | Reply |
|---|---|---|
| `depositor` label | required | Done in d684482: the five deposit formats now label the field "Depositor (gets refund, can change recipient and amount)"; the speed-up formats keep "Depositor". The source backs the claim: `speedUpDeposit` (lines 853-870) and `speedUpV3Deposit` (907-924) accept a new output amount, recipient and message when `_verifyUpdateV3DepositMessage` (1560-1584) finds a valid signature from `depositor` (`_verifyDepositorSignature`, 1593-1606), and the NatSpec says the depositor is "the account credited with the deposit who can request to speed up this deposit" (492-493) and gets `inputAmount` of `inputToken` back after the fill deadline (650-651). The label exceeds the 20-character Ledger limit, so the pinned linter adds one "label too long" warning; the registry already has about 30 labels of this length. Say if you prefer a shorter form such as "Depositor (refund, edits)". |
| deposit sentence | suggestion | Done in d684482: "Bridge {inputAmount} to {recipient}, who gets {outputAmount}; depositor {depositor}" in all five deposit formats. `inputAmount`, `recipient` and `outputAmount` have no `visible` rule, so the sentence respects the spec rule on interpolation. We kept the depositor clause, which was already there, because a wallet may show only the sentence and the depositor controls the refund and the speed-up. For a Solana destination the output amount stays raw in the sentence, as in the field, and for the `bytes32` formats the recipient stays the raw 32 bytes. |
| `unsafeDeposit`, `depositNonce` | suggestion | Done in d684482: "Deposit Nonce" is a raw field after Fill Deadline, the intent is "Bridge tokens with a chosen deposit nonce", and the sentence ends with "; deposit nonce {depositNonce}". The id is `uint256(keccak256(abi.encodePacked(msg.sender, depositor, depositNonce)))` (`getUnsafeDepositId`, lines 1363-1369, called at line 695), so the signer now sees the one input they choose. The NatSpec warns that a reused nonce lets a speed-up signature be reused (650-653, 834-837). The test now expects "Deposit Nonce" = 7. |
| `multicall` / `tryMulticall` tests | suggestion | Added in d684482: "multicall, two deposits (encoded)" (a real `depositV3` to Polygon and a real `deposit` to Polygon with its integrator tag) and "tryMulticall, one deposit (encoded)" (a real `depositV3Now` to Linea), built from the calldata of the existing real cases, value 0. Both runners render the nested deposit screens, including the nested sentence. They are encoded because HyperSync over the whole chain (to block 26,304,381) finds 7,883 successful `multicall`/`tryMulticall` transactions on the SpokePool and none carries a deposit: every batch is a fill, a slow-fill request, or empty. The two real empty batches stay as well. |

Description: append "Update: review round 1" of `across-Ethereum_SpokePool.md`. The test count is 18.

## #3176 Pendle, commits `75a427d` and `a0b7be5`

| Thread | Kind | Reply |
|---|---|---|
| `calldata-PendleRouterV4.json`, `redeemDueInterestAndRewards` lists | suggestion | Done in 75a427d. `sys.[]`, `yts.[]` and `markets.[]` now render as token tickers, labelled "SY Rewards", "YT Claims" and "LP Rewards". The router calls `claimRewards(user)` on each SY (ActionMiscV3.sol:79-81), `redeemDueInterestAndRewards(user, true, true)` on each YT (:83-85) and `redeemRewards(user)` on each market (:87-89), so each list is exactly the set of positions claimed for the shown beneficiary. We used "YT Claims" instead of "YT Interest and Rewards" because the linter flags labels over 20 characters as truncated on Ledger devices, and the V2 format already uses that label. The three affected test expectations are updated. |
| `testsv2/calldata-PendleRouterV4.tests.json`, native currency tests | suggestion | Done in a0b7be5. Added a real `swapExactTokenForPt` with `input.tokenIn = 0x0`, `netTokenIn = 0.5 ETH` and `msg.value = 0.5 ETH` (`0xd8db82419abb1cb7652ae56a82c97867c4ad4d092f47a9e9e889e7513ed5ed92`, block 26291981; `limit.limitRouter` is `0x0`, so it passes the only pin on that format), rendering "Amount to Pay 0.5 ETH" and "Native Value Sent 0.5 ETH". The multicall case wraps that same calldata with the same value and is encoded: a HyperSync scan of all 211,000 router multicalls since deployment found none with a non-zero value. Both runners render the nested action with its own "Native Value Sent 0.5 ETH", as the delegatecall keeps the outer `msg.value` (ActionMiscV3.sol:413-420). |

Description: append "Update: review round 1" of `pendle-PendleRouterV4.md`. The test count is 48.

## Round 2: #3173 Across, commit `d890b5e`

#3172, #3174 and #3176 were approved and merged on 2026-10-30. #3173 got a second review with two changes; both are done.

| Thread | Kind | Reply |
|---|---|---|
| deposit `interpolatedIntent`, "gets" | required | Done in d890b5e. The sentence now reads "Bridge {inputAmount} to {recipient} on the destination chain; the relayer must send {outputAmount}; depositor {depositor}" (with "; deposit nonce {depositNonce}" in `unsafeDeposit`). We used "the relayer must send" to match the field label "Relayer Must Send"; it is true whether the recipient receives the wrapped token or native currency through `_unwrapwrappedNativeTokenTo` (lines 1630-1637). The 12 deposit expectations and the 3 nested deposits in the batch cases are updated. |
| speed-up formats, "Update bridge deposit" | required | Done in d890b5e, with your wording: intent "Request bridge deposit update" and sentence "Request update of deposit {depositId} of {depositor}: {updatedOutputAmount} raw units to {updatedRecipient}". Both functions only emit `RequestedSpeedUpDeposit` (lines 874 and 928), and the relayer may ignore it (line 839). The two speed-up expectations are updated. |

Description: append "Update: review round 2" of `across-Ethereum_SpokePool.md`. The head is now `043f71b` (a cleanup commit removed unused `metadata.constants`; no screen changed).

## Leftover on merged #3174 Base

A non-blocking suggestion came with the approval: the encoded case `sendMessage-l2-call-to-message-passer` in `registry/base/testsv2/calldata-L1CrossDomainMessenger.tests.json` shows a call that cannot run, because the Base L2 messenger refuses the L2ToL1MessagePasser as a target. The PR is merged, so this is a small follow-up PR: replace the case with a `sendMessage` to an L2 target the messenger accepts and that has a descriptor on chain 8453, or add a note to the case description.

