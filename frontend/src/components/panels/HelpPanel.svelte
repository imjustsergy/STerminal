<script lang="ts">
  import type { HelpResponse } from '../../lib/types';

  interface Props {
    response: HelpResponse;
  }

  const { response }: Props = $props();
</script>

<div class="help-panel">
  <div class="title">REFERENCIA DE COMANDOS</div>
  <div class="subtitle dim">
    Sintaxis: <span class="acc">[SÍMBOLO] [FUNCIÓN]</span> · Enter ejecuta · ↑ ↓ historial
  </div>
  {#each response.commands as entry (entry.usage)}
    <div class="row">
      <span class="usage acc">{entry.usage}</span>
      <span class="desc">{entry.description}</span>
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
</style>
