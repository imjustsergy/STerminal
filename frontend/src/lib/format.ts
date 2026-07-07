/**
 * Formateo compartido de números/P&L/edad de dato (feat-10/feat-11) — funciones puras,
 * testeadas sin DOM.
 */

/** `toLocaleString` con decimales fijos, igual que `fmtN` del prototipo `sterminal.dc.html`. */
export function formatMoney(n: number, dp = 2): string {
  return n.toLocaleString('en-US', {
    minimumFractionDigits: dp,
    maximumFractionDigits: dp,
  });
}

export type Sign = 'pos' | 'neg' | 'dim';

/** Clasifica un número (o `null`) en positivo/negativo/neutro para el color por signo. */
export function signColor(n: number | null | undefined): Sign {
  if (n === null || n === undefined || n === 0) {
    return 'dim';
  }
  return n > 0 ? 'pos' : 'neg';
}

/** `+x.xx%` / `x.xx%` / `-x.xx%`, o `"—"` si `n` es `null` (ej. `daily_pnl_percent` sin histórico). */
export function formatPercent(n: number | null | undefined, dp = 2): string {
  if (n === null || n === undefined) {
    return '—';
  }
  const sign = n > 0 ? '+' : '';
  return `${sign}${n.toFixed(dp)}%`;
}

/** `+$x.xx` / `-$x.xx`, con el signo de dólar antes del valor absoluto. */
export function formatUsd(n: number | null | undefined, dp = 2): string {
  if (n === null || n === undefined) {
    return '—';
  }
  const sign = n < 0 ? '-' : n > 0 ? '+' : '';
  return `${sign}$${formatMoney(Math.abs(n), dp)}`;
}

/**
 * Antigüedad legible de un dato desde `lastUpdateMs` hasta `nowMs` (feat-11, banner de
 * stale), ej. `"hace 22s"` / `"hace 3m"`. Recibe `nowMs` explícito para ser testeable
 * sin depender de temporizadores reales.
 */
export function ageLabel(lastUpdateMs: number, nowMs: number): string {
  const deltaSeconds = Math.max(0, Math.round((nowMs - lastUpdateMs) / 1000));
  if (deltaSeconds < 60) {
    return `hace ${deltaSeconds}s`;
  }
  return `hace ${Math.round(deltaSeconds / 60)}m`;
}
