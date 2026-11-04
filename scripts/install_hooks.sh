#!/usr/bin/env bash
# Instala os hooks de governanca do AIHawk em .git/hooks/
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
HOOKS_SRC="${REPO_ROOT}/scripts/hooks"
HOOKS_DEST="${REPO_ROOT}/.git/hooks"

if [ ! -d "${HOOKS_DEST}" ]; then
    echo "Erro: Diretorio .git/hooks nao encontrado em ${HOOKS_DEST}" >&2
    exit 1
fi

echo "Instalando hooks de governanca em ${HOOKS_DEST}..."
cp -f "${HOOKS_SRC}/ler_topo.py" "${HOOKS_DEST}/ler_topo.py"
cp -f "${HOOKS_SRC}/commit-msg" "${HOOKS_DEST}/commit-msg"
cp -f "${HOOKS_SRC}/pre-commit" "${HOOKS_DEST}/pre-commit"
cp -f "${HOOKS_SRC}/pre-push" "${HOOKS_DEST}/pre-push"

chmod +x "${HOOKS_DEST}/commit-msg" "${HOOKS_DEST}/pre-commit" "${HOOKS_DEST}/pre-push" "${HOOKS_DEST}/ler_topo.py"
chmod +x "${HOOKS_SRC}/commit-msg" "${HOOKS_SRC}/pre-commit" "${HOOKS_SRC}/pre-push" "${HOOKS_SRC}/ler_topo.py"

echo "Hooks instalados com sucesso:"
ls -la "${HOOKS_DEST}/commit-msg" "${HOOKS_DEST}/pre-commit" "${HOOKS_DEST}/pre-push" "${HOOKS_DEST}/ler_topo.py"
