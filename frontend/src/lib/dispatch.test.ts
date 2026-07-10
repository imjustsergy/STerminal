import { describe, expect, it } from 'vitest';
import { panelForResponse, panelForType, titleForKind } from './dispatch';
import type { CommandResponse } from './types';

describe('panelForType', () => {
  it('mapea cada CommandType conocido a su panel', () => {
    expect(panelForType('SUMMARY')).toBe('summary');
    expect(panelForType('GRAPH_PRICE')).toBe('graph_price');
    expect(panelForType('PORTFOLIO')).toBe('portfolio');
    expect(panelForType('HELP')).toBe('help');
    expect(panelForType('NEWS')).toBe('news');
    expect(panelForType('FA')).toBe('financials');
    expect(panelForType('CORR')).toBe('correlations');
    expect(panelForType('REPORTS')).toBe('reports');
    expect(panelForType('MAP')).toBe('value_chain');
    expect(panelForType('WATCHLIST_ADD')).toBe('watch');
    expect(panelForType('WATCHLIST_REMOVE')).toBe('watch');
    expect(panelForType('PROVIDERS')).toBe('providers');
  });

  it('cae a "unknown" ante un type no reconocido, sin reventar', () => {
    expect(panelForType('')).toBe('unknown');
    expect(panelForType('cualquier-cosa')).toBe('unknown');
  });
});

describe('panelForResponse', () => {
  it('deriva el panel directamente de una CommandResponse tipada', () => {
    const response: CommandResponse = {
      type: 'HELP',
      commands: [],
    };
    expect(panelForResponse(response)).toBe('help');
  });
});

describe('titleForKind (feat-24)', () => {
  const summaryResponse: CommandResponse = {
    type: 'SUMMARY',
    symbol: 'AAPL',
    asset_class: 'equity',
    quote: {
      symbol: 'AAPL',
      price: 1,
      currency: 'USD',
      change: 0,
      change_percent: 0,
      timestamp: 't',
    },
  };

  it('usa el símbolo desnudo para "summary"', () => {
    expect(titleForKind('summary', summaryResponse)).toBe('AAPL · sterminal');
  });

  it('añade el sufijo de comando para paneles con símbolo + función', () => {
    const graphResponse: CommandResponse = {
      type: 'GRAPH_PRICE',
      symbol: 'BTC',
      asset_class: 'crypto',
      candles: [],
    };
    expect(titleForKind('graph_price', graphResponse)).toBe('BTC GP · sterminal');
  });

  it('usa una etiqueta fija para paneles sin símbolo propio', () => {
    expect(titleForKind('portfolio', null)).toBe('PORT · sterminal');
    expect(titleForKind('watch', null)).toBe('WATCH · sterminal');
    expect(titleForKind('providers', null)).toBe('PROVIDERS · sterminal');
    expect(titleForKind('help', null)).toBe('HELP · sterminal');
  });

  it('vuelve al título fijo "sterminal" en bienvenida/error/tipo desconocido', () => {
    expect(titleForKind('welcome', null)).toBe('sterminal');
    expect(titleForKind('error', null)).toBe('sterminal');
    expect(titleForKind('unknown', null)).toBe('sterminal');
  });
});
