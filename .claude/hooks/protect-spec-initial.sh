#!/usr/bin/env bash
# PreToolUse hook (Edit|Write|NotebookEdit|MultiEdit) — bloquea cualquier escritura
# sobre docs/sys/spec-initial.md. Ver docs/sys/workflow.md sección F.3.
set -euo pipefail

input="$(cat)"
file_path="$(printf '%s' "$input" | jq -r '.tool_input.file_path // empty')"

if [ -z "$file_path" ]; then
  exit 0
fi

if [[ "$file_path" == *"docs/sys/spec-initial.md" ]]; then
  echo "Bloqueado: docs/sys/spec-initial.md está congelado y no se puede editar (ver docs/sys/workflow.md sección C/F.1). Si necesitas reflejar un cambio de estado del proyecto, edita docs/sys/spec.md en su lugar." >&2
  exit 2
fi

exit 0
