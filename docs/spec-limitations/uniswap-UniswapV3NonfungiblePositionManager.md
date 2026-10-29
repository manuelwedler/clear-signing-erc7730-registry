# Uniswap V3 NonfungiblePositionManager — ERC-7730 spec limitations

## Token amounts whose token lives in contract storage
- **What the signer should see:** `increaseLiquidity`, `decreaseLiquidity` and `collect` take amounts (`amount0Desired`, `amount0Min`, `amount0Max`, …) in the two tokens of the position's pool. The signer should see "up to 1.5 WETH and up to 3000 USDC", with tickers and decimals.
- **What the spec cannot express:** `tokenAmount` resolves the token only from a constant (`token`) or from a path into the calldata or the transaction (`tokenPath`), see "Field formats > tokenAmount". Here the token is `_poolIdToPoolKey[_positions[tokenId].poolId].token0`, a storage value keyed by the `tokenId` argument. No path reference can read contract state, and no format can call a view function.
- **Why a map does not help:** each `tokenId` has its own pair, fixed at mint, and there are 1,244,243 positions (`totalSupply()` on 2026-10-29), growing by about a thousand mints a week. A `metadata.maps` entry per position is far too large and would always be out of date.
- **Workaround in this descriptor:** the amounts are shown with `raw` and labels that say so ("Max Token0 (raw)", "Min Token0 Due (raw)"); the sentence says "(raw units)". The position is shown with `nftName` so the signer at least knows which position is touched.
- **Proposed spec improvement:** an `eth_call`-backed reference for `tokenPath`, e.g. `{"call": {"to": "@.to", "function": "positions(uint256)", "args": ["params.tokenId"], "output": "token0"}}`, restricted to view functions of the contract being called, with the wallet allowed to fall back to the raw value when it cannot make the call.

## No sentinel message for integer formats other than amounts
- **What the signer should see:** `collect` is almost always called with `amount0Max = amount1Max = type(uint128).max`, which the contract clamps to what the position is owed (NonfungiblePositionManager.sol lines 354-358). The signer should read "all owed token0".
- **What the spec cannot express:** `threshold` and `message` exist only on `amount` and `tokenAmount` ("Field formats > amount, tokenAmount"). `raw` and `unit` render the number as is. Because the token cannot be resolved (previous section), `tokenAmount` is not usable, so the sentinel cannot be labelled.
- **Workaround in this descriptor:** the value renders as `340282366920938463463374607431768211455`. The label says "Max" and the sentence says "up to", so the screen stays true; the test case shows the real rendering.
- **Proposed spec improvement:** allow `threshold` and `message` on `raw` and `unit`, or better, a `specialValues` map on every format (ethereum/ERCs PR 2027 adds it to `date` only), for example `{"340282366920938463463374607431768211455": "All owed"}`. This is wishlist item 7.

## Price ranges given as ticks
- **What the signer should see:** `mint` sets the position's price range with `tickLower` and `tickUpper`; the price bound is `1.0001^tick` scaled by the two tokens' decimals. The signer should read "Range: 1,800 to 2,200 USDC per WETH".
- **What the spec cannot express:** no format applies an exponent or a decimals ratio of two other fields; `unit` only scales by a power of ten ("Field formats > unit").
- **Workaround in this descriptor:** the ticks are shown raw as "Lower Tick" and "Upper Tick". A raw tick is not readable as a price, but the signer can at least see and compare the range. Strict portability flags negative signed integers for some Ledger devices; both registry runners render them correctly.
- **Proposed spec improvement:** a `tick` (or general `exponential`) integer format with parameters `base` (1.0001), `decimals0Path`, `decimals1Path` and an `invert` flag, rendering the price of one token in the other.

## Q64.96 square-root prices
- **What the signer should see:** `createAndInitializePoolIfNecessary` sets the pool's starting price from `sqrtPriceX96`; the price is `(sqrtPriceX96 / 2^96)^2` adjusted for decimals. The signer should read "Starting price: 2,000 USDC per WETH".
- **What the spec cannot express:** no format squares a value or divides by a power of two; `unit` scales by powers of ten only ("Field formats > unit").
- **Workaround in this descriptor:** the value is shown with `raw` and the label "Sqrt Price (Q64.96)". No funds move in this call, so the screen is complete even though the price is not readable.
- **Proposed spec improvement:** a fixed-point format with `fractionalBits` (96) and an optional `power` (2), combined with the decimals parameters proposed above.

## Owner of the position a call funds
- **What the signer should see:** `increaseLiquidity` has no `isAuthorizedForToken` check (NonfungiblePositionManager.sol lines 198-202; compare `decreaseLiquidity` at line 261). It pulls the tokens from `msg.sender` (LiquidityManagement.sol line 85) into any position. The signer should see "Position #123, owned by you" or "owned by 0xabc…", so that a dapp cannot make them fund a position someone else owns.
- **What the spec cannot express:** the owner is `ownerOf(tokenId)`, contract state. `nftName` shows the collection and the id only, and no path reference reads state ("Field formats > nftName", "Path references").
- **Workaround in this descriptor:** the screen shows the position as "Uniswap V3 Positions NFT-V1 #<id>". The sentence says "to position <id>" and does not claim the position is the signer's.
- **Proposed spec improvement:** the same `eth_call`-backed reference proposed in the first section, usable from `addressName` (e.g. `ownerOf(tokenId)` compared against `@.from`, rendered as "you" when equal).

## No condition across the elements of a batch
- **What the signer should see:** "Pay 0.01 ETH; up to 0.01 WETH is added to the position and the rest returns to you." This is true for `multicall([mint, refundETH])` with ETH.
- **What the spec cannot express:** the `calldata` format renders each element of `data.[]` alone (Embedded Calldata; Field formats > calldata). `visible`/`mustMatch` checks one value. Nothing can say "this element's `@.value` may be non-zero only if a later element calls `refundETH`".
- **Workaround in this descriptor:** `@.value` stays pinned to 0 in `mint` and `increaseLiquidity`. ETH-paying batches are not clear-signed.
- **Proposed spec improvement:** a batch-level rule on a `calldata` array field, for example `"requires": [{"selector": "0x12210e8a", "after": "self"}]`. Under it, an element's pins on `@.value` are relaxed only when the required element is present.

## Zero address that stands for this contract
- **What the signer should see:** in `collect`, `recipient = address(0)` means "keep the tokens in the position manager itself" (NonfungiblePositionManager.sol line 318), where any caller can take them with `sweepToken` or `unwrapWETH9`. The Uniswap app's remove-to-ETH batch uses exactly this (`collect` to zero, then `unwrapWETH9` and `sweepToken`). The signer should read "Recipient: this contract (any caller can sweep)", not a zero address.
- **What the spec cannot express:** `addressName` has no value-to-label map: it has `senderAddress`, which maps a value to the signer, but nothing that maps a value to the called contract or to a text. `enum` applies only to integers. The visibility rules do not help either: `ifNotIn: ["0x0000000000000000000000000000000000000000"]` can hide the zero address but cannot show a text in its place, and `mustMatch` would refuse every real recipient ("Field formats > addressName, enum"; "Field format specification > visible").
- **Workaround in this descriptor:** the recipient is shown with `addressName`, so a zero recipient shows as `0x0000…0000`, and the `collect` sentence explains it: "The zero address keeps them in this contract, where any caller can sweep them".
- **Proposed spec improvement:** a `specialValues` map on `addressName` (and every other format), for example `{"0x0000000000000000000000000000000000000000": "This contract (any caller can sweep)"}`. ethereum/ERCs PR 2027 adds `specialValues` to `date` only. This is wishlist item 7.

