<script lang="ts">
  import CommandBar from './components/CommandBar.svelte';
  import PanelRouter from './components/PanelRouter.svelte';
  import { CommandApiError, postCommand } from './lib/api';
  import type { Range } from './lib/chartData';
  import { panelForResponse, type PanelKind } from './lib/dispatch';
  import type { CommandResponse } from './lib/types';

  let kind: PanelKind | 'welcome' | 'watch' | 'error' = $state('welcome');
  let response: CommandResponse | null = $state(null);
  let errorMessage = $state('');
  let errorSuggestions: string[] = $state([]);
  let activeRange: Range = $state('1D');
  let lastRawInput = $state('');

  function showError(err: unknown): void {
    if (err instanceof CommandApiError) {
      errorMessage = err.message;
      errorSuggestions = err.detail?.suggestions ?? [];
    } else {
      errorMessage = 'error inesperado en el frontend';
      errorSuggestions = [];
    }
    kind = 'error';
  }

  async function runCommand(raw: string, resolution: Range): Promise<void> {
    try {
      const result = await postCommand(raw, { resolution });
      response = result;
      kind = panelForResponse(result);
    } catch (err) {
      showError(err);
    }
  }

  async function handleSubmit(raw: string): Promise<void> {
    const upper = raw.trim().toUpperCase();
    if (upper === 'WATCH') {
      kind = 'watch';
      response = null;
      return;
    }
    if (upper === 'HOME') {
      kind = 'welcome';
      response = null;
      return;
    }
    lastRawInput = raw;
    await runCommand(raw, activeRange);
  }

  async function handleRangeChange(range: Range): Promise<void> {
    activeRange = range;
    if (lastRawInput) {
      await runCommand(lastRawInput, range);
    }
  }

  /**
   * feat-18: navegación cruzada entre símbolos — clicar un símbolo referenciado
   * dentro de un panel (ej. una fila de CORR, un nodo de MAP) lleva a su SUMMARY,
   * reutilizando el mismo camino que escribirlo a mano en la barra de comando.
   */
  async function navigateToSymbol(symbol: string): Promise<void> {
    await handleSubmit(symbol);
  }
</script>

<div class="app-shell">
  <header>
    <div class="brand">
      <span class="name">sterminal</span>
      <span class="dimmer version">v0.9 · local</span>
    </div>
  </header>
  <main>
    <PanelRouter
      {kind}
      {response}
      {errorMessage}
      {errorSuggestions}
      {activeRange}
      onRangeChange={handleRangeChange}
      onNavigate={navigateToSymbol}
    />
  </main>
  <CommandBar onSubmit={handleSubmit} />
</div>

<style>
  .app-shell {
    display: flex;
    flex-direction: column;
    height: 100%;
  }
  header {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 6px 12px;
    border-bottom: 1px solid var(--border);
    background: var(--panel);
    flex: none;
  }
  .brand {
    display: flex;
    align-items: baseline;
    gap: 8px;
  }
  .name {
    color: var(--acc);
    font-weight: 700;
    letter-spacing: 1.5px;
  }
  .version {
    font-size: 11px;
  }
  main {
    flex: 1;
    min-height: 0;
    overflow: auto;
  }
</style>
