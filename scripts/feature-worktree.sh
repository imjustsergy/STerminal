#!/usr/bin/env bash
# Crea o limpia el worktree + rama de una feature, según docs/sys/workflow.md sección E.
# Uso:
#   scripts/feature-worktree.sh new <N> <slug>    # crea worktree ../<repo>-feature-N + rama feature-N-slug
#   scripts/feature-worktree.sh close <N> <slug>  # elimina el worktree y la rama local tras el merge
set -euo pipefail

usage() {
  echo "Uso: $0 new|close <N> <slug-corto>" >&2
  echo "  slug-corto: minusculas y guiones, ej. auth-login" >&2
  exit 1
}

[ $# -eq 3 ] || usage
action="$1"
num="$2"
slug="$3"

[[ "$num" =~ ^[0-9]+$ ]] || { echo "Error: <N> debe ser numérico, recibido '$num'" >&2; exit 1; }
[[ "$slug" =~ ^[a-z0-9]+(-[a-z0-9]+)*$ ]] || { echo "Error: <slug> debe ser minúsculas-con-guiones, recibido '$slug'" >&2; exit 1; }

repo_root="$(git rev-parse --show-toplevel)"
repo_name="$(basename "$repo_root")"
branch="feature-${num}-${slug}"
worktree_path="${repo_root}/../${repo_name}-feature-${num}"

case "$action" in
  new)
    cd "$repo_root"
    if git show-ref --verify --quiet "refs/heads/${branch}"; then
      echo "Error: la rama '${branch}' ya existe." >&2
      exit 1
    fi
    if [ -e "$worktree_path" ]; then
      echo "Error: ya existe algo en '${worktree_path}'." >&2
      exit 1
    fi
    git fetch origin main --quiet || true
    git worktree add -b "$branch" "$worktree_path" origin/main 2>/dev/null \
      || git worktree add -b "$branch" "$worktree_path" main
    echo ""
    echo "Worktree creado: ${worktree_path}"
    echo "Rama: ${branch}"
    echo ""
    echo "Siguiente paso:"
    echo "  cd ${worktree_path}"
    echo "  claude"
    ;;
  close)
    if [ ! -e "$worktree_path" ]; then
      echo "Aviso: no existe worktree en '${worktree_path}', nada que quitar." >&2
    else
      if [ -x "${repo_root}/scripts/preview-server.sh" ] && [ -f "${worktree_path}/.preview.json" ]; then
        ( cd "$worktree_path" && "${repo_root}/scripts/preview-server.sh" stop ) || true
      fi
      git -C "$repo_root" worktree remove "$worktree_path" --force
      echo "Worktree eliminado: ${worktree_path}"
    fi
    if git -C "$repo_root" show-ref --verify --quiet "refs/heads/${branch}"; then
      # Auditoría 2026-07-08 (docs/sys/audit-infra-agentes-2026-07-08.md, hallazgo 7):
      # borrar la rama local sin pushearla antes perdía el historial por completo en
      # bucles sin PR (donde GitHub nunca llega a ver la rama). Push best-effort antes
      # de borrar — si falla (sin red, sin remoto), se avisa pero no bloquea el close.
      if git -C "$repo_root" push origin "$branch" --quiet 2>/dev/null; then
        echo "Rama pusheada a origin: ${branch}"
      else
        echo "Aviso: no se pudo pushear '${branch}' a origin antes de borrarla — revisa manualmente si hace falta conservar su historial." >&2
      fi
      git -C "$repo_root" branch -D "$branch"
      echo "Rama local eliminada: ${branch}"
    else
      echo "Aviso: la rama local '${branch}' no existe (¿ya se borró?)." >&2
    fi
    ;;
  *)
    usage
    ;;
esac
