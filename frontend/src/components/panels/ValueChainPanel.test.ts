import { afterEach, describe, expect, it } from 'vitest';
import { cleanup, render } from '@testing-library/svelte';
import ValueChainPanel from './ValueChainPanel.svelte';
import type { ValueChainResponse } from '../../lib/types';

afterEach(() => {
  cleanup();
});

function baseResponse(overrides: Partial<ValueChainResponse> = {}): ValueChainResponse {
  return {
    type: 'MAP',
    symbol: 'AAPL',
    asset_class: 'equity',
    sector: 'Technology',
    center: {
      symbol: 'AAPL',
      price: 312.19,
      currency: 'USD',
      change: -0.47,
      change_percent: -0.15,
      timestamp: '2026-07-07T00:00:00Z',
    },
    inputs: [
      {
        quote: { symbol: 'SOXX', price: 200.0, currency: 'USD', change: 1.0, change_percent: 0.5, timestamp: '2026-07-07T00:00:00Z' },
        description: 'ETF de semiconductores — insumo clave de dispositivos electrónicos',
      },
      {
        quote: { symbol: 'CPER', price: 30.0, currency: 'USD', change: -0.5, change_percent: -1.5, timestamp: '2026-07-07T00:00:00Z' },
        description: 'ETF de cobre — materia prima de componentes y cableado electrónico',
      },
    ],
    outputs: [
      {
        quote: { symbol: 'XLY', price: 180.0, currency: 'USD', change: 0.8, change_percent: 0.4, timestamp: '2026-07-07T00:00:00Z' },
        description: 'ETF de consumo discrecional — venta de electrónica/bienes de consumo',
      },
    ],
    ...overrides,
  };
}

describe('ValueChainPanel', () => {
  it('renderiza el mindmap: nodo central + nodos de entrada/salida como SVG conectado', () => {
    const { container } = render(ValueChainPanel, { response: baseResponse() });

    const svg = container.querySelector('svg.mindmap');
    expect(svg).not.toBeNull();

    // Nodo central + 2 entradas + 1 salida = 4 círculos.
    const circles = container.querySelectorAll('svg circle');
    expect(circles.length).toBe(4);

    // Cada nodo (menos el centro) se conecta al centro con una línea.
    const edges = container.querySelectorAll('svg line.edge');
    expect(edges.length).toBe(3);

    // Los símbolos aparecen tanto en el SVG como en la leyenda — se comprueba dentro
    // del SVG específicamente para no ambigüedad con getByText.
    const svgSymbols = Array.from(svg!.querySelectorAll('.node-symbol')).map((el) => el.textContent);
    expect(svgSymbols).toEqual(expect.arrayContaining(['AAPL', 'SOXX', 'CPER', 'XLY']));
  });

  it('renderiza una leyenda con la descripción de cada nodo (feedback del owner)', () => {
    const { getByText } = render(ValueChainPanel, { response: baseResponse() });

    expect(getByText(/ETF de semiconductores/)).toBeInTheDocument();
    expect(getByText(/ETF de cobre/)).toBeInTheDocument();
    expect(getByText(/ETF de consumo discrecional/)).toBeInTheDocument();
  });

  it('muestra el sector en la cabecera cuando está presente', () => {
    const { getByText } = render(ValueChainPanel, { response: baseResponse() });
    expect(getByText('Technology')).toBeInTheDocument();
  });

  it('muestra un estado vacío explícito cuando el sector no tiene mapeo curado', () => {
    const response = baseResponse({ sector: 'Financial Services', inputs: [], outputs: [] });
    const { getByText, queryByText } = render(ValueChainPanel, { response });

    expect(getByText(/sin mapeo de cadena de valor definido/)).toBeInTheDocument();
    expect(queryByText('ERROR')).not.toBeInTheDocument();
  });

  it('muestra un estado vacío explícito para crypto/fx (sector null), sin tratarlo como error', () => {
    const response = baseResponse({
      symbol: 'BTC',
      asset_class: 'crypto',
      sector: null,
      inputs: [],
      outputs: [],
      center: {
        symbol: 'BTC',
        price: 63506.0,
        currency: 'USD',
        change: 100.0,
        change_percent: 0.16,
        timestamp: '2026-07-07T00:00:00Z',
      },
    });
    const { getByText, queryByText } = render(ValueChainPanel, { response });

    expect(getByText(/sin taxonomía de sector/)).toBeInTheDocument();
    expect(queryByText('ERROR')).not.toBeInTheDocument();
  });

  it('muestra el símbolo del nodo central', () => {
    const { container } = render(ValueChainPanel, { response: baseResponse() });
    const centerText = container.querySelector('svg .center-node .node-symbol');
    expect(centerText?.textContent).toBe('AAPL');
  });
});
