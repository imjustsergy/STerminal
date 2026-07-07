import { describe, expect, it } from 'vitest';
import { panelForResponse, panelForType } from './dispatch';
import type { CommandResponse } from './types';

describe('panelForType', () => {
  it('mapea cada CommandType conocido a su panel', () => {
    expect(panelForType('SUMMARY')).toBe('summary');
    expect(panelForType('GRAPH_PRICE')).toBe('graph_price');
    expect(panelForType('PORTFOLIO')).toBe('portfolio');
    expect(panelForType('HELP')).toBe('help');
  });

  it('cae a "unknown" ante un type no reconocido, sin reventar', () => {
    expect(panelForType('NEWS')).toBe('unknown');
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
