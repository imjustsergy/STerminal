import { describe, expect, it } from 'vitest';
import { CommandHistory } from './commandHistory';

describe('CommandHistory', () => {
  it('prev/next devuelven null cuando no hay historial', () => {
    const history = new CommandHistory();
    expect(history.prev()).toBeNull();
    expect(history.next()).toBeNull();
  });

  it('push añade al historial y prev() recorre hacia atrás', () => {
    const history = new CommandHistory();
    history.push('AAPL');
    history.push('BTC GP');
    history.push('PORT');

    expect(history.prev()).toBe('PORT');
    expect(history.prev()).toBe('BTC GP');
    expect(history.prev()).toBe('AAPL');
    // Ya en el más antiguo, prev() no puede ir más atrás.
    expect(history.prev()).toBeNull();
  });

  it('next() recorre hacia adelante y vacía el input en el extremo más reciente', () => {
    const history = new CommandHistory();
    history.push('AAPL');
    history.push('BTC GP');

    history.prev(); // 'BTC GP'
    history.prev(); // 'AAPL'
    expect(history.next()).toBe('BTC GP');
    expect(history.next()).toBe(''); // posición "vacío"
    // Ya en el extremo, next() no hace nada más (no hay "más adelante" que vacío).
    expect(history.next()).toBeNull();
  });

  it('push tras navegar el historial resetea el cursor al final', () => {
    const history = new CommandHistory();
    history.push('AAPL');
    history.push('BTC GP');
    history.prev();
    history.prev();
    history.push('PORT');

    expect(history.prev()).toBe('PORT');
  });

  it('ignora push de comandos vacíos o solo espacios', () => {
    const history = new CommandHistory();
    history.push('   ');
    history.push('');
    expect(history.toArray()).toEqual([]);
  });

  it('toArray devuelve una copia, no la referencia interna', () => {
    const history = new CommandHistory();
    history.push('AAPL');
    const arr = history.toArray();
    arr.push('MUTATED');
    expect(history.toArray()).toEqual(['AAPL']);
  });
});
