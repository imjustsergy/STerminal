import { afterEach, describe, expect, it, vi } from 'vitest';
import { cleanup, render } from '@testing-library/svelte';
import PortfolioPanel from './PortfolioPanel.svelte';
import type { PortfolioResponse } from '../../lib/types';

afterEach(() => {
  cleanup();
});

function baseResponse(): PortfolioResponse {
  return {
    type: 'PORTFOLIO',
    holdings: [
      {
        symbol: 'AAPL',
        asset_class: 'equity',
        quantity: 10,
        avg_cost_price: 150.0,
        current_price: 312.19,
        market_value: 3121.9,
        cost_basis: 1500.0,
        pnl: 1621.9,
        pnl_percent: 108.13,
        allocation_percent: 100.0,
        previous_close: 310.0,
        daily_pnl: 21.9,
        daily_pnl_percent: 0.7,
      },
    ],
    summary: {
      total_market_value: 3121.9,
      total_cost_basis: 1500.0,
      total_pnl: 1621.9,
      total_pnl_percent: 108.13,
      total_daily_pnl: 21.9,
      holdings_count: 1,
    },
  };
}

describe('PortfolioPanel', () => {
  it('renderiza las posiciones con sus totales', () => {
    const { getByText } = render(PortfolioPanel, { response: baseResponse(), onNavigate: vi.fn() });
    expect(getByText('AAPL')).toBeInTheDocument();
  });

  it('feat-18: clicar el símbolo de una posición navega a ese símbolo', () => {
    const onNavigate = vi.fn();
    const { getByText } = render(PortfolioPanel, { response: baseResponse(), onNavigate });

    getByText('AAPL').click();
    expect(onNavigate).toHaveBeenCalledWith('AAPL');
  });

  it('feat-19: el footer invita a usar PORT ADD, ahora que sí funciona de verdad', () => {
    const { getByText } = render(PortfolioPanel, { response: baseResponse(), onNavigate: vi.fn() });
    expect(getByText(/PORT ADD AAPL 10 150.50/)).toBeInTheDocument();
  });
});
