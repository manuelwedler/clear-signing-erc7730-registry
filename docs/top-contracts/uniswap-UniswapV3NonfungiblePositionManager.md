# uniswap: add Uniswap V3 NonfungiblePositionManager calldata descriptor (mainnet)

> **Draft.** This descriptor was written for the registry's top-contracts effort. It was **not** submitted by the Uniswap Labs team, and Uniswap Labs has not reviewed it. Open the pull request from an account tied to the owner, or label it as a third-party draft.

The descriptor is `registry/uniswap/calldata-UniswapV3NonfungiblePositionManager.json`. Its tests are in `registry/uniswap/testsv2/calldata-UniswapV3NonfungiblePositionManager.tests.json`.

## Summary

The Uniswap V3 NonfungiblePositionManager wraps V3 liquidity positions as ERC-721 tokens (`UNI-V3-POS`). This descriptor clear-signs the position lifecycle sent as a direct call: `mint`, `increaseLiquidity`, `decreaseLiquidity`, `collect` and `burn`. It also covers the ERC-721 transfer and approval functions, the ERC-721 `permit`, the pool initializer, and the payment helpers (`refundETH`, `sweepToken`, `unwrapWETH9`, `selfPermit*`).

- `multicall` stays blind. It carries about half the traffic, including all Uniswap app calls.
- Only Ethereum mainnet is bound. **Other chains were out of scope for this draft.**

The verified source is Sourcify `match` (runtime and creation) for `contracts/NonfungiblePositionManager.sol:NonfungiblePositionManager`, solc `0.7.6+commit.7338295f`. The contract was deployed in transaction `0xc5eabeff36dc4593e58ede208838105815106e5a11aa725638d72b43f88e5fb2` at block 12369651. It is not a proxy.

Before authoring, `clear-signing init --registry` ran against the registry clone. It returned `registryMatches: []`, so no registry descriptor shares this contract's functions.

## Coverage

### Described (19)

| Function | Intent | Notes |
|---|---|---|
| `mint` | Open liquidity position | Amounts in `params.token0` / `params.token1` with tickers. Shows the pool fee, the position recipient and the deadline. |
| `increaseLiquidity` | Add to liquidity position | Amounts are raw; see the spec-limitation notes. |
| `decreaseLiquidity` | Decrease liquidity | Says that nothing is transferred until `collect`. |
| `collect` | Collect from position | Maximums are raw and labelled "Max". |
| `burn` | Burn empty position NFT | |
| `approve` | Approve position operator | |
| `setApprovalForAll` | Set operator for all NFTs | `approved` shown as Grant / Revoke. |
| `transferFrom`, `safeTransferFrom` (both overloads) | Transfer position NFT | |
| `permit` (ERC-721) | Approve operator by permit | |
| `createAndInitializePoolIfNecessary` | Create pool if needed | |
| `refundETH` | Refund leftover ETH | |
| `sweepToken` | Sweep leftover tokens | |
| `unwrapWETH9` | Unwrap WETH to ETH | |
| `selfPermit` | Approve token by permit | |
| `selfPermitIfNecessary` | Approve by permit if needed | |
| `selfPermitAllowed` | Approve unlimited by permit | |
| `selfPermitAllowedIfNecessary` | Unlimited permit if needed | |

### Excluded (2)

- `multicall(bytes[])`: each element is a `delegatecall` into this contract (base/Multicall.sol lines 11-27). A static descriptor cannot decode that nested calldata. The helper also rejects the ERC-7730 `calldata` format, which is a tool limitation, not a spec limitation. This is the largest gap: the Uniswap app sends `multicall`.
- `uniswapV3MintCallback`: this is the pool's callback. `CallbackValidation.verifyCallback` reverts unless `msg.sender` is the pool for that key (base/LiquidityManagement.sol line 31), so no user signs it.

### Hidden fields (30, each `visible: "never"`)

