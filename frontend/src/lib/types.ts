// Interfaces TS espejo de los tipos de dominio del backend (backend/app/models.py,
// backend/app/portfolio.py). Escritas a mano (sin generación automática de un schema
// OpenAPI) — YAGNI para el alcance de las features 8-11, ver plan-8-frontend-skeleton.md.

export interface SymbolMatch {
  symbol: string;
  name: string;
  asset_class: string;
}

export interface Quote {
  symbol: string;
  price: number;
  currency: string;
  change: number;
  change_percent: number;
  timestamp: string;
}

export interface Candle {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface Holding {
  symbol: string;
  asset_class: string;
  quantity: number;
  avg_cost_price: number;
  current_price: number;
  market_value: number;
  cost_basis: number;
  pnl: number;
  pnl_percent: number;
  allocation_percent: number;
  previous_close: number | null;
  daily_pnl: number | null;
  daily_pnl_percent: number | null;
}

export interface PortfolioSummary {
  total_market_value: number;
  total_cost_basis: number;
  total_pnl: number;
  total_pnl_percent: number;
  total_daily_pnl: number;
  holdings_count: number;
}

export interface NewsItem {
  title: string;
  url: string;
  source: string;
  published_at: string;
}

export interface Financials {
  symbol: string;
  market_cap: number | null;
  pe_ratio: number | null;
  eps: number | null;
  dividend_yield: number | null;
  week52_high: number | null;
  week52_low: number | null;
  beta: number | null;
  sector: string | null;
  industry: string | null;
}

export interface HelpEntry {
  usage: string;
  type: string;
  description: string;
}

export interface SummaryResponse {
  type: 'SUMMARY';
  symbol: string;
  asset_class: string;
  quote: Quote;
}

export interface GraphPriceResponse {
  type: 'GRAPH_PRICE';
  symbol: string;
  asset_class: string;
  candles: Candle[];
}

export interface PortfolioResponse {
  type: 'PORTFOLIO';
  holdings: Holding[];
  summary: PortfolioSummary;
}

export interface HelpResponse {
  type: 'HELP';
  commands: HelpEntry[];
}

/** feat-12: `items` puede ser `[]` para crypto/fx — no es un error, es el dato real. */
export interface NewsResponse {
  type: 'NEWS';
  symbol: string;
  asset_class: string;
  items: NewsItem[];
}

/** feat-14: `financials` con todos los campos a `null` para crypto/fx — no es un
 * error, es el dato real (solo equity tiene ratios financieros). */
export interface FinancialsResponse {
  type: 'FA';
  symbol: string;
  asset_class: string;
  financials: Financials;
}

/** Unión discriminada de todo lo que `POST /command` puede devolver con 200. */
export type CommandResponse =
  | SummaryResponse
  | GraphPriceResponse
  | PortfolioResponse
  | HelpResponse
  | NewsResponse
  | FinancialsResponse;

/** Detalle de error tal cual lo construye `command_router.py::_data_error_detail`. */
export interface CommandErrorDetail {
  message: string;
  suggestions?: string[];
}

/** Mensaje `{"quotes": [...]}` o `{"error": ...}` de `stream_router.py`. */
export type StreamQuoteEntry = Quote | { symbol: string; error: string };
