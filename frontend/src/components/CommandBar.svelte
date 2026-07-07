<script lang="ts">
  import { onDestroy, onMount } from 'svelte';
  import { CommandHistory } from '../lib/commandHistory';

  interface Props {
    onSubmit: (raw: string) => void;
    /** Sugerencia/pista mostrada a la derecha de la barra (ej. estado del último comando). */
    hint?: string;
  }

  const { onSubmit, hint = '' }: Props = $props();

  let value = $state('');
  let inputEl: HTMLInputElement | undefined = $state();
  const history = new CommandHistory();

  function submit(): void {
    const raw = value.trim();
    if (!raw) {
      return;
    }
    history.push(raw);
    onSubmit(raw);
    value = '';
  }

  function onKeyDown(event: KeyboardEvent): void {
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
  });
</script>

<div class="command-bar">
  <span class="prompt">&rsaquo;</span>
  <input
    bind:this={inputEl}
    bind:value
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

<style>
  .command-bar {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 14px;
    border-top: 1px solid var(--border);
    background: var(--panel);
    flex: none;
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
</style>
