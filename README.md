# sterminal

Terminal financiero personal, estilo Bloomberg. App web local y privada que corre en tu
propia máquina/Raspberry Pi — sin cuentas, sin telemetría, un solo usuario.

- Multi-activo: acciones/ETFs, cripto, forex/materias primas, bajo la misma interfaz.
- Navegación por teclado con barra de comando (`AAPL`, `BTC GP`, `PORT`, `WATCH`, `HELP`...).
- Cartera real por entrada manual o import CSV, con P&L en vivo.
- Ligero por diseño: pensado para volar en una Raspberry Pi 5.

## Estado del proyecto

Diseño aprobado, en fase de planificación del MVP. Ver
[`docs/sys/spec.md`](docs/sys/spec.md) para la spec viva y
[`docs/sys/init-specs/DESIGN.md`](docs/sys/init-specs/DESIGN.md) para el diseño visual/UX.

## Stack

Python + FastAPI (backend/engine) · Svelte + TradingView `lightweight-charts` (frontend)
· SQLite (persistencia) · Raspberry Pi 5 self-hosted (zero open ports).

## Desarrollo

Este proyecto sigue un workflow spec-first con agentes AI en Git worktrees aislados.
Ver [`docs/sys/workflow.md`](docs/sys/workflow.md) para el proceso completo y
[`CLAUDE.md`](CLAUDE.md) para las reglas operativas de los agentes.
