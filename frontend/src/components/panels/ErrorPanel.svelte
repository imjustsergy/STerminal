<script lang="ts">
  interface Props {
    message: string;
    suggestions?: string[];
  }

  const { message, suggestions = [] }: Props = $props();
</script>

<div class="error-panel">
  <div class="msg">&#10005; {message}</div>
  {#if suggestions.length > 0}
    <div class="sug-label dim">¿Quisiste decir?</div>
    <div class="sug-list">
      {#each suggestions as s (s)}
        <div class="sug-item">{s}</div>
      {/each}
    </div>
  {/if}
  <div class="footer dimmer">Escribe HELP para ver todos los comandos.</div>
</div>

<style>
  .error-panel {
    padding: 44px 32px;
    max-width: 640px;
    margin: 0 auto;
  }
  .msg {
    color: var(--neg);
    font-size: 15px;
    font-weight: 500;
  }
  .sug-label {
    margin-top: 12px;
    font-size: 12px;
  }
  .sug-list {
    margin-top: 10px;
    display: flex;
    flex-direction: column;
    gap: 2px;
  }
  .sug-item {
    padding: 5px 0;
    font-size: 12px;
    color: var(--acc);
    font-weight: 700;
  }
  .footer {
    font-size: 11px;
    margin-top: 20px;
  }
</style>
