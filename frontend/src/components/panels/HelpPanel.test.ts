import { afterEach, describe, expect, it } from 'vitest';
import { cleanup, render } from '@testing-library/svelte';
import HelpPanel from './HelpPanel.svelte';
import type { HelpResponse } from '../../lib/types';

afterEach(() => {
  cleanup();
});

function baseResponse(): HelpResponse {
  return {
    type: 'HELP',
    commands: [
      { usage: '<SÍMBOLO>', type: 'SUMMARY', description: 'Resumen de activo.' },
      { usage: 'MOVERS', type: 'MOVERS', description: 'Mayores subidas/bajadas del día (fuera de alcance del MVP).' },
      { usage: 'HELP', type: 'HELP', description: 'Esta lista de comandos.' },
    ],
  };
}

describe('HelpPanel', () => {
  it('renderiza cada comando con su descripción', () => {
    const { getByText } = render(HelpPanel, { response: baseResponse() });
    expect(getByText('<SÍMBOLO>')).toBeInTheDocument();
    expect(getByText('Resumen de activo.')).toBeInTheDocument();
  });

  it('feat-18: distingue visualmente MOVERS como no disponible', () => {
    const { getByText } = render(HelpPanel, { response: baseResponse() });

    const workingUsage = getByText('HELP');
    const unavailableUsage = getByText('MOVERS');

    expect(workingUsage.classList.contains('acc')).toBe(true);
    expect(unavailableUsage.classList.contains('acc')).toBe(false);
    expect(getByText('· no disponible todavía')).toBeInTheDocument();
  });
});
