"""Taxonomía curada sector → materias primas de entrada / sectores de salida
(feat-17, comando `MAP`).

NO es un feed de datos de cadena de suministro real — ninguna API gratuita ya
integrada (yfinance/CoinGecko/frankfurter) expone relaciones reales de
proveedores/clientes por empresa. Es una tabla editorial, curada a mano, de relaciones
económicas ampliamente conocidas y defendibles (ej. "las aerolíneas consumen el
combustible que produce el sector energético"), representadas con ETFs reales y
líquidos como proxy de cada nodo — la cotización de cada proxy sí es un dato de mercado
real y en vivo (vía `Registry.get_quote`); solo la relación input/output en sí es una
elección editorial, no algo sacado de una API.

Solo se mapean los sectores donde la relación materia-prima-de-entrada /
sector-de-salida es económicamente clara y ampliamente aceptada. El resto de sectores
GICS que expone yfinance (`Financial Services`, `Healthcare`, `Real Estate`,
`Consumer Cyclical`, `Communication Services`) se deja sin mapear a propósito, en vez
de forzar una relación débil o discutible — devuelven listas vacías, documentado, no
un error (ver `docs/sys/features/feat-17-value-chain-map.md`).
"""

from __future__ import annotations

# sector (tal cual lo devuelve yfinance `Ticker.info["sector"]`) -> tickers de ETF que
# representan sus insumos típicos.
SECTOR_INPUTS: dict[str, list[str]] = {
    "Energy": ["OIH"],  # servicios/equipos de perforación
    "Basic Materials": ["USO"],  # coste energético de la extracción
    "Technology": ["SOXX", "CPER"],  # semiconductores + cobre
    "Consumer Defensive": ["DBA"],  # materias primas agrícolas
    "Industrials": ["XLB"],  # metales/materiales
    "Utilities": ["USO", "UNG"],  # combustibles fósiles
}

# sector -> tickers de ETF que representan a quién compra típicamente su producción.
SECTOR_OUTPUTS: dict[str, list[str]] = {
    "Energy": ["JETS", "XLI"],  # aerolíneas + industriales consumen energía
    "Basic Materials": ["XLI"],  # industriales consumen metales/materiales
    "Technology": ["XLY"],  # electrónica de consumo -> retail/consumidor
    "Consumer Defensive": ["XRT"],  # distribución minorista
    "Utilities": ["XLI"],  # industriales consumen electricidad
}

# Descripción en prosa de cada proxy ETF — por qué representa ese rol en la cadena de
# valor. Se muestra en la leyenda del panel (`ValueChainPanel.svelte`) porque el
# ticker solo no le dice nada a un usuario que no conozca de memoria qué es "SOXX".
PROXY_DESCRIPTIONS: dict[str, str] = {
    "OIH": "ETF de servicios petroleros — equipos y servicios de perforación",
    "USO": "ETF de petróleo crudo — coste energético de la actividad",
    "SOXX": "ETF de semiconductores — insumo clave de dispositivos electrónicos",
    "CPER": "ETF de cobre — materia prima de componentes y cableado electrónico",
    "DBA": "ETF de materias primas agrícolas — insumo de alimentos y bebidas",
    "XLB": "ETF del sector de materiales — metales y materiales industriales",
    "UNG": "ETF de gas natural — combustible fósil",
    "JETS": "ETF de aerolíneas — grandes consumidoras del combustible del sector",
    "XLI": "ETF del sector industrial — consume metales, materiales y energía",
    "XLY": "ETF de consumo discrecional — venta de electrónica/bienes de consumo",
    "XRT": "ETF de venta minorista — distribución de productos de consumo",
}


def describe_proxy(symbol: str) -> str:
    """Descripción en prosa de `symbol`, o un genérico si no está en
    `PROXY_DESCRIPTIONS` (no debería pasar para los símbolos de `SECTOR_INPUTS`/
    `SECTOR_OUTPUTS`, pero degrada sin reventar si la tabla se queda desactualizada)."""
    return PROXY_DESCRIPTIONS.get(symbol, f"proxy de la cadena de valor ({symbol})")


def value_chain_symbols(sector: str | None) -> tuple[list[str], list[str]]:
    """`(tickers_de_entrada, tickers_de_salida)` para `sector`.

    `([], [])` si `sector` es `None` (crypto/fx, sin taxonomía GICS) o si el sector no
    tiene mapeo curado definido (ver docstring del módulo) — ambos casos son
    respuestas documentadas, no errores.
    """
    if sector is None:
        return [], []
    return SECTOR_INPUTS.get(sector, []), SECTOR_OUTPUTS.get(sector, [])
