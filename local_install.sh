#!/bin/sh
# Build vvm.pyz from the local source tree and install it, overriding the
# `vvm` command already on PATH (or installing it if not present).
#
# Usage:
#   ./local_install.sh
#
# Environment overrides:
#   VVM_PYTHON    interpreter used to build   (default: python3)
#   VVM_BIN_DIR   directory to install into   (default: dir of the `vvm` on PATH,
#                                              else ~/.local/bin)
#   VVM_TARGET    full path to install as     (overrides VVM_BIN_DIR)

set -eu

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
PYZ="$ROOT/dist/vvm.pyz"
ACTION="${1:-install}"

log() { printf 'vvm: %s\n' "$*" >&2; }
fail() {
    log "error: $*"
    exit 1
}
have() { command -v "$1" >/dev/null 2>&1; }

choose_python() {
    for candidate in "${VVM_PYTHON:-}" python3 python; do
        [ -n "$candidate" ] || continue
        if have "$candidate" &&
            "$candidate" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)' 2>/dev/null; then
            printf '%s' "$candidate"
            return 0
        fi
    done
    return 1
}

resolve_target() {
    if [ -n "${VVM_TARGET:-}" ]; then
        printf '%s' "$VVM_TARGET"
        return
    fi
    if [ -n "${VVM_BIN_DIR:-}" ]; then
        printf '%s/vvm' "$VVM_BIN_DIR"
        return
    fi
    for name in vvm vvm.pyz; do
        existing="$(command -v "$name" 2>/dev/null || true)"
        if [ -n "$existing" ]; then
            printf '%s' "$existing"
            return
        fi
    done
    printf '%s/vvm' "$HOME/.local/bin"
}

do_install() {
    python="$(choose_python)" || fail "Python 3.11+ is required to build vvm.pyz"
    log "building ${PYZ} with ${python}"
    "$python" "$ROOT/scripts/build_zipapp.py" -o "$PYZ"

    target="$(resolve_target)"
    target_dir="$(dirname "$target")"
    mkdir -p "$target_dir"

    if [ -e "$target" ] && [ ! -w "$target" ]; then
        fail "cannot overwrite ${target} (permission denied)"
    fi
    rm -f "$target"
    cp "$PYZ" "$target"
    chmod +x "$target"

    log "installed ${target} (from ${PYZ})"
    case ":${PATH}:" in
        *":${target_dir}:"*) ;;
        *) log "note: ${target_dir} is not on your PATH" ;;
    esac
    log "done. Run: vvm --help"
}

usage() {
    printf '%s\n' \
        "local_install.sh — build and install vvm from this checkout" \
        "" \
        "Usage: ./local_install.sh" \
        "" \
        "Environment overrides: VVM_PYTHON, VVM_BIN_DIR, VVM_TARGET"
}

case "$ACTION" in
    install) do_install ;;
    -h | --help | help) usage ;;
    *) fail "unknown action '$ACTION' (try --help)" ;;
esac
