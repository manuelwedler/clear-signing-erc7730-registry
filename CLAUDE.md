# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

The **ERC-7730 Clear Signing Registry** is a curated collection of JSON descriptor files that enable hardware wallets (Ledger) to display human-readable transaction details when signing EVM smart contract calls and EIP-712 typed messages. Each entity (protocol/dApp) maintains a folder under `registry/` with their descriptors.

## File naming conventions

Under `registry/<entity-name>/`:
- `calldata-<ContractName>.json` — calldata descriptor for a smart contract
- `eip712-<MessageName>.json` — EIP-712 typed message descriptor
- `common-<sharedDef>.json` — shared definitions included by other descriptors (no `calldata`/`eip712` prefix)
- `tests/<descriptor-name>.tests.json` — reference test cases for a descriptor

## Environment setup

Copy `tools/scripts/env.example` to `.env` at the project root and fill in keys:

```bash
cp tools/scripts/env.example .env
# Then set: ETHERSCAN_API_KEY, OPENAI_API_KEY or ANTHROPIC_API_KEY, GATING_TOKEN
source .env
```

## Linting and validation

Setup (first time only):
```bash
cd tools/linter && ./setup.sh
```

Lint all descriptors:
```bash
source .env && source tools/linter/.venv/bin/activate && erc7730 lint registry/
```

Lint a specific file:
```bash
source .env && source tools/linter/.venv/bin/activate && erc7730 lint registry/<entity>/calldata-Contract.json
```

Requires Python 3.12+. CI runs `erc7730 lint` on all changed `calldata-*.json` and `eip712-*.json` files.

## Generating descriptors

Generate from an on-chain contract address:
```bash
source .env && node tools/scripts/generate-7730.js \
  --address 0xContractAddress \
  --chain 1 \
  --output registry/<entity> \
  --name "Protocol Name"
```

Backends: `--backend openai` (default), `--backend anthropic`, `--backend cursor` (no API key needed inside Cursor).

## Generating test files

Generate tests from real blockchain transactions:
```bash
source .env && node tools/scripts/generate-tests.js registry/<entity>/calldata-Contract.json
```

Key options: `--dry-run`, `--no-test` (skip device emulator), `--depth <n>` (tx search depth), `--max-tests <n>`.

## Running device emulator tests

Setup (first time only — requires Docker, pnpm, and access to private `LedgerHQ/coin-apps`):
```bash
cd tools/tester && ./setup.sh
```

Run a test:
```bash
export GATING_TOKEN='your-token'
cd tools/tester && ./run-test.sh \
  ../../registry/<entity>/calldata-Contract.json \
  ../../registry/<entity>/tests/calldata-Contract.tests.json \
  flex   # device: flex, stax, nanosp, nanox
```

## Schema migration (v1 → v2)

Migrate a single file:
```bash
node tools/scripts/migrate-v1-to-v2.js --file registry/<entity>/calldata-Contract.json
```

Migrate with preview:
```bash
node tools/scripts/migrate-v1-to-v2.js --dry-run --verbose
```

## Batch processing

Orchestrate migration + test generation + PR creation for an entire entity folder:
```bash
source .env && node tools/scripts/batch-process.js <entity-name> --pr
```

Use `--dry-run --verbose` to preview. Use `--skip-tests` or `--skip-migration` to run only one phase.

Two ordering modes:
- **Migrate-first** (default): migrate all files to v2, then generate tests — use when the entity has external deps (e.g., references `ercs/`)
- **Test-first** (`--test-first`): generate tests on v1, then migrate — use when no external deps or deps are already v2

## Validate function signatures against on-chain ABIs

```bash
source .env && node tools/scripts/check-contract-functions.js \
  --file registry/<entity>/calldata-Contract.json \
  --all-chains
```

## Architecture overview

```
registry/           # Descriptor files, one folder per entity/protocol
ercs/               # Standard ERC descriptors (ERC20, ERC721, ERC4626, etc.) shared across entities
specs/              # JSON schemas (erc7730-v2.schema.json is the current standard) and spec markdown
                    # — do not edit; synced weekly from ethereum/ERCs upstream
tools/
  scripts/          # Node.js scripts: generate-7730.js, generate-tests.js, migrate-v1-to-v2.js,
                    #   batch-process.js, check-contract-functions.js
  linter/           # Python erc7730 CLI setup (virtualenv)
  tester/           # Ledger Speculos device emulator test runner (Docker-based)
  analyzer/         # Supplementary analysis tooling
.cursor/rules/      # Per-tool usage rules (consulted by generate-7730.mdc, lint-erc7730.mdc, etc.)
```

The `specs/erc7730-v2.schema.json` is the authoritative schema for all new and migrated descriptors. The v2 format uses human-readable ABI signatures as format keys (e.g., `"transfer(address to, uint256 amount)"`) instead of v1's hex selectors, and uses `visible: "always"` / `visible: "never"` instead of `required`/`excluded` arrays.
