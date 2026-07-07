import { describe, expect, it } from 'vitest';
import { ageLabel, formatMoney, formatPercent, formatUsd, signColor } from './format';

describe('formatMoney', () => {
  it('formatea con 2 decimales por defecto', () => {
    expect(formatMoney(1234.5)).toBe('1,234.50');
  });

  it('acepta decimales configurables', () => {
    expect(formatMoney(0.12345, 4)).toBe('0.1235');
  });
});

describe('signColor', () => {
  it('positivo -> pos, negativo -> neg, cero/null/undefined -> dim', () => {
    expect(signColor(5)).toBe('pos');
    expect(signColor(-5)).toBe('neg');
    expect(signColor(0)).toBe('dim');
    expect(signColor(null)).toBe('dim');
    expect(signColor(undefined)).toBe('dim');
  });
});

describe('formatPercent', () => {
  it('antepone + a los positivos, nada a los negativos (el signo ya lo trae toFixed)', () => {
    expect(formatPercent(2.5)).toBe('+2.50%');
    expect(formatPercent(-2.5)).toBe('-2.50%');
    expect(formatPercent(0)).toBe('0.00%');
  });

  it('devuelve — para null/undefined (holdings sin histórico suficiente)', () => {
    expect(formatPercent(null)).toBe('—');
    expect(formatPercent(undefined)).toBe('—');
  });
});

describe('formatUsd', () => {
  it('antepone +/- y $ antes del valor absoluto', () => {
    expect(formatUsd(10)).toBe('+$10.00');
    expect(formatUsd(-10)).toBe('-$10.00');
    expect(formatUsd(0)).toBe('$0.00');
  });

  it('devuelve — para null/undefined', () => {
    expect(formatUsd(null)).toBe('—');
  });
});

describe('ageLabel', () => {
  const now = 1_000_000;

  it('muestra segundos por debajo de 60s', () => {
    expect(ageLabel(now - 22_000, now)).toBe('hace 22s');
    expect(ageLabel(now, now)).toBe('hace 0s');
  });

  it('muestra minutos redondeados a partir de 60s', () => {
    expect(ageLabel(now - 60_000, now)).toBe('hace 1m');
    expect(ageLabel(now - 190_000, now)).toBe('hace 3m');
  });

  it('nunca devuelve un valor negativo si nowMs < lastUpdateMs', () => {
    expect(ageLabel(now + 5000, now)).toBe('hace 0s');
  });
});
