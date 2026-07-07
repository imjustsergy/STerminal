#!/usr/bin/env bash
# PreToolUse hook (Bash) — bloquea push/merge directos a main y comandos de deploy
# ejecutados directamente por el agente. Ver docs/sys/workflow.md sección E.4/F.3/G.
set -euo pipefail

input="$(cat)"
command="$(printf '%s' "$input" | jq -r '.tool_input.command // empty')"

if [ -z "$command" ]; then
  exit 0
fi

deny() {
  echo "Bloqueado: $1 (ver docs/sys/workflow.md secciones E.4/F.1/G — los agentes no mergean ni despliegan directamente)." >&2
  exit 2
}

# git push ... main  (push directo a main, saltándose el PR)
if printf '%s' "$command" | grep -Eq '^[[:space:]]*git[[:space:]]+push([[:space:]]|.)*[[:space:]:](main)([[:space:]]|$)'; then
  deny "git push directo a la rama main. Abre un PR desde la rama de la feature (/feature:pr) y deja que el owner mergee."
fi

# git merge mientras se está en main (mergear algo directamente en main sin PR)
if printf '%s' "$command" | grep -Eq '^[[:space:]]*git[[:space:]]+merge([[:space:]]|$)'; then
  current_branch="$(git branch --show-current 2>/dev/null || true)"
  if [ "$current_branch" = "main" ]; then
    deny "git merge directo estando en main. Usa un PR (/feature:pr) en vez de mergear localmente."
  fi
fi

# comandos de deploy directo
if printf '%s' "$command" | grep -Eq '(docker[[:space:]]+compose[[:space:]]+up|docker-compose[[:space:]]+up|wrangler[[:space:]]+(pages[[:space:]]+)?deploy)'; then
  deny "comando de deploy directo. El deploy lo dispara el pipeline de CI/CD tras el merge a main, nunca el agente (ver docs/sys/ci-cd.md)."
fi

exit 0
