# plan-19 — Añadir posiciones a la cartera (comando PORT ADD)

**Feature:** feat-19 — Añadir posiciones a la cartera (comando `PORT ADD`)
**Estado:** aprobado (auto-aprobado, delegación explícita del owner — bucle post-MVP,
merge directo a `main` sin PR para este bucle)

## Desglose de tareas

1. `commands.py`: `CommandType.PORTFOLIO_ADD`; `Command` extendido con `quantity:
   float | None = None`, `cost_price: float | None = None`; nuevo
   `InvalidPortAddArgsError(CommandParseError)`; caso especial en `parse_command`
   detectado antes del despacho por número de tokens (`tokens[0].upper() == "PORT"
   and tokens[1].upper() == "ADD"` cuando hay ≥2 tokens), exige exactamente 5 tokens
   y valida símbolo/cantidad/precio.
2. `command_router.py`: `_dispatch_portfolio_add(command, portfolio_engine,
   registry)` — resuelve `asset_class` vía `registry.resolve`, llama
   `portfolio_engine.add_position(...)` con `opened_at` = hoy (UTC), devuelve el
   mismo payload que `_dispatch_portfolio`. Entrada en `_dispatch()` y en
   `_COMMAND_DESCRIPTIONS`.
3. Frontend: `PortfolioPanel.svelte` — footer actualizado (ya no dice "no
   disponible"), ejemplo en `PanelRouter.svelte` welcome panel si aplica.
4. Tests: `test_commands.py` (parsing válido, cada tipo de error), `test_command_router.py`
   (`FakePortfolioEngine.add_position`, caso feliz + errores propagados), frontend
   (`PortfolioPanel.test.ts` actualizado al nuevo texto del footer).
5. Verificación en vivo: `PORT ADD AAPL 10 150.50` y `PORT ADD BTC 0.5 60000` contra
   el backend real (SQLite real, no mock) antes de mergear — confirmar que la
   posición persiste y aparece en `PORT` después.

## Dependencias

Ninguna nueva feature — construye enteramente sobre feat-6 (`PortfolioEngine.add_position`,
ya existente y probado), feat-4 (parser), feat-5 (`command_router`). Sin nuevas
dependencias de terceros.

## Criterios de aceptación

Igual que `docs/sys/features/feat-19-port-add.md`.
