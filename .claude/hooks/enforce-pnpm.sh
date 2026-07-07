#!/usr/bin/env bash
# PreToolUse hook (Bash) — bloquea comandos que usan npm en vez de pnpm.
# Ver docs/sys/workflow.md sección F.3 / A (Python-first, pnpm obligatorio).
set -euo pipefail

input="$(cat)"
command="$(printf '%s' "$input" | jq -r '.tool_input.command // empty')"

if [ -z "$command" ]; then
  exit 0
fi

# Exige que "npm" sea el propio comando invocado (inicio de línea o tras ; & | y
# separado por espacio), para no bloquear falsos positivos como "pnpm" o "npm-cache".
if printf '%s' "$command" | grep -Eq '(^|[;&|]|[[:space:]])npm([[:space:]]|$)'; then
  echo "Bloqueado: este proyecto usa pnpm, no npm (ver docs/sys/workflow.md sección A/F.4). Reescribe el comando con pnpm, ej. 'pnpm install' en vez de 'npm install'." >&2
  exit 2
fi

exit 0
