<script lang="ts">
  import CommandBar from './components/CommandBar.svelte';
  import PanelRouter from './components/PanelRouter.svelte';
  import { CommandApiError, postCommand } from './lib/api';
  import type { Range } from './lib/chartData';
  import { panelForResponse, type PanelKind } from './lib/dispatch';
  import type { CommandResponse } from './lib/types';

  let kind: PanelKind | 'welcome' | 'error' = $state('welcome');
  let response: CommandResponse | null = $state(null);
  let errorMessage = $state('');
  let errorSuggestions: string[] = $state([]);
  let activeRange: Range = $state('1D');
  let lastRawInput = $state('');
  // feat-20: se incrementa cada vez que WATCH ADD/REMOVE tiene éxito desde la barra
  // de comando (kind ya vale 'watch', así que no remontaría solo) — PanelRouter usa
  // este contador como key para forzar que WatchlistPanel se remonte y recargue la
  // lista persistida real.
  let watchlistVersion = $state(0);
  // feat-23: sin esto, el panel anterior se queda estático y sin ninguna señal
  // mientras postCommand está en curso — el owner no tiene forma de distinguir
  // "está cargando" de "se ha quedado colgado". Activo mientras cualquier
  // comando (o cambio de rango del gráfico) está en vuelo.
  let loading = $state(false);

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
    loading = true;
    try {
      const result = await postCommand(raw, { resolution });
      response = result;
      kind = panelForResponse(result);
      if (result.type === 'WATCHLIST_ADD' || result.type === 'WATCHLIST_REMOVE') {
        watchlistVersion += 1;
      }
    } catch (err) {
      showError(err);
    } finally {
      loading = false;
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
  <div class="progress-track" class:active={loading} aria-hidden={!loading}>
    <div class="progress-bar"></div>
  </div>
  <main>
    <PanelRouter
      {kind}
      {response}
      {errorMessage}
      {errorSuggestions}
      {activeRange}
      {watchlistVersion}
      onRangeChange={handleRangeChange}
      onNavigate={navigateToSymbol}
    />
  </main>
  <CommandBar onSubmit={handleSubmit} hint={loading ? 'cargando…' : ''} />
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
  .progress-track {
    height: 2px;
    flex: none;
    background: transparent;
    overflow: hidden;
  }
  .progress-track.active {
    background: var(--border);
  }
  .progress-bar {
    height: 100%;
    width: 40%;
    background: var(--acc);
    transform: translateX(-100%);
  }
  .progress-track.active .progress-bar {
    animation: progress-sweep 1.1s ease-in-out infinite;
  }
  @keyframes progress-sweep {
    0% {
      transform: translateX(-100%);
    }
    50% {
      transform: translateX(150%);
    }
    100% {
      transform: translateX(150%);
    }
  }
  main {
    flex: 1;
    min-height: 0;
    overflow: auto;
  }
</style>
