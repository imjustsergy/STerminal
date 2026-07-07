"""Utilidades compartidas por los providers concretos (feature 2).

Ver docs/plans/plan-2-providers-base.md, sección "Mapeo de resolution→rango temporal".
"""

_VALID_RESOLUTIONS = {"1D", "1W", "1M", "1Y"}


def normalize_resolution(resolution: str) -> str:
    """Normaliza `resolution` a uno de `1D`/`1W`/`1M`/`1Y`.

    Cualquier valor no reconocido cae a `"1D"` por defecto en vez de lanzar una
    excepción, para no romper el panel ante una entrada inesperada (spec.md sección 8:
    "Backend degradado → sirve lo último conocido en lugar de fallar").
    """
    candidate = (resolution or "").strip().upper()
    return candidate if candidate in _VALID_RESOLUTIONS else "1D"
