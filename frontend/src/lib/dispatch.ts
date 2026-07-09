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
    default:
      return 'unknown';
  }
}

/** Variante tipada: deriva el `PanelKind` directamente de una `CommandResponse`. */
export function panelForResponse(response: CommandResponse): PanelKind {
  return panelForType(response.type);
}