| Function | Field(s) | Reason |
|---|---|---|
| `mint` | `token0`, `token1` | Each one is shown as the ticker of its amounts. |
| `mint` | `tickLower`, `tickUpper` | Strict portability rejected them; see "What the screens say". |
| `permit` | `v`, `r`, `s` | Signature; it proves the owner's consent and changes nothing the signer checks. |
| `permit` | `deadline` | Expiry of the signature; it limits when the permit can be used, not what it grants. |
| `selfPermit`, `selfPermitIfNecessary` | `token` | Shown as the ticker of the approved amount. |
| `selfPermit`, `selfPermitIfNecessary` | `deadline`, `v`, `r`, `s` | Same reasons as `permit`. |
| `selfPermitAllowed`, `selfPermitAllowedIfNecessary` | `nonce` | Permit nonce, which the signer does not choose. |
| `selfPermitAllowed`, `selfPermitAllowedIfNecessary` | `expiry`, `v`, `r`, `s` | Same reasons as `permit`. |
| `safeTransferFrom(…,bytes)` | `_data` | Opaque bytes forwarded to the recipient's `onERC721Received` hook; this contract does not read them. |
| `sweepToken` | `token` | Shown as the ticker of the minimum. |

### Pinned arguments (`mustMatch`)

`@.value` is pinned to `[0]` on 15 payable functions:

- `mint`, `increaseLiquidity`, `decreaseLiquidity`, `collect`, `burn`
- `permit`, `createAndInitializePoolIfNecessary`
- `refundETH`, `sweepToken`, `unwrapWETH9`
- all four `selfPermit*`

ETH sent with any of these calls is not used, or only partly used, and stays in the contract. Any caller can then take it with `refundETH` (base/PeripheryPayments.sol lines 44-46). In `mint` and `increaseLiquidity`, `pay` wraps only the ETH needed (lines 58-61). The rest stays in the contract, and all of it stays when neither pool token is WETH9.

So a direct `mint` that pays in ETH is **not clear-signed**. It falls back to blind signing, and so does every Uniswap app flow, which uses `multicall(mint, refundETH)`. All 15 real fixtures have `value = 0`. On `refundETH` the pin keeps the screen simple: the call returns any `msg.value` anyway.

## What the screens say

All line numbers refer to the verified source on Sourcify, under `contracts/` and `base/`.

