<script lang="ts">
  import { onDestroy, onMount } from 'svelte';
  import { CommandHistory } from '../lib/commandHistory';
  import { searchSymbols } from '../lib/api';
  import type { SymbolMatch } from '../lib/types';

  interface Props {
    onSubmit: (raw: string) => void;
    /** Sugerencia/pista mostrada a la derecha de la barra (ej. estado del último comando). */
    hint?: string;
  }

  const { onSubmit, hint = '' }: Props = $props();

  let value = $state('');
  let inputEl: HTMLInputElement | undefined = $state();
  const history = new CommandHistory();

  // --- Autocompletado de símbolos (feat-13) ---------------------------------
  let suggestions: SymbolMatch[] = $state([]);
  let suggestionIndex = $state(-1);
  const dropdownOpen = $derived(suggestions.length > 0);
  let debounceTimer: ReturnType<typeof setTimeout> | undefined;
  // Descarta respuestas de búsquedas ya obsoletas (el usuario siguió escribiendo antes
  // de que volviera el fetch anterior) — evita que una respuesta lenta pise una más
  // reciente.
  let searchToken = 0;

  function closeSuggestions(): void {
    suggestions = [];
    suggestionIndex = -1;
  }

  function selectSuggestion(match: SymbolMatch): void {
    value = match.symbol;
    closeSuggestions();
    inputEl?.focus();
  }

  function scheduleSearch(query: string): void {
    if (debounceTimer) {
      clearTimeout(debounceTimer);
    }
    // Solo mientras se escribe el símbolo, antes de una función (ej. "AAPL GP") — un
    // espacio significa que el usuario ya pasó a teclear la función, no tiene sentido
    // seguir buscando símbolos.
    if (!query || query.includes(' ')) {
      closeSuggestions();
      return;
    }
    const token = ++searchToken;
    debounceTimer = setTimeout(async () => {
      const results = await searchSymbols(query);
      if (token !== searchToken) {
        return; // respuesta obsoleta, una búsqueda más nueva ya está en curso
      }
      suggestions = results;
      suggestionIndex = results.length > 0 ? 0 : -1;
    }, 250);
  }

  function onInput(): void {
    scheduleSearch(value.trim());
  }

  function submit(): void {
    const raw = value.trim();
    if (!raw) {
      return;
    }
    history.push(raw);
    onSubmit(raw);
    value = '';
    closeSuggestions();
  }

  function onKeyDown(event: KeyboardEvent): void {
    if (dropdownOpen) {
      if (event.key === 'ArrowDown') {
        event.preventDefault();
        suggestionIndex = (suggestionIndex + 1) % suggestions.length;
        return;
      }
      if (event.key === 'ArrowUp') {
        event.preventDefault();
        suggestionIndex = (suggestionIndex - 1 + suggestions.length) % suggestions.length;
        return;
      }
      if (event.key === 'Enter' && suggestionIndex >= 0) {
        event.preventDefault();
        selectSuggestion(suggestions[suggestionIndex]);
        return;
      }
      if (event.key === 'Escape') {
        event.preventDefault();
        closeSuggestions();
        return;
      }
    }

    if (event.key === 'Enter') {
      event.preventDefault();
      submit();
      return;
    }
    if (event.key === 'ArrowUp') {
      event.preventDefault();
      const prev = history.prev();
      if (prev !== null) {
        value = prev;
      }
      return;
    }
    if (event.key === 'ArrowDown') {
      event.preventDefault();
      const next = history.next();
      if (next !== null) {
        value = next;
      }
      return;
    }
    if (event.key === 'Escape') {
      value = '';
    }
  }

  // Re-enfoca la barra de comando si el foco se pierde a cualquier sitio que no sea un
  // input explícito (DESIGN.md sección 3 / prototipo sterminal.dc.html) — un keydown
  // imprimible en cualquier parte de la página vuelve a llevar el foco al input.
  function onWindowKeyDown(event: KeyboardEvent): void {
    const target = event.target as HTMLElement | null;
    const tag = target?.tagName ?? '';
    if (tag === 'INPUT' || tag === 'TEXTAREA') {
      return;
    }
    if (event.metaKey || event.ctrlKey || event.altKey) {
      return;
    }
    if (event.key.length === 1 || event.key === 'Backspace') {
      inputEl?.focus();
    }
  }

  onMount(() => {
    window.addEventListener('keydown', onWindowKeyDown);
    inputEl?.focus();
  });

  onDestroy(() => {
    window.removeEventListener('keydown', onWindowKeyDown);
    if (debounceTimer) {
      clearTimeout(debounceTimer);
    }
  });
</script>

<div class="command-bar-wrap">
  {#if dropdownOpen}
    <ul class="suggestions" role="listbox">
      {#each suggestions as match, i (match.symbol + match.asset_class)}
        <li>
          <button
            type="button"
            role="option"
            aria-selected={i === suggestionIndex}
            class:active={i === suggestionIndex}
            onmousedown={(e) => e.preventDefault()}
            onclick={() => selectSuggestion(match)}
          >
            <span class="sym acc">{match.symbol}</span>
            <span class="name dim">{match.name}</span>
            <span class="class dimmer">{match.asset_class}</span>
          </button>
        </li>
      {/each}
    </ul>
  {/if}
  <div class="command-bar">
    <span class="prompt">&rsaquo;</span>
    <input
      bind:this={inputEl}
      bind:value
      oninput={onInput}
      onkeydown={onKeyDown}
      spellcheck="false"
      autocomplete="off"
      placeholder="Escribe un comando…  p.ej.  AAPL · BTC GP · PORT · WATCH · HELP"
      aria-label="Barra de comando"
    />
    {#if hint}
      <span class="hint dimmer">{hint}</span>
    {/if}
  </div>
</div>

<style>
  .command-bar-wrap {
    position: relative;
    flex: none;
  }
  .command-bar {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 14px;
    border-top: 1px solid var(--border);
    background: var(--panel);
  }
  .prompt {
    color: var(--acc);
    font-weight: 700;
    font-size: 15px;
  }
  input {
    flex: 1;
    background: transparent;
    border: none;
    outline: none;
    color: var(--fg);
    font-size: 15px;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    caret-color: var(--acc);
  }
  input::placeholder {
    color: var(--dimmer);
    text-transform: none;
  }
  .hint {
    font-size: 11px;
    white-space: nowrap;
  }
  .suggestions {
    position: absolute;
    bottom: 100%;
    left: 0;
    right: 0;
    list-style: none;
    max-height: 260px;
    overflow-y: auto;
    background: var(--panel);
    border: 1px solid var(--border);
    border-bottom: none;
  }
  .suggestions button {
    display: flex;
    align-items: baseline;
    gap: 10px;
    width: 100%;
    padding: 7px 14px;
    background: none;
    border: none;
    border-bottom: 1px solid var(--border);
    color: var(--fg);
    font-family: inherit;
    font-size: 12px;
    text-align: left;
    cursor: pointer;
  }
  .suggestions button.active {
    background: var(--panel2);
  }
  .sym {
    font-weight: 700;
    min-width: 90px;
  }
  .name {
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .class {
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
</style>
