# CI/CD & deploy pipeline — sterminal

> **Pendiente de implementar.** Este documento describe el pipeline objetivo, a crear en
> la primera feature que añada código (backend). No hay todavía `.github/workflows/` ni
> script de deploy en el repo — se generan cuando haya algo real que testear/desplegar,
> siguiendo esta especificación.

## Contexto

sterminal es una app self-hosted, de un solo usuario, corriendo en una Raspberry Pi 5
propia. No hay hosting de terceros para el backend: **zero open ports**, sin conexiones
entrantes expuestas. El despliegue se hace por *polling* saliente desde la propia Pi.

Si en el futuro se sirve el frontend por separado (p. ej. Cloudflare Pages), ese tramo
sí puede ser un deploy push-triggered normal; hoy el plan es servir todo desde la Pi.

## Pipeline objetivo

### 1. Push a `main` → GitHub Actions

Disparado automáticamente en cada push a `main` (nunca en otras ramas — esas se validan
vía PR checks, no deploy).

| Paso | Herramienta | Bloquea merge si falla |
|---|---|---|
| Lint | `ruff` (Python) | Sí |
| Test | `pytest` (unit + integración con fixtures, sin red real) | Sí |
| Build (si aplica frontend) | `pnpm build` | Sí |

### 2. Raspberry Pi — polling + deploy

```
cron (cada N min) → git ls-remote origin main
                  → ¿hay commit nuevo?
                        sí → git pull
                           → docker compose up -d --build
                        no → nada
```

- Sin puertos entrantes: la Pi inicia la conexión (saliente) hacia GitHub, nunca al revés.
- Ningún agente AI ejecuta este paso directamente — lo hace el cron de la propia Pi tras
  el merge, nunca un `claude`/`codex` en un worktree.
- `docker compose up -d --build` reconstruye y reinicia los servicios solo si hay
  cambios.

## Reglas generales

- `main` es la única rama que dispara el pipeline y el eventual deploy.
- Ningún deploy ocurre sin CI en verde.
- Los agentes AI nunca ejecutan `docker compose up`, `wrangler pages deploy` ni
  comandos equivalentes directamente — bloqueado por el hook
  `guard-main-and-deploy.sh` (ver [`workflow.md`](workflow.md), sección F.3).

## Tareas pendientes al implementar

- [ ] Crear `.github/workflows/ci.yml` (lint + test, disparado en push/PR)
- [ ] Definir estructura de `docker-compose.yml` para el backend
- [ ] Script de polling+deploy en la Pi (cron + script de pull/build)
- [ ] Decidir si el frontend se sirve desde la Pi o se separa a Cloudflare Pages
