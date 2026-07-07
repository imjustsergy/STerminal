import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, waitFor } from '@testing-library/svelte';
import CommandBar from './CommandBar.svelte';

vi.mock('../lib/api', () => ({
  searchSymbols: vi.fn(),
}));

import { searchSymbols } from '../lib/api';

function getInput(getByLabelText: (label: string) => HTMLElement): HTMLInputElement {
  return getByLabelText('Barra de comando') as HTMLInputElement;
}

describe('CommandBar — autocompletado de símbolos (feat-13)', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.mocked(searchSymbols).mockReset();
  });

  afterEach(() => {
    cleanup();
    vi.useRealTimers();
  });

  it('no busca hasta pasar el debounce', async () => {
    vi.mocked(searchSymbols).mockResolvedValue([]);
    const { getByLabelText } = render(CommandBar, { onSubmit: vi.fn() });
    const input = getInput(getByLabelText);

    await fireEvent.input(input, { target: { value: 'AA' } });
    expect(searchSymbols).not.toHaveBeenCalled();

    vi.advanceTimersByTime(250);
    await Promise.resolve();
    expect(searchSymbols).toHaveBeenCalledWith('AA');
  });

  it('no busca si el valor ya tiene un espacio (función escrita)', async () => {
    const { getByLabelText } = render(CommandBar, { onSubmit: vi.fn() });
    const input = getInput(getByLabelText);

    await fireEvent.input(input, { target: { value: 'AAPL GP' } });
    vi.advanceTimersByTime(300);
    await Promise.resolve();

    expect(searchSymbols).not.toHaveBeenCalled();
  });

  it('muestra el dropdown con los resultados tras el debounce', async () => {
    vi.mocked(searchSymbols).mockResolvedValue([
      { symbol: 'AAPL', name: 'Apple Inc.', asset_class: 'equity' },
      { symbol: 'AAPL.MX', name: 'Apple Inc. (Mexico)', asset_class: 'equity' },
    ]);
    const { getByLabelText, getByText } = render(CommandBar, { onSubmit: vi.fn() });
    const input = getInput(getByLabelText);

    await fireEvent.input(input, { target: { value: 'AA' } });
    vi.advanceTimersByTime(250);
    await Promise.resolve();
    await waitFor(() => expect(getByText('Apple Inc.')).toBeInTheDocument());

    expect(getByText('AAPL.MX')).toBeInTheDocument();
  });

  it('↓/↑ navegan el dropdown en vez de tocar el historial mientras está abierto', async () => {
    vi.mocked(searchSymbols).mockResolvedValue([
      { symbol: 'AAPL', name: 'Apple Inc.', asset_class: 'equity' },
      { symbol: 'AMZN', name: 'Amazon.com Inc.', asset_class: 'equity' },
    ]);
    const { getByLabelText, getAllByRole } = render(CommandBar, { onSubmit: vi.fn() });
    const input = getInput(getByLabelText);

    await fireEvent.input(input, { target: { value: 'A' } });
    vi.advanceTimersByTime(250);
    await Promise.resolve();
    await waitFor(() => expect(getAllByRole('option')).toHaveLength(2));

    await fireEvent.keyDown(input, { key: 'ArrowDown' });
    const options = getAllByRole('option');
    expect(options[1].getAttribute('aria-selected')).toBe('true');
  });

  it('Enter con una sugerencia resaltada la selecciona sin ejecutar el comando', async () => {
    vi.mocked(searchSymbols).mockResolvedValue([
      { symbol: 'AAPL', name: 'Apple Inc.', asset_class: 'equity' },
    ]);
    const onSubmit = vi.fn();
    const { getByLabelText, queryByRole } = render(CommandBar, { onSubmit });
    const input = getInput(getByLabelText);

    await fireEvent.input(input, { target: { value: 'AA' } });
    vi.advanceTimersByTime(250);
    await Promise.resolve();
    await waitFor(() => expect(queryByRole('option')).toBeInTheDocument());

    await fireEvent.keyDown(input, { key: 'Enter' });

    expect(input.value).toBe('AAPL');
    expect(onSubmit).not.toHaveBeenCalled();
    expect(queryByRole('option')).not.toBeInTheDocument();
  });

  it('clic en una sugerencia la selecciona', async () => {
    vi.mocked(searchSymbols).mockResolvedValue([
      { symbol: 'AAPL', name: 'Apple Inc.', asset_class: 'equity' },
    ]);
    const { getByLabelText, getByText } = render(CommandBar, { onSubmit: vi.fn() });
    const input = getInput(getByLabelText);

    await fireEvent.input(input, { target: { value: 'AA' } });
    vi.advanceTimersByTime(250);
    await Promise.resolve();
    await waitFor(() => expect(getByText('Apple Inc.')).toBeInTheDocument());

    await fireEvent.click(getByText('Apple Inc.'));
    expect(input.value).toBe('AAPL');
  });

  it('Escape con el dropdown abierto lo cierra sin borrar el valor', async () => {
    vi.mocked(searchSymbols).mockResolvedValue([
      { symbol: 'AAPL', name: 'Apple Inc.', asset_class: 'equity' },
    ]);
    const { getByLabelText, queryByRole } = render(CommandBar, { onSubmit: vi.fn() });
    const input = getInput(getByLabelText);

    await fireEvent.input(input, { target: { value: 'AA' } });
    vi.advanceTimersByTime(250);
    await Promise.resolve();
    await waitFor(() => expect(queryByRole('option')).toBeInTheDocument());

    await fireEvent.keyDown(input, { key: 'Escape' });

    expect(queryByRole('option')).not.toBeInTheDocument();
    expect(input.value).toBe('AA');
  });

  it('sin dropdown abierto, ↑/↓ siguen controlando el historial (feat-8)', async () => {
    const onSubmit = vi.fn();
    const { getByLabelText } = render(CommandBar, { onSubmit });
    const input = getInput(getByLabelText);

    await fireEvent.input(input, { target: { value: 'PORT' } });
    await fireEvent.keyDown(input, { key: 'Enter' });
    expect(onSubmit).toHaveBeenCalledWith('PORT');

    await fireEvent.keyDown(input, { key: 'ArrowUp' });
    expect(input.value).toBe('PORT');
  });
});
