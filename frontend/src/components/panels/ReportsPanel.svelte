<script lang="ts">
  import type { ReportsResponse } from '../../lib/types';

  interface Props {
    response: ReportsResponse;
  }

  const { response }: Props = $props();
</script>

<div class="reports-panel">
  <div class="header">
    <span class="title">REPORTS</span>
    <span class="symbol acc">{response.symbol}</span>
    <span class="dim class-tag">{response.asset_class}</span>
  </div>
  <div class="notice dimmer">
    enlaces a fuentes externas — sterminal no aloja ni reprocesa el contenido de los
    reports
  </div>
  {#if response.links.length === 0}
    <div class="empty dim">
      sin enlaces disponibles para {response.symbol}
      {#if response.asset_class === 'fx'}
        <span class="dimmer"> — un par de divisas no tiene reports asociados</span>
      {/if}
    </div>
  {:else}
    <ul class="links">
      {#each response.links as link (link.url)}
        <li>
          <a class="link" href={link.url} target="_blank" rel="noopener noreferrer">
            {link.label}
          </a>
        </li>
      {/each}
    </ul>
  {/if}
</div>

<style>
  .reports-panel {
    padding: 20px 18px 60px;
    max-width: 820px;
  }
  .header {
    display: flex;
    align-items: baseline;
    gap: 10px;
    margin-bottom: 10px;
  }
  .title {
    font-weight: 700;
    font-size: 15px;
  }
  .symbol {
    font-weight: 700;
  }
  .class-tag {
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  .notice {
    font-size: 12px;
    margin-bottom: 18px;
  }
  .empty {
    font-size: 13px;
    padding: 12px 0;
  }
  .links {
    list-style: none;
    display: flex;
    flex-direction: column;
    border: 1px solid var(--border);
  }
  .link {
    display: block;
    padding: 10px 14px;
    color: var(--fg);
    font-size: 13px;
    font-weight: 500;
    text-decoration: none;
    border-bottom: 1px solid var(--border);
  }
  .link:last-child {
    border-bottom: none;
  }
  .link:hover {
    color: var(--acc);
    text-decoration: underline;
  }
</style>
