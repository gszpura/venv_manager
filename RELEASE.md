# Releasing vvm

## Cutting a release

Pushing a `v*` tag triggers the [`release`](.github/workflows/release.yml)
workflow:

```bash
git tag v0.1.0
git push origin v0.1.0
```

The workflow then:

1. installs the project with its dev extras,
2. runs the test suite,
3. builds the wheel and sdist (`python -m build`),
4. builds the standalone `vvm.pyz`,
5. generates `SHA256SUMS`,
6. publishes `vvm.pyz`, the wheel, the sdist and `SHA256SUMS` to a GitHub
   Release with generated release notes.

Running the workflow manually (`workflow_dispatch`) performs the same build but
uploads the artifacts instead of creating a release.

## Build the standalone executable locally

```bash
python scripts/build_zipapp.py -o dist/vvm.pyz
./dist/vvm.pyz --version
```

`vvm.pyz` is a single-file executable with a `#!/usr/bin/env python3` shebang.
It has no runtime dependencies but requires a Python 3.11+ interpreter on
`PATH`.

## Installer

[`install.sh`](install.sh) downloads a released `vvm.pyz` and places it on
`PATH`. It supports the following environment variables:

| Variable           | Default                                              |
| ------------------ | ---------------------------------------------------- |
| `VVM_REPO`         | `gszpura/venv_manager`                               |
| `VVM_VERSION`      | `latest`                                             |
| `VVM_BIN_DIR`      | `~/.local/bin`                                       |
| `VVM_ASSET`        | `vvm.pyz`                                            |
| `VVM_RELEASE_BASE` | GitHub release URL for `VVM_REPO`/`VVM_VERSION`      |
| `VVM_PYZ_URL`      | full URL to `vvm.pyz` (overrides repo/version)       |
| `VVM_NO_VERIFY`    | unset; set to `1` to skip `SHA256SUMS` verification  |

When a release publishes `SHA256SUMS`, the installer verifies the downloaded
artifact against it (skipped when `VVM_PYZ_URL` is set or `VVM_NO_VERIFY=1`).