- **Desired amounts are maximums.** `mint` / `increaseLiquidity` compute liquidity from `amount0Desired`/`amount1Desired` (LiquidityManagement.sol lines 71-77), and the pool takes only what that liquidity needs. They are labelled "Maximum to Add" or "Max Token0 (raw)", with "up to" in the sentence.
- **Minimums are enforced in the same call.** `amount0Min`/`amount1Min` are checked by `require(amount0 >= params.amount0Min && amount1 >= params.amount1Min)` (LiquidityManagement.sol line 88). They are labelled "Minimum to Add" or "Min Token0 (raw)". No argument switches the check off.
- **`mint` recipient.** The NFT goes to `params.recipient` (NonfungiblePositionManager.sol line 156). It is shown as "Position Recipient" and named in the sentence.
- **`mint` ticks hidden.** This is a portability judgment call. `--strict-portability` rejected the shown `int24` ticks: the registry's pinned runners misrender negative signed integers, and every real mint has negative ticks. A raw tick is also unreadable as a price. The maximums, minimums and recipient bound the call for any tick (LiquidityManagement.sol line 88), so the screen stays true, but **the signer does not see the price range**. This was preferred to excluding `mint`, the most-called direct function (1047 transactions a week). See the spec-limitation notes, "Price ranges given as ticks".
- **`decreaseLiquidity` sends no tokens.** It burns liquidity in the pool and only credits `tokensOwed0/1` (NonfungiblePositionManager.sol lines 273-298). The sentence ends "become owed to the position; nothing is transferred until collect". The minimums are labelled "Min Token0 Due (raw)" and enforced at line 275.
- **`collect` maximums.** The amounts are clamped to what is owed (lines 354-358). They are labelled "Max Token0 (raw)" with "up to" in the sentence. The usual `type(uint128).max` renders as `340282366920938463463374607431768211455`, which is true but unlabelled; see the spec-limitation notes. The recipient is shown. `recipient = address(0)` sends the tokens to the contract itself (line 318), where it shows as a zero address.
- **Raw amounts.** `increaseLiquidity`, `decreaseLiquidity` and `collect` show raw amounts because their tokens live in storage (`_poolIdToPoolKey`). The labels and sentences say "(raw units)".
- **`increaseLiquidity` can fund someone else's position.** It has no `isAuthorizedForToken` check (lines 198-202). The sentence says "to position <id>", not "your position".
- **`burn`.** The "empty" in the intent is backed by `require(liquidity == 0 && tokensOwed0 == 0 && tokensOwed1 == 0)` (line 379).
- **Operator grants.** A single-token operator (`approve`, `permit`) or an all-tokens operator (`setApprovalForAll`) passes `_isApprovedOrOwner` (line 185). That lets it call `decreaseLiquidity`, and `collect` to any recipient, and transfer the NFT. Hence the wording "withdraw and transfer". Grant and revoke come from `approved` (OpenZeppelin ERC721.sol line 211).
- **ERC-721 `permit`.** The owner's signature sets the operator (ERC721Permit.sol lines 55-85). The intent and sentence say that it grants operator rights.
- **Payment helpers.**
  - `sweepToken` and `unwrapWETH9` send the **whole** balance after `require(balance >= amountMinimum)` (PeripheryPayments.sol lines 19-41). The wording is "the whole token balance … at least {amountMinimum}", with the minimum labelled "Minimum to Sweep" or "Minimum to Unwrap".
  - `refundETH` pays `msg.sender` (line 45), so its sentence says "to you".
  - The registry's `calldata-UniswapV3Router02.json` has no `refundETH`, `sweepToken`, `unwrapWETH9` or `selfPermit*` formats, so there was no wording to reuse. Its `"Unlimited"` threshold idiom (`0x8000…0000`) is kept.
- **`selfPermit*` grants.**
  - `selfPermit` approves `value` to this contract (SelfPermit.sol line 24). `value` is shown with "Unlimited" at or above `2^255`.
  - `selfPermitAllowed` uses the DAI-style `allowed = true`, which is unlimited (line 48), so the intent says "unlimited" and the token is shown.
  - The `IfNecessary` variants skip the permit when the allowance is already high enough (lines 36 and 60), and their sentences say so.
- **`createAndInitializePoolIfNecessary`.** It creates and initializes the pool only when needed (PoolInitializer.sol lines 13-31). No funds move. `sqrtPriceX96` is raw and labelled "(Q64.96)".

## Deployments

| Chain | Address | Evidence |
|---|---|---|
| 1 (Ethereum) | `0xC36442b4a4522E871399CD717aBDD847Ab11FE88` | Sourcify full match (runtime and creation). `name()` returns "Uniswap V3 Positions NFT-V1". Not a proxy. |

Other chains were out of scope. No other deployment was added.

## Tests

19 cases, all on chain 1, one or more per described function.

**Real transactions (15).** Each was found by `discover` through Envio HyperSync, then re-read and checked over RPC.

