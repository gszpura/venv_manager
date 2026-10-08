#!/bin/sh
# vvm installer — downloads the standalone vvm.pyz release artifact.
#
# Quick start:
#   curl -fsSL https://raw.githubusercontent.com/anomalyco/vvm/main/install.sh | sh
#
# Pin a version:
#   curl -fsSL https://raw.githubusercontent.com/anomalyco/vvm/main/install.sh | VVM_VERSION=v0.1.0 sh
#
# Uninstall:
#   curl -fsSL https://raw.githubusercontent.com/anomalyco/vvm/main/install.sh | sh -s -- uninstall
#
# Environment overrides:
#   VVM_REPO      GitHub owner/repo            (default: anomalyco/vvm)
#   VVM_VERSION   release tag, or "latest"     (default: latest)
#   VVM_BIN_DIR   install directory            (default: ~/.local/bin)
#   VVM_ASSET     release asset filename       (default: vvm.pyz)
#   VVM_RELEASE_BASE  base URL for a mirror (overrides repo/version)
#   VVM_PYZ_URL   full URL/path to the .pyz    (overrides repo/version)
#   VVM_NO_VERIFY set to 1 to skip SHA256 verification
#
# vvm.pyz is a single-file executable that needs a Python 3.11+ interpreter on
# PATH; no pip, venv or other Python tooling is required.

set -eu

REPO="${VVM_REPO:-anomalyco/vvm}"
VERSION="${VVM_VERSION:-latest}"
BIN_DIR="${VVM_BIN_DIR:-$HOME/.local/bin}"
ASSET="${VVM_ASSET:-vvm.pyz}"
ACTION="${1:-install}"

log() { printf 'vvm: %s\n' "$*" >&2; }
fail() {
    log "error: $*"
    exit 1
}
have() { command -v "$1" >/dev/null 2>&1; }

release_base() {
    if [ -n "${VVM_RELEASE_BASE:-}" ]; then
        printf '%s' "$VVM_RELEASE_BASE"
    elif [ "$VERSION" = "latest" ]; then
        printf '%s' "https://github.com/${REPO}/releases/latest/download"
    else
        printf '%s' "https://github.com/${REPO}/releases/download/${VERSION}"
    fi
}

asset_url() {
    if [ -n "${VVM_PYZ_URL:-}" ]; then
        printf '%s' "$VVM_PYZ_URL"
    else
        printf '%s/%s' "$(release_base)" "$ASSET"
    fi
}

sha256_of() {
    if have sha256sum; then
        sha256sum "$1" | cut -d ' ' -f 1
    elif have shasum; then
        shasum -a 256 "$1" | cut -d ' ' -f 1
    else
        return 1
    fi
}

verify_checksum() {
    file="$1"
    [ "${VVM_NO_VERIFY:-0}" = "1" ] && return 0
    if [ -n "${VVM_PYZ_URL:-}" ]; then
        return 0
    fi

    sums="$(release_base)/SHA256SUMS"
    if ! curl -fsSL "$sums" -o "$TMPDIR_PATH/SHA256SUMS" 2>/dev/null; then
        log "note: no SHA256SUMS published; skipping verification"
        return 0
    fi
    expected="$(grep " ${ASSET}\$" "$TMPDIR_PATH/SHA256SUMS" | head -n 1 | cut -d ' ' -f 1)"
    [ -n "$expected" ] || fail "no checksum entry for ${ASSET}"
    actual="$(sha256_of "$file")" || {
        log "note: no sha256 tool available; skipping verification"
        return 0
    }
    [ "$expected" = "$actual" ] || fail "checksum mismatch for ${ASSET}"
    log "checksum verified"
}

check_python() {
    for candidate in python3 python; do
        if have "$candidate" && "$candidate" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)' 2>/dev/null; then
            return 0
        fi
    done
    log "warning: vvm needs Python 3.11+ on PATH; none found"
    log "         install Python 3.11+ or the command will fail at runtime"
}

ensure_path() {
    case ":${PATH}:" in
        *":${BIN_DIR}:"*) ;;
        *)
            log "${BIN_DIR} is not on your PATH. Add it with:"
            log "  export PATH=\"${BIN_DIR}:\$PATH\""
            ;;
    esac
}

do_install() {
    have curl || fail "curl is required"

    url="$(asset_url)"
    log "downloading ${url}"

    TMPDIR_PATH="$(mktemp -d)"
    trap 'rm -rf "$TMPDIR_PATH"' 0 2 15

    curl -fsSL "$url" -o "$TMPDIR_PATH/$ASSET" || fail "download failed: ${url}"
    [ -s "$TMPDIR_PATH/$ASSET" ] || fail "downloaded file is empty"
    verify_checksum "$TMPDIR_PATH/$ASSET"

    mkdir -p "$BIN_DIR"
    chmod +x "$TMPDIR_PATH/$ASSET"
    mv "$TMPDIR_PATH/$ASSET" "$BIN_DIR/vvm"

    log "installed vvm to ${BIN_DIR}/vvm"
    check_python
    ensure_path
    log "done. Run: vvm --help"
}

do_uninstall() {
    target="${BIN_DIR}/vvm"
    if [ -e "$target" ]; then
        rm -f "$target"
        log "removed ${target}"
    else
        log "nothing to remove at ${target}"
    fi
}

usage() {
    printf '%s\n' \
        "vvm installer" \
        "" \
        "Usage: install.sh [install|uninstall]" \
        "" \
        "Environment overrides: VVM_REPO, VVM_VERSION, VVM_BIN_DIR," \
        "VVM_ASSET, VVM_RELEASE_BASE, VVM_PYZ_URL, VVM_NO_VERIFY"
}

case "$ACTION" in
    install) do_install ;;
    uninstall | --uninstall) do_uninstall ;;
    -h | --help | help) usage ;;
    *) fail "unknown action '$ACTION' (use install|uninstall)" ;;
esac
