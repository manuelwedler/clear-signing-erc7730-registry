# Agent instructions: allow `chainId` / `chainIdPath` in the ERC-7730 `calldata` format schema

Paste the block below into a local coding agent that can open pull requests on ethereum/ERCs as Manuel Wedler (through a fork).

```text
Open a pull request on ethereum/ERCs that adds `chainId` and `chainIdPath` to the parameters of the ERC-7730 `calldata` field format in the JSON schema. Open it from a fork, as a normal (not draft) PR unless the repo's rules say otherwise. Do not change anything else in the spec.

Background:
- ERC-7730 (ERCS/erc-7730.md, status Draft) already lists the parameter in the `calldata` format table: "`chainIdPath` or `chainId` | Optional. Specifies the chain ID if it differs from the current contract's chain."
- The schema does not allow it. In assets/erc-7730/, `$format/calldataParameters` has only callee, calleePath, selector, selectorPath, amount, amountPath, spender and spenderPath, with `additionalProperties: false`. So a descriptor that uses `chainId` on a `calldata` field fails schema validation and the registry linter.
- The `tokenAmount` parameters already define the same pair. Copy their shape:
  - `chainId`: `{"title": "Chain ID", "type": ["integer", "object"], "anyOf": [{"type": "integer"}, {"$ref": "#/$format/mapReference"}], "description": "Optional. The chain ID of the called contract, if it differs from the current contract's chain."}`
  - `chainIdPath`: `{"title": "Chain ID Path", "type": "string", "description": "Optional. The path to the chain ID of the called contract, if it differs from the current contract's chain."}`
- Real use: an OP Stack L1 portal's `depositTransaction(_to, _value, _gasLimit, _isCreation, _data)` runs `_data` as a call to `_to` on the L2 chain (for example Base, chain 8453). With `chainId` the wallet resolves the callee's descriptor on the right chain. Both registry test runners (Sourcify and Rust) already render it.

Versioning (follow the "Version numbers" and "Schema files and the `$schema` key" sections of ERCS/erc-7730.md exactly):
- This change only accepts more descriptors, so it is a MINOR release on the active v2 line. It does not go through the draft. Release it directly in this PR:
  1. Add a new exact-version file assets/erc-7730/erc7730-v2.2.0.schema.json: a copy of the current newest v2 exact-version file with the two properties added and its top-level `version` key set to "2.2.0". Never edit an existing exact-version file.
  2. Update the alias file assets/erc-7730/erc7730-v2.schema.json so it is a byte-for-byte copy of the new 2.2.0 file.
  3. Add the same two properties to the draft assets/erc-7730/erc7730-v3.0.0-next.schema.json (if `calldataParameters` exists there), so the next major does not lose them.
  4. In the "Released versions" table of ERCS/erc-7730.md, add a row for `2.2.0` (exact file, alias, Commit ID "TBD", Status "Active") and set the `2.1.0` row's Status to "Superseded". Do not alter any other column of existing rows.
  5. The ERC text already describes the parameter; change it only if the wording must match the schema description. The schema and the ERC text change together in this PR.
- Before you start, check the open PRs on ethereum/ERCs that touch ERC-7730 (for example "Custom Encoding Layout for ERC-7730", PR 1925, and any PR that publishes a 2.2.0 schema). If another open PR already releases 2.2.0, do not create a conflicting version. Stop and report which PR it is, and propose adding this change to that release instead.

Checks before pushing:
- Validate the new and changed schema files as JSON Schema (for example with `check-jsonschema --check-metaschema`).
- Validate a sample descriptor field `{"path": "_data", "label": "L2 Call", "format": "calldata", "params": {"calleePath": "_to", "chainId": 8453, "amountPath": "_value"}}` inside a minimal v2 descriptor against the new schema. It must pass, and it must fail against the 2.1.0 file.
- Run the repo's own checks (the EIP/ERC linter `eipw` and any markdown or link checks the repo's CI runs).

PR text:
- Title: "Update ERC-7730: allow chainId in the calldata field format schema".
- Body: what was wrong (the ERC text lists the parameter, the schema rejects it), what changed (the two properties, the 2.2.0 release files, the alias, the versions table), why it is a MINOR release, and the OP Stack portal example. Mention that the registry linter (sourcifyeth/python-erc7730) needs a matching change.
- Follow the repo's PR template if it has one. Do not mention any person with a bare @name. Do not include any Claude session link or model name.

Report back with the PR URL and the check results.
```

A matching change is needed in the registry linter (sourcifyeth/python-erc7730): its model for the `calldata` parameters must accept `chainId` and `chainIdPath`. The registry also mirrors the schema files through its sync-specs workflow, so the new schema arrives there after the ERCs PR merges.
