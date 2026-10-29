# Nested-call test cases kept outside the registry

These real mainnet cases render an embedded call whose descriptor has an `interpolatedIntent`. The test schema allows a nested `interpolatedIntent` (`definitions.renderedOutput` in `specs/erc7730-tests-v2.schema.json`), and the Sourcify runner requires it. The Rust runner at `65af2281` rejects it (`NestedExpected` in `crates/cs-test/src/schema.rs` has `deny_unknown_fields`). So these cases are not in the testsv2 files yet.

Each file has the shape of a testsv2 file. Its `descriptor` is relative to `registry/<entity>/testsv2/`. When the registry runs a Rust runner that accepts a nested `interpolatedIntent`, append the `tests` and merge the `dataProvider` of each file into `registry/<entity>/testsv2/calldata-<Name>.tests.json`.

The expected values were generated with the Sourcify runner `9d6d2fe4` against the descriptors of commit `a7496d9`, and all 23 cases pass there.
