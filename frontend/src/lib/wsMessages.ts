import type { StreamQuoteEntry } from './types';

export type StreamMessage =
  | { kind: 'quotes'; quotes: StreamQuoteEntry[] }
  | { kind: 'error'; error: string }
  | { kind: 'unknown' };

/**
 * Parsea un mensaje crudo del WebSocket `/stream` (feat-7) en una de las tres formas
 * reconocidas — función pura, testeada sin un WebSocket real (feat-10). Cualquier JSON
 * malformado o forma inesperada cae a `{kind: "unknown"}` en vez de reventar, mismo
 * espíritu defensivo que el resto del frontend.
 */
export function parseStreamMessage(raw: string): StreamMessage {
  let parsed: unknown;
  try {
    parsed = JSON.parse(raw);
  } catch {
    return { kind: 'unknown' };
  }

  if (!parsed || typeof parsed !== 'object') {
    return { kind: 'unknown' };
  }

  const obj = parsed as Record<string, unknown>;

  if (Array.isArray(obj.quotes)) {
    return { kind: 'quotes', quotes: obj.quotes as StreamQuoteEntry[] };
  }

  if (typeof obj.error === 'string') {
    return { kind: 'error', error: obj.error };
  }

  return { kind: 'unknown' };
}

/** Distingue una entrada de cotización válida de una entrada de símbolo roto. */
export function isQuoteError(entry: StreamQuoteEntry): entry is { symbol: string; error: string } {
  return 'error' in entry;
}
