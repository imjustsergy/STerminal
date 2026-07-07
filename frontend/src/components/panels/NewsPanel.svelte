<script lang="ts">
  import { ageLabel } from '../../lib/format';
  import type { NewsResponse } from '../../lib/types';

  interface Props {
    response: NewsResponse;
  }

  const { response }: Props = $props();

  const now = Date.now();

  function relativeDate(publishedAt: string): string {
    const ms = Date.parse(publishedAt);
    if (Number.isNaN(ms)) {
      return publishedAt;
    }
    return ageLabel(ms, now);
  }
</script>

<div class="news-panel">
  <div class="header">
    <span class="title">NOTICIAS</span>
    <span class="symbol acc">{response.symbol}</span>
    <span class="dim class-tag">{response.asset_class}</span>
  </div>
  {#if response.items.length === 0}
    <div class="empty dim">
      sin noticias disponibles para {response.symbol}
      {#if response.asset_class !== 'equity'}
        <span class="dimmer"> — solo acciones tienen fuente de noticias por ahora</span>
      {/if}
    </div>
  {:else}
    <ul class="items">
      {#each response.items as item (item.url || item.title)}
        <li>
          <a class="headline" href={item.url} target="_blank" rel="noopener noreferrer">
            {item.title}
          </a>
          <div class="meta dim">
            <span class="source">{item.source}</span>
            <span class="sep">·</span>
            <span class="age">{relativeDate(item.published_at)}</span>
          </div>
        </li>
      {/each}
    </ul>
  {/if}
</div>

<style>
  .news-panel {
    padding: 20px 18px 60px;
    max-width: 820px;
  }
  .header {
    display: flex;
    align-items: baseline;
    gap: 10px;
    margin-bottom: 18px;
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
  .empty {
    font-size: 13px;
    padding: 12px 0;
  }
  .items {
    list-style: none;
    display: flex;
    flex-direction: column;
    gap: 14px;
  }
  .headline {
    display: block;
    color: var(--fg);
    font-size: 13px;
    font-weight: 500;
    text-decoration: none;
  }
  .headline:hover {
    color: var(--acc);
    text-decoration: underline;
  }
  .meta {
    font-size: 11px;
    margin-top: 3px;
  }
  .sep {
    margin: 0 5px;
  }
</style>
