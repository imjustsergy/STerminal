import { afterEach, describe, expect, it } from 'vitest';
import { cleanup, render } from '@testing-library/svelte';
import FinancialsPanel from './FinancialsPanel.svelte';
import type { FinancialsResponse } from '../../lib/types';

afterEach(() => {
  cleanup();
});

describe('FinancialsPanel', () => {
  it('renderiza los ratios financieros con el formato por campo', () => {
    const response: FinancialsResponse = {
      type: 'FA',
      symbol: 'AAPL',
      asset_class: 'equity',
      financials: {
        symbol: 'AAPL',
        market_cap: 4562774130688,
        pe_ratio: 37.655758,
        eps: 8.25,
        dividend_yield: 0.35,
        week52_high: 317.4,
        week52_low: 201.5,
        beta: 1.097,
        sector: 'Technology',
        industry: 'Consumer Electronics',
      },
    };
    const { getByText } = render(FinancialsPanel, { response });

    expect(getByText('$4.56T')).toBeInTheDocument();
    expect(getByText('37.66x')).toBeInTheDocument();
    expect(getByText('$8.25')).toBeInTheDocument();
    expect(getByText('0.35%')).toBeInTheDocument();
    expect(getByText('Technology')).toBeInTheDocument();
    expect(getByText('Consumer Electronics')).toBeInTheDocument();
  });

  it('muestra "no disponible" por campo cuando todos los valores son null, sin tratarlo como error', () => {
    const response: FinancialsResponse = {
      type: 'FA',
      symbol: 'BTC',
      asset_class: 'crypto',
      financials: {
        symbol: 'BTC',
        market_cap: null,
        pe_ratio: null,
        eps: null,
        dividend_yield: null,
        week52_high: null,
        week52_low: null,
        beta: null,
        sector: null,
        industry: null,
      },
    };
    const { getAllByText, queryByText } = render(FinancialsPanel, { response });

    expect(getAllByText('no disponible').length).toBe(9);
    expect(queryByText('ERROR')).not.toBeInTheDocument();
  });

  it('muestra el símbolo y la clase de activo en la cabecera', () => {
    const response: FinancialsResponse = {
      type: 'FA',
      symbol: 'AAPL',
      asset_class: 'equity',
      financials: {
        symbol: 'AAPL',
        market_cap: null,
        pe_ratio: null,
        eps: null,
        dividend_yield: null,
        week52_high: null,
        week52_low: null,
        beta: null,
        sector: null,
        industry: null,
      },
    };
    const { getByText } = render(FinancialsPanel, { response });

    expect(getByText('AAPL')).toBeInTheDocument();
    expect(getByText('equity')).toBeInTheDocument();
  });
});
