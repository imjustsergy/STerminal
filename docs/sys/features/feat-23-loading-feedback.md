# feat-23 — Estado de carga durante la ejecución de comandos

**Estado:** feat-23

> Decimotercera iteración del bucle post-MVP, cuarta de la fase "features
> interesantes + mejora continua de UX". Continúa la queja general del owner
> sobre pulido visual — feat-22 resolvió el panel `SUMMARY` en concreto; esta
> feature ataca un hueco que afecta a **todos** los comandos, no solo uno.

## Problema / motivación

Al escribir cualquier comando y pulsar Enter, no hay ninguna señal visual de que
la petición está en curso — el panel anterior se queda estático hasta que
`postCommand` resuelve (éxito o error), sin transición ni indicador. Si el
backend tarda (red lenta, proveedor externo lento, Alpha Vantage con
rate-limit) el owner no tiene forma de saber si el comando se está procesando o
si la app se ha quedado colgada. Es un hueco de pulido que afecta a la
experiencia completa de la app, no a un panel concreto — coherente con la queja
general del owner ("la UX... un poco más").

## Alcance (qué incluye, qué no)

**Incluye:**
- **`App.svelte`**: estado `loading` que se activa al enviar cualquier comando
  (`runCommand`) y se desactiva al resolver (éxito o error). El panel anterior
  permanece visible mientras tanto — sin parpadeo a blanco.
- **Barra superior de progreso**: barra fina animada bajo el header, visible
  solo mientras `loading` es `true` — patrón ya familiar (GitHub, YouTube), no
  hace falta reinventar nada.
- **`CommandBar.svelte`**: reutiliza su prop `hint` (ya existía en el
  componente, sin ningún consumidor hasta ahora) para mostrar `"cargando…"`
  junto a la barra de comando mientras la petición está en curso.

**No incluye (fuera de alcance de esta feature):**
- Loading states específicos por panel (esqueletos de contenido, spinners
  dentro de cada panel) — la barra de progreso global cubre el caso general sin
  tener que tocar los ~10 paneles existentes uno a uno.
- Cancelar una petición en curso al escribir un comando nuevo — la petición
  anterior simplemente se ignora cuando llega tarde (mismo criterio de
  "descarta respuestas obsoletas" que ya usa el autocompletado de
  `CommandBar`, feat-13); cancelación real de la petición HTTP queda fuera de
  alcance.

## Criterios de aceptación

- Al enviar un comando, la barra de progreso aparece de inmediato y desaparece
  al llegar la respuesta (éxito o error).
- El hint `"cargando…"` aparece junto a la barra de comando durante la espera.
- El panel anterior no desaparece ni parpadea a blanco durante la carga.
- Verificable con datos reales: un comando que tarde visiblemente (ej. un
  proveedor con latencia real) muestra la barra de progreso durante todo ese
  tiempo, no solo un instante.
