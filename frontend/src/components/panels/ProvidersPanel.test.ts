import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, render } from '@testing-library/svelte';
import { tick } from 'svelte';
import ProvidersPanel from './ProvidersPanel.svelte';
import type { ProvidersResponse } from '../../lib/types';

vi.mock('../../lib/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../../lib/api')>();
  return {
    ...actual,
    postCommand: vi.fn(),
  };
});

import { postCommand } from '../../lib/api';

afterEach(() => {
  cleanup();
});

function baseResponse(): ProvidersResponse {
  return {
    type: 'PROVIDERS',
    providers: {
      equity: [
        { name: 'default', active: true },
        { name: 'alphavantage', active: false },
      ],
      crypto: [{ name: 'default', active: true }],
      fx: [{ name: 'default', active: true }],
    },
  };
}

describe('ProvidersPanel', () => {
  beforeEach(() => {
    vi.mocked(postCommand).mockReset();
  });

  it('lista los proveedores de las tres clases de activo con su estado', () => {
    const { getByText, getAllByText } = render(ProvidersPanel, { response: baseResponse() });
    expect(getByText('alphavantage')).toBeInTheDocument();
    expect(getAllByText('● ACTIVO').length).toBeGreaterThanOrEqual(3);
  });

  it('un proveedor inactivo muestra un botón "activar", el activo no', () => {
    const { getAllByRole, getByText } = render(ProvidersPanel, { response: baseResponse() });
    expect(getByText('inactivo')).toBeInTheDocument();
    const buttons = getAllByRole('button', { name: 'activar' });
    expect(buttons).toHaveLength(1);
  });

  it('clicar "activar" envía PROVIDERS SET y refresca el estado con la respuesta', async () => {
    vi.mocked(postCommand).mockResolvedValue({
      type: 'PROVIDERS',
      providers: {
        equity: [
          { name: 'default', active: false },
          { name: 'alphavantage', active: true },
        ],
        crypto: [{ name: 'default', active: true }],
        fx: [{ name: 'default', active: true }],
      },
    });
    const { getByRole, getByText } = render(ProvidersPanel, { response: baseResponse() });

    getByRole('button', { name: 'activar' }).click();
    await tick();
    await tick();

    expect(postCommand).toHaveBeenCalledWith('PROVIDERS SET equity alphavantage');
    expect(getByText('inactivo')).toBeInTheDocument(); // ahora "default" es el inactivo
  });

  it('un fallo de postCommand no revienta el panel — el estado no cambia', async () => {
    vi.mocked(postCommand).mockRejectedValue(new Error('fallo simulado'));
    const { getByRole, getByText } = render(ProvidersPanel, { response: baseResponse() });

    getByRole('button', { name: 'activar' }).click();
    await tick();
    await tick();

    expect(getByText('alphavantage')).toBeInTheDocument();
    expect(getByText('inactivo')).toBeInTheDocument();
  });
});
