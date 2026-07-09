<script lang="ts">
  import { postCommand } from '../../lib/api';
  import type { ProvidersResponse } from '../../lib/types';

  interface Props {
    response: ProvidersResponse;
  }

  const { response }: Props = $props();

  // feat-21: la respuesta de PROVIDERS SET ya trae el estado completo actualizado
  // (mismo espíritu que WatchlistPanel.removeSymbol) — se sustituye el estado local
  // en vez de forzar un remount del panel entero.
  let providers = $state(response.providers);
  let switching = $state<string | null>(null);

  const ASSET_CLASS_LABELS: Record<string, string> = {
    equity: 'EQUITY',
    crypto: 'CRYPTO',
    fx: 'FX',
  };

  async function activate(assetClass: string, name: string): Promise<void> {
    switching = `${assetClass}:${name}`;
    try {
      const result = await postCommand(`PROVIDERS SET ${assetClass} ${name}`);
      if (result.type === 'PROVIDERS') {
        providers = result.providers;
      }
    } catch {
      // postCommand ya normaliza errores de red/backend — un fallo aquí no debe
      // reventar el panel, el proveedor simplemente sigue como estaba.
    } finally {
      switching = null;
    }
  }
</script>

<div class="providers-panel">
  <div class="header">
    <span class="title">PROVEEDORES DE DATOS</span>
    <span class="dim hint">
      <span class="acc">PROVIDERS SET &lt;CLASE&gt; &lt;PROVEEDOR&gt;</span> para cambiar el activo
    </span>
  </div>
  {#each Object.entries(providers) as [assetClass, list] (assetClass)}
    <div class="asset-class-block">
      <div class="asset-class-title dim">{ASSET_CLASS_LABELS[assetClass] ?? assetClass.toUpperCase()}</div>
      <table>
        <thead>
          <tr>
            <th>PROVEEDOR</th>
            <th class="num">ESTADO</th>
            <th class="num"></th>
          </tr>
        </thead>
        <tbody>
          {#each list as provider (provider.name)}
            {@const key = `${assetClass}:${provider.name}`}
            <tr>
              <td class:acc={provider.active}>{provider.name}</td>
              {#if provider.active}
                <td class="num status-active">● ACTIVO</td>
                <td class="num"></td>
              {:else}
                <td class="num dim">inactivo</td>
                <td class="num">
                  <button
                    type="button"
                    class="activate-btn"
                    disabled={switching === key}
                    onclick={() => activate(assetClass, provider.name)}
                  >
                    activar
                  </button>
                </td>
              {/if}
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {/each}
</div>

<style>
  .providers-panel {
    padding: 0 0 40px;
  }
  .header {
    display: flex;
    align-items: baseline;
    gap: 12px;
    padding: 11px 18px;
    border-bottom: 1px solid var(--border);
    background: var(--panel);
  }
  .title {
    font-weight: 700;
    font-size: 15px;
  }
  .hint {
    font-size: 11px;
  }
  .acc {
    color: var(--acc);
  }
  .asset-class-block {
    padding: 16px 18px 0;
  }
  .asset-class-title {
    font-size: 11px;
    letter-spacing: 1px;
    margin-bottom: 6px;
  }
  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 12px;
  }
  th {
    text-align: right;
    color: var(--dimmer);
    font-weight: 400;
    font-size: 10px;
    letter-spacing: 0.5px;
    padding: 6px 14px;
    border-bottom: 1px solid var(--border);
    background: var(--panel2);
  }
  th:first-child {
    text-align: left;
  }
  td {
    padding: 6px 14px;
    border-bottom: 1px solid var(--border);
  }
  td.num {
    text-align: right;
  }
  .status-active {
    color: var(--pos);
    font-size: 11px;
  }
  .activate-btn {
    background: none;
    border: 1px solid var(--border);
    color: var(--dim);
    font-family: inherit;
    font-size: 11px;
    padding: 3px 9px;
    cursor: pointer;
  }
  .activate-btn:hover:not(:disabled) {
    color: var(--acc);
    border-color: var(--acc);
  }
  .activate-btn:disabled {
    opacity: 0.4;
    cursor: default;
  }
</style>
