<script lang="ts">
  import CommandBar from './components/CommandBar.svelte';
  import PanelRouter from './components/PanelRouter.svelte';
  import { postCommand } from './lib/api';
  import type { Range } from './lib/chartData';
  import { panelForResponse, type PanelKind } from './lib/dispatch';
  import type { CommandResponse } from './lib/types';

  let kind: PanelKind | 'welcome' = $state('welcome');
  let response: CommandResponse | null = $state(null);
  let errorMessage = $state('');
  let activeRange: Range = $state('1D');
  let lastRawInput = $state('');

  async function runCommand(raw: string, resolution: Range): Promise<void> {
    try {
      const result = await postCommand(raw, { resolution });
      response = result;
      kind = panelForResponse(result);
    } catch (err) {
      errorMessage = err instanceof Error ? err.message : 'error inesperado en el frontend';
      kind = 'unknown';
    }
  }

  async function handleSubmit(raw: string): Promise<void> {
    const upper = raw.trim().toUpperCase();
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
</script>

<div class="app-shell">
  <header>
    <div class="brand">
      <span class="name">sterminal</span>
      <span class="dimmer version">v0.9 · local</span>
    </div>
  </header>
  <main>
    <PanelRouter {kind} {response} {errorMessage} {activeRange} onRangeChange={handleRangeChange} />
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
