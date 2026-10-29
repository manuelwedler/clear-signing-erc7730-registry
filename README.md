# Test reports

This branch is written by the Descriptor Test Results workflow. Do not edit it by hand, and do not base work on it: it has no shared history with `master`, and it can be recreated from scratch at any time.

Each run of the Descriptor Tests workflow on a pull request adds one bundle, and updates the index of that pull request:

```
pr/<pull request number>/<run id>.json   the bundle of one run
pr/<pull request number>/index.json      the runs of the pull request, newest first
```

The bundle format is documented in `.github/test-runner-docs/bundle.md` on `master`. The test report viewer reads the files from `raw.githubusercontent.com`.
