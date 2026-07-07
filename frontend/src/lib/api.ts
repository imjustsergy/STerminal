import { API_BASE_URL } from './config';
import type { CommandErrorDetail, CommandResponse } from './types';

/**
 * Error tipado lanzado por `postCommand` ante cualquier fallo: respuesta 4xx/5xx del
 * backend (con `detail` ya parseado) o fallo de red (mensaje genérico, sin `detail`).
 * `PanelRouter`/`App.svelte` lo capturan para renderizar `ErrorPanel` (feat-8/feat-11).
 */
export class CommandApiError extends Error {
  readonly status: number | null;
  readonly detail: CommandErrorDetail | null;

  constructor(message: string, status: number | null, detail: CommandErrorDetail | null) {
    super(message);
    this.name = 'CommandApiError';
    this.status = status;
    this.detail = detail;
  }
}

function normalizeDetail(rawDetail: unknown): CommandErrorDetail {
  if (typeof rawDetail === 'string') {
    return { message: rawDetail };
  }
  if (
    rawDetail &&
    typeof rawDetail === 'object' &&
    'message' in rawDetail &&
    typeof (rawDetail as Record<string, unknown>).message === 'string'
  ) {
    const detail = rawDetail as { message: string; suggestions?: unknown };
    const suggestions = Array.isArray(detail.suggestions)
      ? detail.suggestions.filter((s): s is string => typeof s === 'string')
      : undefined;
    return suggestions ? { message: detail.message, suggestions } : { message: detail.message };
  }
  return { message: 'respuesta de error del backend con formato inesperado' };
}

export interface PostCommandOptions {
  /** Resolución de histórico opcional para `GRAPH_PRICE` (feat-9): "1D"/"1W"/"1M"/"1Y". */
  resolution?: string;
}

/**
 * `POST {API_BASE_URL}/command` con `{"input": raw}` (mismo formato que consume
 * `command_router.py`, feat-5). Lanza `CommandApiError` ante cualquier fallo — nunca
 * devuelve una respuesta a medias silenciosamente (spec.md sección 8: nunca pantalla en
 * blanco).
 */
export async function postCommand(
  raw: string,
  options: PostCommandOptions = {},
): Promise<CommandResponse> {
  const body: Record<string, unknown> = { input: raw };
  if (options.resolution) {
    body.resolution = options.resolution;
  }

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/command`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
  } catch {
    throw new CommandApiError('no se pudo contactar con el backend', null, null);
  }

  let payload: unknown = null;
  try {
    payload = await response.json();
  } catch {
    payload = null;
  }

  if (!response.ok) {
    const detail = normalizeDetail((payload as { detail?: unknown } | null)?.detail);
    throw new CommandApiError(detail.message, response.status, detail);
  }

  return payload as CommandResponse;
}
