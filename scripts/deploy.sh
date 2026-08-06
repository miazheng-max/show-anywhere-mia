#!/usr/bin/env bash
# deploy.sh — publish a generated deck to a public URL via Vercel.
#
# Usage:
#   bash scripts/deploy.sh <deck.html | deck-folder/>
#
#   --yes    Skip the confirmation prompt (only for non-interactive use where
#            the person has already agreed to publish).
#
# ⚠ THIS PUBLISHES PUBLICLY. Anyone with the URL can read the deck, and it may
#   be cached or indexed even after you delete it. Never run this on a deck the
#   person has not explicitly agreed to publish. Check the deck for personal
#   data, client names, or unreleased numbers first.
#
# Requires Node.js (for the Vercel CLI) and a free Vercel account.
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; CYAN='\033[0;36m'
YELLOW='\033[1;33m'; BOLD='\033[1m'; NC='\033[0m'
info() { echo -e "${CYAN}i${NC} $*"; }
ok()   { echo -e "${GREEN}✓${NC} $*"; }
warn() { echo -e "${YELLOW}!${NC} $*"; }
err()  { echo -e "${RED}✗${NC} $*" >&2; }

ASSUME_YES=false
POSITIONAL=()
for arg in "$@"; do
  case "$arg" in
    --yes) ASSUME_YES=true ;;
    *) POSITIONAL+=("$arg") ;;
  esac
done
set -- "${POSITIONAL[@]:-}"

if [[ $# -lt 1 || -z "${1:-}" ]]; then
  err "Usage: bash scripts/deploy.sh <deck.html | deck-folder/> [--yes]"
  exit 1
fi
INPUT="$1"

# ─── Stage the files to upload ────────────────────────────────────────────
CLEANUP_TEMP=false
if [[ -f "$INPUT" && "$INPUT" == *.html ]]; then
  DEPLOY_DIR=$(mktemp -d)
  CLEANUP_TEMP=true
  cp "$INPUT" "$DEPLOY_DIR/index.html"
  PARENT_DIR=$(dirname "$INPUT")

  # Decks from this skill inline their images as data: URIs, so usually there
  # is nothing local to copy. Handle the non-inlined case anyway.
  #
  # The `|| true` matters: under `set -o pipefail`, a fully self-contained deck
  # makes the filtering grep exit 1 (it matches nothing), which would otherwise
  # abort the whole script on the most common input.
  LOCAL_REFS=$(grep -oE '(src|href)=["'"'"'][^"'"'"']+' "$INPUT" 2>/dev/null \
    | sed 's/^[a-z]*=//; s/["'"'"']//g' \
    | grep -Ev '^(https?:|data:|#|/)' | sort -u || true)

  if [[ -n "$LOCAL_REFS" ]]; then
    while IFS= read -r ref; do
      [[ -z "$ref" ]] && continue
      if [[ -e "$PARENT_DIR/$ref" ]]; then
        mkdir -p "$DEPLOY_DIR/$(dirname "$ref")"
        cp -r "$PARENT_DIR/$ref" "$DEPLOY_DIR/$(dirname "$ref")/"
      fi
    done <<< "$LOCAL_REFS"
  fi
elif [[ -d "$INPUT" ]]; then
  if [[ ! -f "$INPUT/index.html" ]]; then
    err "Folder '$INPUT' has no index.html."
    exit 1
  fi
  DEPLOY_DIR="$INPUT"
else
  err "'$INPUT' is not an .html file or a directory."
  exit 1
fi

# ─── Confirm before publishing ────────────────────────────────────────────
echo ""
echo -e "${BOLD}Publish this deck to a public URL?${NC}"
echo "  Source: $INPUT"
echo "  Size:   $(du -sh "$DEPLOY_DIR" | cut -f1 | xargs)"
echo ""
warn "Anyone with the link will be able to read it."
warn "Published pages can be cached or indexed even after deletion."
echo ""
if [[ "$ASSUME_YES" != "true" ]]; then
  read -r -p "Type 'yes' to publish: " REPLY_CONFIRM
  if [[ "$REPLY_CONFIRM" != "yes" ]]; then
    info "Cancelled — nothing was published."
    [[ "$CLEANUP_TEMP" == "true" ]] && rm -rf "$DEPLOY_DIR"
    exit 0
  fi
fi

# ─── Vercel CLI ───────────────────────────────────────────────────────────
if ! command -v npx &>/dev/null; then
  err "Node.js is required for the Vercel CLI but was not found."
  err "Install it from https://nodejs.org (or 'brew install node')."
  [[ "$CLEANUP_TEMP" == "true" ]] && rm -rf "$DEPLOY_DIR"
  exit 1
fi

if command -v vercel &>/dev/null; then
  VERCEL="vercel"
else
  VERCEL="npx --yes vercel"
fi

if ! $VERCEL whoami &>/dev/null; then
  echo ""
  warn "Not logged in to Vercel."
  echo "  1. Sign up (free): https://vercel.com/signup"
  echo "  2. Run: vercel login"
  echo "  3. Re-run this script."
  echo ""
  info "Attempting interactive login…"
  $VERCEL login || {
    err "Login failed. Run 'vercel login' manually, then retry."
    [[ "$CLEANUP_TEMP" == "true" ]] && rm -rf "$DEPLOY_DIR"
    exit 1
  }
fi
ok "Logged in as: $($VERCEL whoami 2>/dev/null || echo unknown)"

# ─── Project name (Vercel derives it from the directory name) ─────────────
if [[ "$CLEANUP_TEMP" == "true" ]]; then
  RAW_NAME=$(basename "$INPUT" .html)
else
  RAW_NAME=$(basename "$DEPLOY_DIR")
fi
DECK_NAME=$(echo "$RAW_NAME" | tr '[:upper:]' '[:lower:]' \
  | sed 's/[^a-z0-9._-]/-/g; s/--*/-/g; s/^-//; s/-$//' | cut -c1-100)
[[ -z "$DECK_NAME" ]] && DECK_NAME="deck"

if [[ "$CLEANUP_TEMP" == "true" ]]; then
  RENAMED="$(dirname "$DEPLOY_DIR")/$DECK_NAME"
  mv "$DEPLOY_DIR" "$RENAMED"
  DEPLOY_DIR="$RENAMED"
fi

# ─── Deploy ───────────────────────────────────────────────────────────────
echo ""
info "Deploying…"
OUTPUT=$($VERCEL deploy "$DEPLOY_DIR" --yes --prod 2>&1) || {
  err "Deployment failed:"
  echo "$OUTPUT"
  [[ "$CLEANUP_TEMP" == "true" ]] && rm -rf "$DEPLOY_DIR"
  exit 1
}
URL=$(echo "$OUTPUT" | grep -oE 'https://[^ ]+' | tail -1)

echo ""
ok "Published."
echo ""
echo -e "  ${BOLD}URL:${NC} $URL"
echo ""
echo "  Works on any device. To take it down, delete the project"
echo "  '$DECK_NAME' at https://vercel.com/dashboard"
echo ""

[[ "$CLEANUP_TEMP" == "true" ]] && rm -rf "$DEPLOY_DIR"
exit 0