| Function | txHash |
|---|---|
| approve | `0xeb4a55bb85271ccc01d9d6260b3d701999e77dd652c4af0466ce329ed5c3905d` |
| burn | `0xeeff4052a7da30ee377bd64a965036fea1365099cf0e50b135f59d0a83b93b48` |
| collect | `0x1b4e6f9e88abba60521ce0081cff06e260e73f572cfb48cea93bfcec6d5eb7e9` |
| createAndInitializePoolIfNecessary | `0x2b2592ce77fa55ad62c5ccb6b1260b8898e582ce4706ce5c05c16296a28ed226` |
| decreaseLiquidity | `0xf8710d5c3e4c26a33c8683b8cd448eab1566badef5df7cf3284dc4a0eeeada4a` |
| increaseLiquidity | `0x257e4313cb65a57f4a6c6767bc143710d60f2425eb6fe3fca52f1ac7e916c302` |
| mint | `0x2abd4dd0ebddfb1cfaac79f42b8bbc2c5a81c7f9ca0a49e8209b615d8f32bb62` |
| permit | `0x0034686f3364d2a7911ce62afd2d98628da23d26ea2a3927032a145881832327` |
| refundETH | `0x039b4a6a21b6f6f0b5c95db5c11da668a918222278ef7309f17c35f526f45f37` |
| safeTransferFrom (with bytes) | `0x3aeef76e2c16e752437f8c1beef343d80f6be2468d1b983c1c095006b0e0d88b` |
| safeTransferFrom (no bytes) | `0xd360fdae84e18cd7e5a1db6b95bb1c728eb195a9b965c16d795d491449e5fb84` |
| setApprovalForAll | `0x9fff453ef872b3a81a18c2c418da6963dff6d848eaae6d815ab7c9a9f5345a27` |
| sweepToken | `0xe14232e5239016c43a40173da6cedf961bd219a703e6f072478216c01c786613` |
| transferFrom | `0xd0111ae0b415a6557c791cb40d3282d8fa38da48c0f4a47ed2fbda44d3642c78` |
| unwrapWETH9 | `0x75e23178ec59ce70d810154ac6247070c2c15f5267bff3c08cc6281e30263eea` |

**Encoded (4):** `selfPermit`, `selfPermitIfNecessary`, `selfPermitAllowed`, `selfPermitAllowedIfNecessary`.

- **Why encoded:** HyperSync searched the whole chain (blocks 0-26291420) and found no successful direct call to any of them. They are only ever used inside `multicall`.
- **How they were built:** the sender is the real `mint` sender `0xF949618879cB256Cc6EBBf9D455B118C79ff0298`. The signatures are placeholders, so these transactions would revert on chain; they test rendering only.
- **What they cover:**
  - `selfPermit` with 1000 USDC.
  - `selfPermitIfNecessary` with `type(uint256).max` USDC, to show "Unlimited USDC".
  - The two `Allowed` variants with DAI.

Token metadata was read from chain by `fixture --rpc-url`: DOS, USDT, USDC, WETH. The tests add `nftCollectionNames` for the position manager. The address names for WETH, Ephemeral and DAI come from their on-chain `name()`.

## Checks

- **Helper:** clear-signing-helper `0.6.0-preview.6`.
- **Lint:** `erc7730 lint`, at the version pinned in the registry's `.github/requirements.txt`. Exit 0, **0 errors**, **4 warnings**:
  - Display intent too long, for the `interpolatedIntent` sentences. They name every shown amount and recipient; the 30-character intents themselves are within the limit.
  - Missing display format for `multicall`. Excluded on purpose.
  - Missing display format for `uniswapV3MintCallback`. Excluded on purpose.

  The linter fetched the reference ABI from Sourcify, so the field paths were checked.
- **Registry runners** (pins read from the registry CI): Sourcify `@ethereum-sourcify/clear-signing@0.3.0` passed **19 of 19**; Rust `llbartekll/clear-signing@0.1.0` passed **19 of 19**.
- **Strict portability:** `export --strict-portability` succeeded once the `mint` ticks were hidden. The portability record still lists `SIGNED_INTEGER_PORTABILITY` for the hidden `tickLower`/`tickUpper`, because a wallet must still decode the `int24` values in the tuple even though it does not display them.
- **Claims:** all 15 real-transaction fixtures were replayed on anvil forks.
  - **Where:** the first 6 on `https://eth.drpc.org` (approve, burn, collect, createAndInitializePoolIfNecessary, decreaseLiquidity, increaseLiquidity). drpc then failed on `mint` with HTTP 408 ("Request timeout on the free plan"), so the remaining 9 ran one at a time on `https://mainnet.gateway.tenderly.co`.
  - **Result: 1013 runs, 0 findings.** Per fixture: increaseLiquidity 300 (it hit the run budget), mint 230, createAndInitializePoolIfNecessary 227, decreaseLiquidity 162, permit 46, collect 39, and 1 run each for the other nine.
  - **Limits:**
    - The single-run fixtures (the ERC-721 transfers and approvals, `refundETH`, `sweepToken`, `unwrapWETH9`) had no arguments the tool varied. Their wording rests on the source lines cited above.
    - The encoded `selfPermit*` fixtures have no txHash and were not replayed.
    - The claims ran before the last two changes: the `@.value` pin on `mint`/`increaseLiquidity`, and hiding the `mint` ticks. Both changes only restrict or hide. The ticks were shown raw during the replay, so claims had already varied them, and all real transactions had `value = 0`.
