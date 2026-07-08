import { afterEach, describe, expect, it } from 'vitest';
import { cleanup, render } from '@testing-library/svelte';
import ReportsPanel from './ReportsPanel.svelte';
import type { ReportsResponse } from '../../lib/types';

afterEach(() => {
  cleanup();
});

describe('ReportsPanel', () => {
  it('renderiza cada enlace con su etiqueta y href', () => {
    const response: ReportsResponse = {
      type: 'REPORTS',
      symbol: 'AAPL',
      asset_class: 'equity',
      links: [
        { label: 'Yahoo Finance', url: 'https://finance.yahoo.com/quote/AAPL' },
        {
          label: 'SEC EDGAR — filings 10-K',
          url: 'https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&company=AAPL&type=10-K',
        },
      ],
    };
    const { getByText } = render(ReportsPanel, { response });

    const yahoo = getByText('Yahoo Finance');
    expect(yahoo).toBeInTheDocument();
    expect(yahoo.closest('a')).toHaveAttribute('href', 'https://finance.yahoo.com/quote/AAPL');
    expect(yahoo.closest('a')).toHaveAttribute('target', '_blank');
    expect(getByText('SEC EDGAR — filings 10-K')).toBeInTheDocument();
  });

  it('muestra "sin enlaces disponibles" para una lista vacía, sin tratarlo como error', () => {
    const response: ReportsResponse = {
      type: 'REPORTS',
      symbol: 'EURUSD',
      asset_class: 'fx',
      links: [],
    };
    const { getByText, queryByText } = render(ReportsPanel, { response });

    expect(getByText(/sin enlaces disponibles para EURUSD/)).toBeInTheDocument();
    expect(queryByText('ERROR')).not.toBeInTheDocument();
  });

  it('muestra el símbolo y la clase de activo en la cabecera', () => {
    const response: ReportsResponse = {
      type: 'REPORTS',
      symbol: 'AAPL',
      asset_class: 'equity',
      links: [],
    };
    const { getByText } = render(ReportsPanel, { response });

    expect(getByText('AAPL')).toBeInTheDocument();
    expect(getByText('equity')).toBeInTheDocument();
  });
});
