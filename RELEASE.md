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

## Installer

[`local_install.sh`](local_install.sh) builds `vvm.pyz` from this checkout and
installs it, overriding the `vvm` already on `PATH` (or installing it if not
present):

```bash
./local_install.sh
```

It supports the following environment variables:

| Variable      | Default                                               |
| ------------- | ----------------------------------------------------- |
| `VVM_PYTHON`  | `python3` (interpreter used to build `vvm.pyz`)       |
| `VVM_BIN_DIR` | directory of the `vvm` on `PATH`, else `~/.local/bin` |
| `VVM_TARGET`  | full install path; overrides `VVM_BIN_DIR`            |

The existing target is replaced with the freshly built `vvm.pyz`. The installer
fails if the target is not writable.
