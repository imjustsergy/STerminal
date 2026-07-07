#!/usr/bin/env bash
# Levanta/para un servidor de prueba (0.0.0.0 + puerto libre) de la feature en cuyo
# worktree se ejecuta este script — para que el owner pruebe antes de mergear el PR.
# Ver docs/sys/workflow.md sección F.5 / J.7.
#
# Uso (siempre desde la RAÍZ del worktree de la feature):
#   scripts/preview-server.sh start
#   scripts/preview-server.sh stop
set -euo pipefail

usage() {
  echo "Uso: $0 start|stop  (ejecutar desde la raíz del worktree de la feature)" >&2
  exit 1
}

[ $# -eq 1 ] || usage
action="$1"
state_file=".preview.json"

free_port() {
  python3 -c 'import socket; s=socket.socket(); s.bind(("0.0.0.0",0)); print(s.getsockname()[1]); s.close()'
}

lan_ip() {
  hostname -I 2>/dev/null | awk '{print $1}' || echo "0.0.0.0"
}

case "$action" in
  start)
    if [ -f "$state_file" ]; then
      echo "Ya hay un preview server corriendo (borra $state_file si está huérfano, o haz 'stop' primero)." >&2
      exit 1
    fi
    ip="$(lan_ip)"
    entries="{}"
    started_any=0
    backend_url=""

    if [ -f backend/pyproject.toml ]; then
      [ -d backend/.venv ] || python3 -m venv backend/.venv
      backend/.venv/bin/pip install -q -e "backend[dev]"
      port="$(free_port)"
      mkdir -p .preview-logs
      setsid nohup backend/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port "$port" --app-dir backend \
        > .preview-logs/backend.log 2>&1 < /dev/null &
      pgid=$!
      disown
      entries="$(printf '%s' "$entries" | jq --arg port "$port" --arg pgid "$pgid" '.backend = {port: ($port|tonumber), pgid: ($pgid|tonumber)}')"
      backend_url="http://${ip}:${port}"
      echo "Backend: ${backend_url}  (health: ${backend_url}/health)"
      started_any=1
    fi

    if [ -f frontend/package.json ]; then
      command -v pnpm >/dev/null || { echo "Aviso: frontend/package.json existe pero pnpm no está instalado, salto el frontend." >&2; }
      if command -v pnpm >/dev/null; then
        (cd frontend && pnpm install --silent)
        port="$(free_port)"
        mkdir -p .preview-logs
        # "pnpm --dir frontend dev -- --host ... --port ..." reenvía un "--" extra al
        # script "vite" subyacente (pnpm antepone su propio separador), que vite no
        # parsea y acaba arrancando en el host/puerto por defecto — invocar el binario
        # de vite directamente vía "pnpm exec" evita el "--" duplicado.
        # VITE_API_BASE_URL: el backend usa un puerto libre distinto cada vez, así que
        # el default estático del .env (localhost:8000) no sirve para este preview —
        # se lo pasamos por entorno, que Vite prioriza sobre el .env.
        VITE_API_BASE_URL="${backend_url}" setsid nohup pnpm --dir frontend exec vite --host 0.0.0.0 --port "$port" \
          > .preview-logs/frontend.log 2>&1 < /dev/null &
        pgid=$!
        disown
        entries="$(printf '%s' "$entries" | jq --arg port "$port" --arg pgid "$pgid" '.frontend = {port: ($port|tonumber), pgid: ($pgid|tonumber)}')"
        echo "Frontend: http://${ip}:${port}"
        started_any=1
      fi
    fi

    if [ "$started_any" -eq 0 ]; then
      echo "No se ha encontrado ni backend/pyproject.toml ni frontend/package.json — nada que arrancar." >&2
      exit 1
    fi

    printf '%s' "$entries" > "$state_file"
    echo "Logs en .preview-logs/. Para pararlo: scripts/preview-server.sh stop"
    ;;
  stop)
    if [ ! -f "$state_file" ]; then
      echo "No hay preview server registrado en este worktree ($state_file no existe)." >&2
      exit 0
    fi
    for key in backend frontend; do
      pgid="$(jq -r --arg k "$key" '.[$k].pgid // empty' "$state_file")"
      if [ -n "$pgid" ]; then
        kill -TERM "-$pgid" 2>/dev/null || true
        sleep 1
        kill -KILL "-$pgid" 2>/dev/null || true
        echo "Parado: $key (pgid $pgid)"
      fi
    done
    rm -f "$state_file"
    ;;
  *)
    usage
    ;;
esac
