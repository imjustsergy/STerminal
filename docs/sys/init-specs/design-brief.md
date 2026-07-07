# Brief de diseño — sterminal

> Documento para pasar a Claude (design) y generar el diseño visual/UX del terminal.
> Complementa la spec principal en [`../spec.md`](../spec.md).

**Qué es:** Un terminal financiero personal, estilo **Bloomberg Terminal**, como app web
local y privada (corre en la máquina del usuario, sin cuentas ni login). Un solo usuario.

**Propósito:** Panel de mando para seguir mercados y su cartera real de inversión en un
solo sitio, todo por teclado.

**Cobertura multi-activo:** acciones/ETFs, cripto y forex/materias primas, más la
**cartera real** del usuario con P&L en vivo.

## Modelo de interacción (clave del diseño)

- **Barra de comando siempre presente y enfocada**, estilo Bloomberg: el usuario escribe
  `[SÍMBOLO] [FUNCIÓN]` o una función.
- Teclado ante todo, cero dependencia del ratón. Historial con ↑/↓ y autocompletado.
- Ejemplos de comandos: `AAPL` (resumen), `BTC GP` (gráfico), `AAPL NEWS` (noticias),
  `PORT` (cartera), `WATCH` (watchlist), `EURUSD` (forex), `MOVERS` (mayores movimientos),
  `HELP`.

## Pantallas / paneles a diseñar

1. **Resumen de activo** — precio actual, cambio %, gráfico, stats clave, cabecera densa.
2. **Gráfico de precio** — velas/línea, selector de rango temporal (estilo TradingView
   lightweight-charts).
3. **Cartera (`PORT`)** — tabla de posiciones: símbolo, cantidad, coste medio, precio
   actual, P&L, P&L diario, % asignación.
4. **Watchlist (`WATCH`)** — lista en vivo con precio y cambio por símbolo, actualización
   automática.
5. **Noticias (`NEWS`)** — titulares por activo.
6. **Movers (`MOVERS`)** — mayores subidas/bajadas del día.
7. **Ayuda (`HELP`)** — referencia de comandos.

## Estética objetivo

- Fondo negro, tipografía **monoespaciada**, acentos **ámbar/verde** (tributo Bloomberg).
- Alta densidad de información, cabeceras compactas, layout de **rejilla de paneles**.
- Números coloreados por signo: **verde** positivo / **rojo** negativo.
- Estados visuales: dato en vivo vs. **dato "stale"** (cacheado, con aviso discreto)
  cuando una API falla o hay rate-limit.

## Comportamiento en vivo

Watchlist y cartera se refrescan solos (WebSocket, ~15 s). El resto se carga bajo demanda
al ejecutar un comando.

## Restricciones técnicas que afectan al diseño

- Debe verse bien y fluido en una **Raspberry Pi 5** (ligero, sin animaciones pesadas).
- Datos de **APIs gratuitas** (Yahoo Finance, CoinGecko) → asumir posibles retrasos/huecos:
  diseñar estados de carga, error y "stale".
- Cartera por **entrada manual/CSV** → hace falta una vista/formulario simple para
  añadir/editar posiciones e importar/exportar CSV.

## Fuera de alcance (no diseñar)

Trading real, conexión a brokers, alertas push, multiusuario, autenticación.

---

## Referencias visuales

- **Bloomberg Terminal** (referencia madre): fondo negro, texto ámbar, densidad extrema, multipanel.
- **TradingView** — para los gráficos y el selector de rango temporal.
- **TUIs modernas**: `lazygit`, `k9s`, `htop` — aire "todo por teclado, rejilla de paneles".
- Estética **CRT/phosphor** opcional (verde/ámbar sobre negro) para el toque retro.
- Tipografías sugeridas: **JetBrains Mono**, **IBM Plex Mono** o **Berkeley Mono**.
- Si hay screenshots o moodboard, adjuntarlos (valen más que la descripción).

## Comandos concretos (diseñar la barra y sus estados)

- Formato: `[SÍMBOLO] [FUNCIÓN]` → `AAPL`, `BTC GP`, `AAPL NEWS`, `PORT`, `WATCH`,
  `EURUSD`, `MOVERS`, `HELP`.
- Diseñar también: **autocompletado** en vivo, **dropdown de sugerencias**, **historial**
  (↑/↓) y el estado de **comando no reconocido / símbolo no encontrado** con sugerencias.
- Ubicación de la barra: fija (estilo Vim abajo o cabecera arriba) — proponer.

## Prioridades (resolver conflictos de diseño en este orden)

1. **Densidad de información** por encima del espacio en blanco (es un terminal, no una landing).
2. **Velocidad de lectura**: números alineados, color por signo, escaneo rápido.
3. **Teclado primero**: el ratón es opcional; todo alcanzable sin él.
4. **Legibilidad de datos financieros**: P&L, %, cotizaciones claros de un vistazo.
5. **Ligereza** (Raspberry Pi): sin animaciones pesadas ni sombras/blur costosos.

## Cosas a evitar

- Nada de estética **SaaS/landing** (mucho aire, cards redondeadas gigantes, ilustraciones).
- Sin **modo claro** por defecto (dark-first, monoespaciado).
- Sin **animaciones/transiciones** llamativas, parallax ni gradientes decorativos.
- Sin **menús hamburguesa, sidebars de iconos ni navegación tipo móvil**.
- Sin elementos que impliquen **trading real, login o multiusuario** (fuera de alcance).
- No sacrificar densidad por "que se vea limpio y espaciado".

> **Regla de oro:** priorizar densidad y teclado sobre estética limpia. Ante la duda,
> más Bloomberg y menos app SaaS.
