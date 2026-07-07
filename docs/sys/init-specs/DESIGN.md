# sterminal — Documento de diseño

Terminal financiero personal, estilo Bloomberg Terminal. App web local y privada, un solo usuario, **todo por teclado**. Panel de mando para seguir mercados (acciones/ETFs, cripto, forex y materias primas) y la cartera real del usuario con P&L en vivo.

Archivo: `sterminal.dc.html` (Design Component único, autocontenido).

---

## 1. Principios de diseño

Ordenados por prioridad — así se resuelven los conflictos:

1. **Densidad > espacio en blanco.** Es un terminal, no una landing. Cabeceras compactas, tablas apretadas, sin cards redondeadas gigantes ni ilustraciones.
2. **Velocidad de lectura.** Números alineados a la derecha, `tabular-nums`, color por signo (verde +, rojo −), sparklines ASCII para tendencia de un vistazo.
3. **Teclado primero.** El ratón es opcional; todo se alcanza sin él. Barra de comando siempre enfocada, se re-enfoca al teclear en cualquier sitio.
4. **Legibilidad de datos financieros.** P&L, %, cotizaciones y asignación siempre claros.
5. **Ligereza (Raspberry Pi 5).** Sin animaciones pesadas, parallax, blur ni gradientes decorativos. Gráficos en `<canvas>` 2D simple; refresco por intervalos, no continuo.

**Anti-objetivos:** nada de estética SaaS/landing, sin modo claro por defecto (dark-first monoespaciado), sin menús hamburguesa/sidebars/navegación móvil, sin trading real, login ni multiusuario.

---

## 2. Sistema visual

### Tipografía
- **JetBrains Mono** (400/500/700) como única familia. Monoespaciada, `tabular-nums` para que las columnas de cifras cuadren.
- Jerarquía por tamaño y color, no por familia: 10–11px para etiquetas/cabeceras de tabla, 12–13px para datos, 22–30px para precios destacados.

### Color — 3 temas (tweakables)
Cada tema es un juego completo de tokens CSS (`--bg`, `--panel`, `--panel2`, `--border`, `--fg`, `--dim`, `--dimmer`, `--acc`, `--accdim`, `--pos`, `--neg`, `--warn`). Se inyectan como variables en el nodo raíz; todo el resto del estilo es literal con `var(--x)`, así el cambio de tema es instantáneo.

| Tema | Fondo | Texto | Acento | Uso |
|---|---|---|---|---|
| **cobalt** (por defecto) | negro azulado | gris azulado claro | azul cobalto `#3d7bff` | look moderno tipo TUI (k9s/lazygit) |
| **amber** | negro cálido | ámbar | ámbar `#ffa72e` | tributo directo a Bloomberg |
| **phosphor** | negro verdoso | verde menta | verde CRT `#33ff99` | retro fósforo / CRT |

En los tres, **positivo = verde, negativo = rojo, aviso/caché = ámbar** se mantienen por convención financiera.

### Señales de estado
- **En vivo:** `● EN VIVO` verde.
- **En caché / stale:** badge ámbar `⚠ EN CACHÉ · hace 22s` cuando una API va retrasada (forex y materias primas simulan lag). Contador en cabecera (`· N EN CACHÉ`).
- **Error:** mensaje rojo con sugerencias ("¿Quisiste decir?") para símbolo/función no reconocidos.

---

## 3. Modelo de interacción — barra de comando

Fija abajo (estilo Vim/TUI), siempre enfocada, ancho completo, con prompt `›`.

**Sintaxis:** `[SÍMBOLO] [FUNCIÓN]` o una función suelta.

| Entrada | Acción |
|---|---|
| `AAPL` | Resumen de activo |
| `AAPL GP` / `BTC GP` | Gráfico de precio |
| `AAPL NEWS` | Noticias del activo |
| `PORT` | Cartera |
| `PORT ADD` | Editar cartera / CSV |
| `WATCH` | Watchlist |
| `MOVERS` | Mayores movimientos |
| `EURUSD` | Forex (mismo resumen) |
| `HELP` | Referencia de comandos |
| `HOME` | Pantalla inicial |

