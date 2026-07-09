import { afterEach, describe, expect, it, vi } from 'vitest';
import { cleanup, render } from '@testing-library/svelte';
import CorrelationsPanel from './CorrelationsPanel.svelte';
import type { CorrelationsResponse } from '../../lib/types';

afterEach(() => {
  cleanup();
});

describe('CorrelationsPanel', () => {
  it('renderiza cada referencia de la cesta con su coeficiente', () => {
    const response: CorrelationsResponse = {
      type: 'CORR',
      symbol: 'AAPL',
      asset_class: 'equity',
      correlations: [
        { symbol: 'SPY', asset_class: 'equity', correlation: 0.85 },
        { symbol: 'GLD', asset_class: 'equity', correlation: -0.2 },
      ],
    };
    const { getByText } = render(CorrelationsPanel, { response, onNavigate: vi.fn() });

    expect(getByText('SPY')).toBeInTheDocument();
    expect(getByText('+0.85')).toBeInTheDocument();
    expect(getByText('GLD')).toBeInTheDocument();
    expect(getByText('-0.20')).toBeInTheDocument();
  });

  it('muestra "datos insuficientes" por fila cuando correlation es null, sin tratarlo como error', () => {
    const response: CorrelationsResponse = {
      type: 'CORR',
      symbol: 'NEWCOIN',
      asset_class: 'crypto',
      correlations: [{ symbol: 'BTC', asset_class: 'crypto', correlation: null }],
    };
    const { getByText, queryByText } = render(CorrelationsPanel, { response, onNavigate: vi.fn() });

    expect(getByText('datos insuficientes')).toBeInTheDocument();
    expect(queryByText('ERROR')).not.toBeInTheDocument();
  });

  it('muestra el símbolo y la clase de activo en la cabecera', () => {
    const response: CorrelationsResponse = {
      type: 'CORR',
      symbol: 'AAPL',
      asset_class: 'equity',
      correlations: [],
    };
    const { getByText } = render(CorrelationsPanel, { response, onNavigate: vi.fn() });

    expect(getByText('AAPL')).toBeInTheDocument();
    expect(getByText('equity')).toBeInTheDocument();
  });

  it('feat-18: clicar una fila de referencia navega a ese símbolo', () => {
    const response: CorrelationsResponse = {
      type: 'CORR',
      symbol: 'AAPL',
      asset_class: 'equity',
      correlations: [{ symbol: 'SPY', asset_class: 'equity', correlation: 0.85 }],
    };
    const onNavigate = vi.fn();
    const { getByText } = render(CorrelationsPanel, { response, onNavigate });

    getByText('SPY').closest('button')?.click();
    expect(onNavigate).toHaveBeenCalledWith('SPY');
  });
});
