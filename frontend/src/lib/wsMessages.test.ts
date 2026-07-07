import { describe, expect, it } from 'vitest';
import { isQuoteError, parseStreamMessage } from './wsMessages';

describe('parseStreamMessage', () => {
  it('reconoce un mensaje de cotizaciones válido', () => {
    const raw = JSON.stringify({
      quotes: [
        { symbol: 'AAPL', price: 200, currency: 'USD', change: 1, change_percent: 0.5, timestamp: 't' },
      ],
    });
    const result = parseStreamMessage(raw);
    expect(result.kind).toBe('quotes');
    if (result.kind === 'quotes') {
      expect(result.quotes).toHaveLength(1);
      expect(result.quotes[0]).toMatchObject({ symbol: 'AAPL', price: 200 });
    }
  });

  it('reconoce un mensaje de error de servidor (mensaje inicial inválido)', () => {
    const result = parseStreamMessage(JSON.stringify({ error: "falta la clave 'subscribe'" }));
    expect(result).toEqual({ kind: 'error', error: "falta la clave 'subscribe'" });
  });

  it('cae a "unknown" con JSON malformado', () => {
    expect(parseStreamMessage('{not valid json')).toEqual({ kind: 'unknown' });
  });

  it('cae a "unknown" con una forma inesperada (ni quotes ni error)', () => {
    expect(parseStreamMessage(JSON.stringify({ foo: 1 }))).toEqual({ kind: 'unknown' });
  });

  it('reconoce una entrada individual de símbolo roto dentro de quotes', () => {
    const raw = JSON.stringify({ quotes: [{ symbol: 'ZZZZ', error: 'no encontrado' }] });
    const result = parseStreamMessage(raw);
    expect(result.kind).toBe('quotes');
    if (result.kind === 'quotes') {
      expect(isQuoteError(result.quotes[0])).toBe(true);
    }
  });
});

describe('isQuoteError', () => {
  it('distingue una cotización válida de una entrada de error', () => {
    expect(
      isQuoteError({ symbol: 'AAPL', price: 1, currency: 'USD', change: 0, change_percent: 0, timestamp: 't' }),
    ).toBe(false);
    expect(isQuoteError({ symbol: 'ZZZZ', error: 'no encontrado' })).toBe(true);
  });
});
