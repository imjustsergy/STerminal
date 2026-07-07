/**
 * Historial de comandos en memoria (feat-8) — módulo puro, sin DOM, para que Vitest lo
 * teste sin montar componentes. ↑ recorre hacia atrás, ↓ hacia adelante; en el extremo
 * más reciente, ↓ vacía el input (mismo comportamiento que el prototipo
 * `sterminal.dc.html`).
 */
export class CommandHistory {
  private entries: string[] = [];
  /** Índice del historial "seleccionado" actualmente; `entries.length` = posición vacía. */
  private cursor: number;

  constructor() {
    this.cursor = this.entries.length;
  }

  /** Añade un comando ejecutado y resetea el cursor a la posición "vacío". */
  push(command: string): void {
    if (!command.trim()) {
      return;
    }
    this.entries.push(command);
    this.cursor = this.entries.length;
  }

  /** Recorre hacia atrás (más antiguo). Devuelve `null` si ya no hay historial previo. */
  prev(): string | null {
    if (this.entries.length === 0 || this.cursor <= 0) {
      return null;
    }
    this.cursor -= 1;
    return this.entries[this.cursor];
  }

  /**
   * Recorre hacia adelante (más reciente). Devuelve `""` al llegar/superar el final
   * (posición "vacío"), o `null` si ya estaba en el final (nada que hacer).
   */
  next(): string | null {
    if (this.cursor >= this.entries.length) {
      return null;
    }
    this.cursor += 1;
    if (this.cursor >= this.entries.length) {
      return '';
    }
    return this.entries[this.cursor];
  }

  /** Copia de las entradas registradas (solo lectura, para tests/inspección). */
  toArray(): string[] {
    return [...this.entries];
  }
}
