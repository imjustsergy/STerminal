"""App FastAPI mínima del backend de sterminal.

Solo expone un health-check. Los routers de negocio (feature 5), el parser
de comandos (feature 4) y el WebSocket `/stream` (feature 7) se añaden en
features posteriores.
"""

from fastapi import FastAPI

app = FastAPI(title="sterminal")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
