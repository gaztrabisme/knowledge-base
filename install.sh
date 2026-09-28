#!/usr/bin/env bash
#
# Usage (default core edition):
#   ./install.sh
# Usage (full edition):
#   ./install.sh --edition full
# Usage with custom options:
#   ./install.sh --edition full --dir ~/my-kb --qdrant-port 6343 --update

set -euo pipefail

EDITION="core"
INSTALL_DIR="${HOME}/knowledge-base"
UPDATE=false
QDRANT_PORT=6333

usage() {
    cat <<EOF
Usage: $0 [OPTIONS]

Options:
  --edition <core|full>  Edition to install (default: core)
  --dir <path>           Install directory (default: ~/knowledge-base)
  --update               Update existing installation keeping data
  --qdrant-port <port>   Qdrant port (default: 6333)
  -h, --help             Show this help message
EOF
    exit 0
}

while [ $# -gt 0 ]; do
    case "$1" in
        --edition)
            if [ $# -lt 2 ]; then
                echo "Error: --edition requires an argument." >&2
                exit 1
            fi
            EDITION="$2"
            shift 2
            ;;
        --edition=*)
            EDITION="${1#*=}"
            shift
            ;;
        --dir)
            if [ $# -lt 2 ]; then
                echo "Error: --dir requires an argument." >&2
                exit 1
            fi
            INSTALL_DIR="$2"
            shift 2
            ;;
        --dir=*)
            INSTALL_DIR="${1#*=}"
            shift
            ;;
        --update)
            UPDATE=true
            shift
            ;;
        --qdrant-port)
            if [ $# -lt 2 ]; then
                echo "Error: --qdrant-port requires an argument." >&2
                exit 1
            fi
            QDRANT_PORT="$2"
            shift 2
            ;;
        --qdrant-port=*)
            QDRANT_PORT="${1#*=}"
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo "Error: Unknown argument: $1" >&2
            exit 1
            ;;
    esac
done

if [ "$EDITION" != "core" ] && [ "$EDITION" != "full" ]; then
    echo "Error: --edition must be 'core' or 'full', got '$EDITION'" >&2
    exit 1
fi

case "$INSTALL_DIR" in
    "~"/*)
        INSTALL_DIR="${HOME}/${INSTALL_DIR#"~/"}"
        ;;
    "~")
        INSTALL_DIR="${HOME}"
        ;;
esac

TOKEN_PROMPTED=false
if [ -z "${KB_GH_TOKEN:-}" ]; then
    printf "Enter GitHub Personal Access Token (fine-grained, Contents: Read-only): " >&2
    read -r -s KB_GH_TOKEN
    echo >&2
    if [ -z "$KB_GH_TOKEN" ]; then
        echo "Error: Token cannot be empty." >&2
        exit 1
    fi
    export KB_GH_TOKEN
    TOKEN_PROMPTED=true
fi

TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/kb-install.XXXXXX")"
chmod 700 "$TMP_DIR"

cleanup() {
    rm -rf "$TMP_DIR"
    if [ "$TOKEN_PROMPTED" = true ]; then
        unset KB_GH_TOKEN
    fi
}
trap cleanup EXIT INT TERM

HEADER_FILE="$TMP_DIR/headers.txt"
(
    umask 077
    cat <<EOF > "$HEADER_FILE"
Authorization: Bearer ${KB_GH_TOKEN}
Accept: application/vnd.github+json
X-GitHub-Api-Version: 2022-11-28
User-Agent: knowledge-base-installer
EOF
)

if ! command -v uv >/dev/null 2>&1; then
    echo "uv not found; installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    if [ -d "$HOME/.local/bin" ]; then
        PATH="$HOME/.local/bin:$PATH"
    fi
    if [ -d "$HOME/.cargo/bin" ]; then
        PATH="$HOME/.cargo/bin:$PATH"
    fi
    export PATH
    if ! command -v uv >/dev/null 2>&1; then
        echo "Error: uv was installed but not found on PATH." >&2
        exit 1
    fi
fi

ZIP_URL="https://api.github.com/repos/gaztrabisme/knowledge-base/zipball/main"
ZIP_FILE="$TMP_DIR/code.zip"

echo "Downloading repository zipball..."
HTTP_STATUS=$(curl -sSL -w "%{http_code}" -o "$ZIP_FILE" --header @"$HEADER_FILE" "$ZIP_URL" || echo "CURL_ERROR")

if [ "$HTTP_STATUS" = "CURL_ERROR" ]; then
    echo "Error: Network request failed while downloading repository zipball." >&2
    exit 1
fi

if [ "$HTTP_STATUS" = "401" ] || [ "$HTTP_STATUS" = "403" ] || [ "$HTTP_STATUS" = "404" ]; then
    echo "Error (HTTP $HTTP_STATUS): token expired or lacks Contents: Read on gaztrabisme/knowledge-base." >&2
    exit 1
elif [ "$HTTP_STATUS" != "200" ]; then
    echo "Error: Failed to download repository zipball (HTTP $HTTP_STATUS)." >&2
    exit 1
fi

EXTRACT_DIR="$TMP_DIR/extracted"
mkdir -p "$EXTRACT_DIR"

echo "Unpacking archive..."
if command -v unzip >/dev/null 2>&1; then
    unzip -q "$ZIP_FILE" -d "$EXTRACT_DIR"
elif command -v python3 >/dev/null 2>&1; then
    python3 -m zipfile -e "$ZIP_FILE" "$EXTRACT_DIR"
else
    echo "Error: Neither unzip nor python3 found to extract archive." >&2
    exit 1
fi

SRC_DIR=""
for d in "$EXTRACT_DIR"/*; do
    if [ -d "$d" ]; then
        SRC_DIR="$d"
        break
    fi
done

if [ -z "$SRC_DIR" ]; then
    SRC_DIR="$EXTRACT_DIR"
fi

mkdir -p "$INSTALL_DIR"

echo "Copying files to $INSTALL_DIR..."
if command -v rsync >/dev/null 2>&1; then
    rsync -a "$SRC_DIR/" "$INSTALL_DIR/"
else
    cp -R "$SRC_DIR/." "$INSTALL_DIR/"
fi

INSTALL_SCRIPT="$INSTALL_DIR/scripts/install.py"
if [ ! -f "$INSTALL_SCRIPT" ]; then
    echo "Error: Installer script not found at $INSTALL_SCRIPT" >&2
    exit 1
fi

echo "Running scripts/install.py with uv..."
CMD=(uv run --project "$INSTALL_DIR" python "$INSTALL_SCRIPT" --dir "$INSTALL_DIR" --edition "$EDITION" --qdrant-port "$QDRANT_PORT")
if [ "$UPDATE" = true ]; then
    CMD+=(--update)
fi

"${CMD[@]}"
