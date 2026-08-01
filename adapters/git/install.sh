#!/bin/sh
# nullius :: install the pre-commit gate, and PROVE it fires.
#
# Written because the obvious instruction is wrong on a lot of machines:
#
#     ln -s ~/.nullius/adapters/git/pre-commit .git/hooks/pre-commit
#
# If `core.hooksPath` is set — husky, lefthook, the pre-commit framework, or a
# dotfiles repo all set it — git never looks in `.git/hooks/` and that symlink
# does nothing. It fails silently, and it fails PERMISSIVELY: every commit sails
# through and the repo looks gated. That is the worst available failure for a
# tool whose entire job is to refuse.
#
# So this script resolves the real hook directory, chains any existing
# pre-commit instead of clobbering it, and then runs a canary commit in a
# throwaway repo to confirm the gate actually blocks. If the canary passes when
# it should have failed, the install is reported as FAILED.
#
# Usage:  sh install.sh [--global | --repo PATH]

set -e
SELF=$(cd "$(dirname "$0")" && pwd)
GATES_DIR=$(cd "$SELF/../.." && pwd)

MODE=${1:---repo}
TARGET=${2:-.}

# Must return an ABSOLUTE path. `git rev-parse --git-dir` answers `.git`
# when run from the repo root, and the canary below then points a different
# repo at a relative `.git/hooks` — which resolves to the canary's own empty
# hooks directory, the canary passes, and the install reports FAILED on a
# perfectly good hook. Caught by the canary; fixed by absolutising here.
resolve_hookdir() {
    hp=$(git -C "$1" config --get core.hooksPath 2>/dev/null || true)
    if [ -n "$hp" ]; then
        case "$hp" in
            /*) echo "$hp" ;;
            ~*) eval echo "$hp" ;;
            *)  echo "$(git -C "$1" rev-parse --show-toplevel)/$hp" ;;
        esac
    else
        git -C "$1" rev-parse --absolute-git-dir 2>/dev/null |
            sed 's|$|/hooks|' ||
            echo "$(git -C "$1" rev-parse --show-toplevel)/.git/hooks"
    fi
}

if [ "$MODE" = "--global" ]; then
    HOOKDIR=$(git config --global --get core.hooksPath || true)
    if [ -z "$HOOKDIR" ]; then
        HOOKDIR="$HOME/.git-hooks"
        mkdir -p "$HOOKDIR"
        git config --global core.hooksPath "$HOOKDIR"
        echo "set global core.hooksPath -> $HOOKDIR"
    fi
else
    HOOKDIR=$(resolve_hookdir "$TARGET")
fi
HOOKDIR=$(eval echo "$HOOKDIR")
mkdir -p "$HOOKDIR"
HOOK="$HOOKDIR/pre-commit"

echo "hook directory : $HOOKDIR"
[ -n "$(git config --get core.hooksPath 2>/dev/null || true)" ] &&
    echo "               (core.hooksPath is set — .git/hooks/ would have been ignored)"

if [ -e "$HOOK" ] && ! grep -q "nullius" "$HOOK" 2>/dev/null; then
    mv "$HOOK" "$HOOK.pre-nullius"
    echo "existing hook  : chained as $HOOK.pre-nullius"
    CHAIN="\"\$(dirname \"\$0\")/pre-commit.pre-nullius\" \"\$@\" || exit \$?"
else
    CHAIN=":"
fi

cat > "$HOOK" <<EOF
#!/bin/sh
# nullius (installed by adapters/git/install.sh)
$CHAIN
NULLIUS_DIR="$GATES_DIR" exec "$SELF/pre-commit" "\$@"
EOF
chmod +x "$HOOK"
echo "installed      : $HOOK"

# ---- canary: prove it blocks, in a throwaway repo -------------------------
CANARY=$(mktemp -d)
trap 'rm -rf "$CANARY"' EXIT
cd "$CANARY"
git init -q
git config user.email canary@local
git config user.name canary
[ "$MODE" = "--global" ] || git config core.hooksPath "$HOOKDIR"
touch .nullius.toml
printf '# canary\n\n| Someone 1999 | depth: full |\n' > canary.md
git add -A
if git commit -qm canary >/dev/null 2>&1; then
    echo
    echo "INSTALL FAILED — the canary commit was ALLOWED."
    echo "  An unbacked 'depth: full' claim should have been refused."
    echo "  The hook is present but not running. Check core.hooksPath and that"
    echo "  python3 is on the PATH git gives its hooks."
    exit 1
fi
echo "canary         : commit correctly REFUSED"
echo
echo "nullius installed and verified."