- **Authorship:** a language-model agent made every decision; no human decided any value yet.
- **Did not run or could not be verified:**
  - No physical-device test.
  - No other-chain deployments (out of scope).

## Update: embedded calls (`calldata` format)

Paste this section into PR #3175. It supersedes the earlier text on `multicall`.

**Coverage.** `multicall(bytes[])` is now described: 20 functions described, 1 excluded (`uniswapV3MintCallback`, the pool callback). Each batch element uses the ERC-7730 `calldata` format with callee `@.to` and `amountPath: @.value`. Each element is a delegatecall into this contract (base/Multicall.sol lines 11-27), so `msg.sender` and `msg.value` are kept. The outer screen shows "ETH Sent". No other parameter carries calldata: `safeTransferFrom` `_data` is opaque bytes for `onERC721Received`, and the callback `data` is an ABI-encoded struct.

**Pins.** The `@.value` `mustMatch [0]` pins stay on all 15 payable functions, and they still apply inside `multicall` through `amountPath`. So a `multicall` that pays ETH stays blind, which covers the app's `mint + refundETH` and `increaseLiquidity + refundETH`. Unused ETH stays in the contract (PeripheryPayments.sol lines 58-61), and anyone can take it with `refundETH` (lines 44-46). A per-element descriptor cannot require a later `refundETH` in the same batch.

**What the screens say (additions).**
- `multicall`: "Send {value} and run every action below in one transaction; if one action fails, the whole transaction reverts" (Multicall.sol lines 16-23). Each action renders with its own format. "to you" in `refundETH` stays true, because a delegatecall keeps `msg.sender`.
- `collect` now adds: "The zero address keeps them in this contract, where any caller can sweep them" (NonfungiblePositionManager.sol line 318). The app's remove-to-ETH batch uses `recipient = 0`, then `unwrapWETH9` and `sweepToken`.

**Tests.** 20 cases: the 19 earlier ones, with the `collect` expectation updated, and one encoded empty `multicall`. Eight real app batches render correctly in both registry runners but cannot be committed. The pinned Rust runner rejects a nested `interpolatedIntent` in `expected`, and the Sourcify runner requires it. Those batches are `0x3e486a3e…a8dc`, `0xd74eede2…b34b`, `0x92f975da…2dec`, `0x055c644d…b8f9`, `0x21ecb1d0…503e`, `0xb938e5bd…f570`, `0x2c3cc358…98e2` and `0x70c3dfd8…ff27`. They cover mint + refundETH, decrease + collect, collect + unwrap + sweep, collect + increase, the full remove flow with burn, selfPermitIfNecessary + mint, and createAndInitializePoolIfNecessary + mint.

**Checks.** Lint at the registry pin: 0 errors, 2 warnings. Sourcify runner `9d6d2fe4` 20/20, Rust runner `65af2281` 20/20. The eight real batches: Sourcify 8/8, and Rust 8/8 with the nested `interpolatedIntent` removed. A language-model agent added the `calldata` format and the tests by hand, because clear-signing-helper does not support that format. `claims` was not run again for these changes.

**Tool limitation (runners).** For an inner format with an `interpolatedIntent`, no `expected` block passes both runners. Sourcify (`compareNestedDisplay`) requires the nested `interpolatedIntent`. The Rust runner's `NestedExpected` uses `deny_unknown_fields` and rejects it. Either runner needs a fix before real nested cases can be committed.
