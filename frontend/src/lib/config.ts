// Configuración compartida — URL base del backend (feat-8) y derivación de la URL de
// WebSocket (feat-10). Un único módulo para no repetir el fallback en cada llamada.

const DEFAULT_API_BASE_URL = 'http://localhost:8000';

/** `VITE_API_BASE_URL`, con fallback a `http://localhost:8000` (ver feat-8/plan-8). */
export const API_BASE_URL: string =
  (import.meta.env?.VITE_API_BASE_URL as string | undefined) ?? DEFAULT_API_BASE_URL;

/**
 * Deriva la URL del WebSocket `/stream` a partir de `API_BASE_URL`: `http`→`ws`,
 * `https`→`wss`, mismo host/puerto, path `/stream`. Ver decisión en
 * plan-10-frontend-panels.md ("sin variable de entorno nueva").
 */
export function wsUrl(base: string = API_BASE_URL): string {
  const url = new URL(base);
  url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
  url.pathname = '/stream';
  return url.toString();
}

/**
 * Lista fija de símbolos de la watchlist (feat-10) — gestión de watchlist (añadir/
 * quitar desde la UI, persistencia en SQLite) queda fuera de alcance del MVP.
 */
export const DEFAULT_WATCHLIST: string[] = [
  'AAPL',
  'NVDA',
  'TSLA',
  'BTC',
  'ETH',
  'SOL',
  'EURUSD',
];

/** Retraso fijo de reintento de reconexión del WebSocket (feat-11). */
export const RECONNECT_DELAY_MS = 5000;
