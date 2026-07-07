import { afterEach, describe, expect, it } from 'vitest';
import { cleanup, render } from '@testing-library/svelte';
import NewsPanel from './NewsPanel.svelte';
import type { NewsResponse } from '../../lib/types';

afterEach(() => {
  cleanup();
});

describe('NewsPanel', () => {
  it('renderiza los titulares con fuente y enlace', () => {
    const response: NewsResponse = {
      type: 'NEWS',
      symbol: 'AAPL',
      asset_class: 'equity',
      items: [
        {
          title: 'Apple anuncia resultados',
          url: 'https://example.com/apple',
          source: 'Example Wire',
          published_at: new Date().toISOString(),
        },
      ],
    };
    const { getByText } = render(NewsPanel, { response });

    expect(getByText('Apple anuncia resultados')).toBeInTheDocument();
    expect(getByText('Example Wire')).toBeInTheDocument();
    const link = getByText('Apple anuncia resultados').closest('a');
    expect(link).toHaveAttribute('href', 'https://example.com/apple');
    expect(link).toHaveAttribute('target', '_blank');
  });

  it('muestra "sin noticias disponibles" para una lista vacía, sin tratarlo como error', () => {
    const response: NewsResponse = {
      type: 'NEWS',
      symbol: 'BTC',
      asset_class: 'crypto',
      items: [],
    };
    const { getByText, queryByText } = render(NewsPanel, { response });

    expect(getByText(/sin noticias disponibles para BTC/)).toBeInTheDocument();
    expect(queryByText('ERROR')).not.toBeInTheDocument();
  });

  it('muestra el símbolo y la clase de activo en la cabecera', () => {
    const response: NewsResponse = {
      type: 'NEWS',
      symbol: 'AAPL',
      asset_class: 'equity',
      items: [],
    };
    const { getByText } = render(NewsPanel, { response });

    expect(getByText('AAPL')).toBeInTheDocument();
    expect(getByText('equity')).toBeInTheDocument();
  });
});
