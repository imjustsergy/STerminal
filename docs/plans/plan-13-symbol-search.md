# plan-13 — Búsqueda de símbolos con autocompletado

**Feature:** feat-13 — Búsqueda de símbolos con autocompletado
**Estado:** aprobado (auto-aprobado, delegación explícita del owner — bucle post-MVP)

## Desglose de tareas

1. `search_router.py` (o añadido a `command_router.py`, a decidir en implementación —
   probablemente router propio ya que no es un `CommandType`): `GET /search?q=...`,
   llama a `registry.search(q)`, limita a 8 resultados, query vacía → `[]` sin llamar
   al registry.
2. `main.py`: incluir el nuevo router.
3. Frontend: `lib/api.ts::searchSymbols(query)`.
4. `CommandBar.svelte`: estado de dropdown, debounce, fetch, navegación por teclado
   (↑/↓ redirigidas al dropdown cuando está abierto, Enter selecciona sin ejecutar,
   Escape cierra). Componente de lista de sugerencias (puede vivir en el mismo fichero
   o extraerse a `SymbolSuggestions.svelte` — a decidir en implementación según
   legibilidad).
5. Tests: backend (`test_search_router.py` o casos en `test_command_router.py`),
   frontend (`CommandBar.test.ts` con `fetch` mockeado + `vi.useFakeTimers()`).

## Dependencias

Ninguna nueva feature — construye sobre feat-3 (`Registry.search`), feat-8 (frontend
skeleton, `CommandBar.svelte`).

## Criterios de aceptación

Igual que `docs/sys/features/feat-13-symbol-search.md`.
