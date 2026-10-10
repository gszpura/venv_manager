# vvm

Have too many venvs and want to reuse them, because half of them are pytorch anyway?
Do this:
```commandline
vvm best
```
in your project directory.

## How it works?

`vvm` discovers all vens in common dirs
and picks the one that delivers minimal requirements from your requirements.txt or pyproject.toml.

## Install

### Standalone (no Python tooling required)

`vvm` ships as a single-file executable (`vvm.pyz`) that only needs a Python
3.11+ interpreter. Install the latest release with:

```sh
curl -fsSL https://raw.githubusercontent.com/gszpura/venv_manager/main/install.sh | sh
```

This downloads `vvm.pyz` into `~/.local/bin/vvm`. Override the location or pin a
version with environment variables:

```sh
# pin a release tag
curl -fsSL https://raw.githubusercontent.com/gszpura/venv_manager/main/install.sh | VVM_VERSION=v0.1.0 sh

# install somewhere else
curl -fsSL https://raw.githubusercontent.com/gszpura/venv_manager/main/install.sh | VVM_BIN_DIR="$HOME/bin" sh
```

Uninstall:

```sh
curl -fsSL https://raw.githubusercontent.com/gszpura/venv_manager/main/install.sh | sh -s -- uninstall
```

Other supported variables: `VVM_REPO`, `VVM_ASSET`, `VVM_RELEASE_BASE`,
`VVM_PYZ_URL`, `VVM_NO_VERIFY`.

### From the package / source

```bash
pip install .
# or, for development
pip install -e ".[dev]"

# isolated tool installs
uv tool install git+https://github.com/gszpura/venv_manager
pipx install git+https://github.com/gszpura/venv_manager
```

## Usage

```bash
vvm list            # list detected virtual environments (alias: vvm detect)
vvm best            # find and link the best venv for the current project
vvm unlink          # remove the venv link created by `best`
vvm config          # show the config path, its contents, and default search paths
```

Common options: `-C/--directory` to target a project directory, `--config` to
use a specific config file, and `--no-cache` to ignore the venv cache.

See [RELEASE.md](RELEASE.md) for the release process and how to build the
standalone executable.