**Teclado:**
- **Enter** ejecuta.
- **Tab** autocompleta la sugerencia resaltada.
- **↑ / ↓** navegan el dropdown de sugerencias si está abierto; si no, recorren el historial de comandos.
- **Esc** limpia el input; con el input vacío, vuelve a inicio.
- Autocompletado en vivo: dropdown con símbolos + funciones + comandos, cada uno con descripción; el resaltado se estiliza con el acento.
- **Estados de fallo:** función no reconocida y símbolo no encontrado muestran el panel de error con sugerencias más cercanas.

---

## 4. Paneles

Todos comparten cabecera compacta + contenido denso.

- **Resumen de activo** — cabecera con símbolo, clase (ACCIÓN/CRIPTO/FOREX…), precio grande coloreado y cambio. Rejilla de stats a la izquierda (apertura, cierre ant., máx/mín día, rango 52s, volumen, vol. medio, cap. mercado) + mini-gráfico de línea 3M a la derecha. Badge de caché si aplica.
- **Gráfico de precio** — `<canvas>` con velas o línea (toggle), selector de rango `1D · 5D · 1M · 3M · 1Y`, línea punteada de último precio con etiqueta, rejilla y ejes. Ligero, redibuja en cada tick/cambio.
- **Cartera (PORT)** — tabla: símbolo, cantidad, coste medio, precio, valor, P&L, P&L %, P&L día, % asignación. Totales (valor, P&L total, P&L día) en la cabecera. Todo coloreado por signo.
- **Watchlist (WATCH)** — símbolo, nombre, último, cambio, %, sparkline de tendencia, estado (EN VIVO / CACHÉ + antigüedad). Refresco automático.
- **Noticias (NEWS)** — titulares por activo con hora, etiqueta de categoría coloreada y fuente. Banner ámbar si el feed va retrasado.
- **Movers (MOVERS)** — dos columnas: ▲ Subidas / ▼ Bajadas, con precio, sparkline y % del día.
- **Ayuda (HELP)** — referencia de comandos agrupada (Activos, Cartera, Mercado, General) con ejemplos.
- **Formulario de cartera (PORT ADD)** — tabla editable de posiciones (añadir/eliminar filas) + área CSV con importar/exportar/guardar.

---

## 5. Layout — 2 modos (tweakable)

- **focus** (por defecto) — un panel a pantalla completa por comando. Más simple, máxima densidad por panel.
- **grid** — dashboard multipanel simultáneo (Watchlist · Movers · Cartera · Gráfico SPY) como pantalla de inicio, al estilo Bloomberg / htop. Los comandos siguen abriendo el panel enfocado; `HOME`/`Esc` vuelve al dashboard.

Extra: **scanlines** (tweakable) añade una textura CRT de líneas de barrido, opcional, para el toque fósforo.

---

## 6. Comportamiento en vivo y estados

- **Refresco:** watchlist y cartera tickean solos (~cada intervalo; en producción sería WebSocket ~15 s). El resto se carga bajo demanda al ejecutar un comando.
- **Estados diseñados explícitamente:** live · cargando (placeholders durante el stream) · **stale/caché** (aviso discreto ámbar cuando una API gratuita se retrasa o hay rate-limit) · error.
- Reloj y precios se actualizan sin recargar la vista.

---

## 7. Restricciones técnicas que moldearon el diseño

- **Raspberry Pi 5:** canvas 2D básico, sin sombras/blur/gradientes costosos, redibujo puntual (no requestAnimationFrame continuo).
- **APIs gratuitas (Yahoo Finance, CoinGecko):** se asumen retrasos y huecos → estados de carga, error y stale de primera clase.
- **Cartera por entrada manual/CSV:** formulario simple + import/export CSV, sin conexión a brokers.

**Fuera de alcance (no diseñado):** trading real, brokers, alertas push, multiusuario, autenticación.

---

## 8. Tweaks (parámetros del componente)

| Prop | Valores | Por defecto |
|---|---|---|
| `theme` | `cobalt` · `amber` · `phosphor` | `cobalt` |
| `layout` | `focus` · `grid` | `focus` |
| `scanlines` | on / off | off |

> Los datos de mercado son ficticios pero realistas (random-walk sembrado por símbolo, cambio diario determinista) para efectos de diseño; la capa de datos real se conectaría a las APIs gratuitas manteniendo los mismos estados live/stale/error.
