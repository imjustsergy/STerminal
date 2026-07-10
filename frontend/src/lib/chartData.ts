import type { UTCTimestamp } from 'lightweight-charts';
import type { Candle } from './types';

/** Forma que espera `lightweight-charts` para una candlestick series. */
export interface LightweightCandle {
  time: UTCTimestamp; // epoch en SEGUNDOS
  open: number;
  high: number;
  low: number;
  close: number;
}

/**
 * Convierte velas del backend (`Candle`, timestamp ISO 8601) al formato de
 * `lightweight-charts` (feat-9). Función pura — importa solo el tipo `UTCTimestamp` de
 * la librería (sin coste en runtime), para que Vitest la teste sin necesitar
 * `<canvas>`/DOM real.
 */
export function toLightweightSeries(candles: Candle[]): LightweightCandle[] {
  return candles.map((candle) => ({
    time: Math.floor(Date.parse(candle.timestamp) / 1000) as UTCTimestamp,
    open: candle.open,
    high: candle.high,
    low: candle.low,
    close: candle.close,
  }));
}

/** Forma que espera `lightweight-charts` para una line/area series — un único `value`
 * por punto, a diferencia de `LightweightCandle` (OHLC). Pasar velas OHLC a una
 * `AreaSeries` revienta en runtime ("Area series item data value must be a number") —
 * error real encontrado al integrar el mini-gráfico de `SummaryPanel` (feat-26). */
export interface LightweightLinePoint {
  time: UTCTimestamp;
  value: number;
}

/** Convierte velas del backend a puntos de línea/área — usa el cierre de cada vela. */
export function toLightweightLineSeries(candles: Candle[]): LightweightLinePoint[] {
  return candles.map((candle) => ({
    time: Math.floor(Date.parse(candle.timestamp) / 1000) as UTCTimestamp,
    value: candle.close,
  }));
}

/** Rangos soportados de verdad por el backend (ver feat-9: no inventar 5D/3M). */
export const SUPPORTED_RANGES = ['1D', '1W', '1M', '1Y'] as const;
export type Range = (typeof SUPPORTED_RANGES)[number];

/**
 * Dado el rango actualmente activo y el rango pulsado, decide si hace falta una nueva
 * petición (`resolution` distinto) — evita releer datos ya cargados si el usuario pulsa
 * el rango que ya está activo.
 */
export function nextRangeRequest(current: Range, requested: Range): Range | null {
  return current === requested ? null : requested;
}
