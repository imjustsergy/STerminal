<script lang="ts">
  import type { HelpResponse } from '../../lib/types';

  interface Props {
    response: HelpResponse;
  }

  const { response }: Props = $props();

  // feat-18: MOVERS está en el lenguaje de comandos (lo reconoce el parser) pero
  // fuera de alcance del MVP — ejecutarlo siempre da 400. Se distingue visualmente
  // aquí en vez de mostrarlo con el mismo estilo que un comando que sí funciona.
  const UNAVAILABLE_TYPES = new Set(['MOVERS']);
</script>

<div class="help-panel">
  <div class="title">REFERENCIA DE COMANDOS</div>
  <div class="subtitle dim">
    Sintaxis: <span class="acc">[SÍMBOLO] [FUNCIÓN]</span> · Enter ejecuta · ↑ ↓ historial
  </div>
  {#each response.commands as entry (entry.usage)}
    {@const unavailable = UNAVAILABLE_TYPES.has(entry.type)}
    <div class="row">
      <span class="usage" class:acc={!unavailable} class:dim={unavailable}>{entry.usage}</span>
      <span class="desc" class:dim={unavailable}>
        {entry.description}
        {#if unavailable}
          <span class="unavailable-badge dimmer">· no disponible todavía</span>
        {/if}
      </span>
    </div>
  {/each}
</div>

<style>
  .help-panel {
    padding: 20px 18px 60px;
    max-width: 820px;
  }
  .title {
    font-weight: 700;
    font-size: 15px;
    margin-bottom: 4px;
  }
  .subtitle {
    font-size: 12px;
    margin-bottom: 20px;
  }
  .acc {
    color: var(--acc);
  }
  .row {
    display: flex;
    gap: 16px;
    padding: 5px 0;
    font-size: 12px;
    border-bottom: 1px dashed var(--border);
  }
  .usage {
    font-weight: 700;
    width: 160px;
    flex: none;
  }
  .desc {
    flex: 1;
  }
  .unavailable-badge {
    font-size: 11px;
    font-style: italic;
  }
</style>
