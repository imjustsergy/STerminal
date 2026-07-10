import type { CommandResponse } from './types';

export type PanelKind =
  | 'summary'
  | 'graph_price'
  | 'portfolio'
  | 'help'
  | 'news'
  | 'financials'
  | 'correlations'
  | 'reports'
  | 'value_chain'
  | 'watch'
  | 'providers'
  | 'unknown';

/**
 * Mapea el campo `type` de una respuesta de `POST /command` al panel que debe
 * renderizarla (feat-8). Cualquier `type` no reconocido cae a `"unknown"` en vez de
 * reventar — mismo espíritu defensivo que el resto del backend (spec.md sección 8).
 */
export function panelForType(type: string): PanelKind {
  switch (type) {
    case 'SUMMARY':
      return 'summary';
    case 'GRAPH_PRICE':
      return 'graph_price';
    case 'PORTFOLIO':
      return 'portfolio';
    case 'HELP':
      return 'help';
    case 'NEWS':
      return 'news';
    case 'FA':
      return 'financials';
    case 'CORR':
      return 'correlations';
    case 'REPORTS':
      return 'reports';
    case 'MAP':
      return 'value_chain';
    case 'WATCHLIST_ADD':
    case 'WATCHLIST_REMOVE':
      return 'watch';
    case 'PROVIDERS':
      return 'providers';
    default:
      return 'unknown';
  }
}

/** Variante tipada: deriva el `PanelKind` directamente de una `CommandResponse`. */
export function panelForResponse(response: CommandResponse): PanelKind {
  return panelForType(response.type);
}

// feat-24: paneles cuya CommandResponse trae un `symbol` que identifica lo que se está
// viendo — el sufijo de comando se añade tras el símbolo en el título de pestaña
// (ej. "AAPL GP · sterminal"). 'summary' no lleva sufijo (solo el símbolo desnudo).
const SYMBOL_TITLE_SUFFIX: Partial<Record<PanelKind, string>> = {
  graph_price: 'GP',
  news: 'NEWS',
  financials: 'FA',
  correlations: 'CORR',
  reports: 'REPORTS',
  value_chain: 'MAP',
};

// Paneles sin símbolo propio pero con una etiqueta fija reconocible en el título.
const FIXED_TITLE_LABEL: Partial<Record<PanelKind, string>> = {
  portfolio: 'PORT',
  watch: 'WATCH',
  providers: 'PROVIDERS',
  help: 'HELP',
};

/**
 * Título de pestaña del navegador (feat-24) para el panel/respuesta actual — sin esto
 * el `<title>` es siempre el texto fijo "sterminal", indistinguible de una pestaña
 * vacía entre las decenas que suele tener abiertas el owner. Función pura, sin tocar
 * `document` — quien la llama (`App.svelte`) es responsable de aplicarla.
 */
export function titleForKind(
  kind: PanelKind | 'welcome' | 'error',
  response: CommandResponse | null,
): string {
  if (kind === 'summary' && response && 'symbol' in response) {
    return `${response.symbol} · sterminal`;
  }
  const suffix = SYMBOL_TITLE_SUFFIX[kind as PanelKind];
  if (suffix && response && 'symbol' in response) {
    return `${response.symbol} ${suffix} · sterminal`;
  }
  const label = FIXED_TITLE_LABEL[kind as PanelKind];
  if (label) {
    return `${label} · sterminal`;
  }
  return 'sterminal';
}
