# vvm

Discover Python virtual environments scattered across a machine and match the
best one to the current project.

## Install

### Standalone (no Python tooling required)

`vvm` ships as a single-file executable (`vvm.pyz`) that only needs a Python
3.11+ interpreter. Install the latest release with:

```sh
curl -fsSL https://raw.githubusercontent.com/anomalyco/vvm/main/install.sh | sh
```

This downloads `vvm.pyz` into `~/.local/bin/vvm`. Override the location or pin a
version with environment variables:

```sh
# pin a release tag
curl -fsSL https://raw.githubusercontent.com/anomalyco/vvm/main/install.sh | VVM_VERSION=v0.1.0 sh

# install somewhere else
curl -fsSL https://raw.githubusercontent.com/anomalyco/vvm/main/install.sh | VVM_BIN_DIR="$HOME/bin" sh
```

Uninstall:

```sh
curl -fsSL https://raw.githubusercontent.com/anomalyco/vvm/main/install.sh | sh -s -- uninstall
```

Other supported variables: `VVM_REPO`, `VVM_ASSET`, `VVM_PYZ_URL`,
`VVM_NO_VERIFY`.

### From the package / source

```bash
pip install .
# or, for development
pip install -e ".[dev]"

# isolated tool installs
uv tool install git+https://github.com/anomalyco/vvm
pipx install git+https://github.com/anomalyco/vvm
```

## Usage

```bash
vvm detect          # list detected virtual environments
vvm best            # find the best venv for the current project
```

## Releases

Pushing a `v*` tag (for example `v0.1.0`) triggers the `release` workflow,
which runs the test suite, builds the wheel/sdist and the standalone
`vvm.pyz`, generates `SHA256SUMS`, and publishes them to a GitHub Release.
`workflow_dispatch` runs the same build but uploads artifacts instead of
releasing.

To build the standalone executable locally:

```bash
python scripts/build_zipapp.py -o dist/vvm.pyz
./dist/vvm.pyz --version
```
