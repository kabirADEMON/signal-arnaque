import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import get_settings
from .routers import agents, public

app = FastAPI(title="Signal Arnaque", version="1.0.0", docs_url="/api/docs", redoc_url=None,
              openapi_url="/api/openapi.json")
app.include_router(public)
app.include_router(agents)

if get_settings().jwt_secret.startswith("dev-uniquement"):
    logging.getLogger("uvicorn.error").warning("JWT_SECRET n'est pas défini : clé de développement utilisée. À ne jamais faire en production.")

SECURITY_HEADERS = {
    "Content-Security-Policy": (
        "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; "
        "font-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'"
    ),
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "same-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
}


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    path = request.url.path
    # La documentation interactive charge ses scripts depuis un CDN : pas de CSP stricte sur elle.
    headers = {k: v for k, v in SECURITY_HEADERS.items() if not (path.startswith("/api/docs") and k == "Content-Security-Policy")}
    response.headers.update(headers)
    if path.startswith("/api/"):
        response.headers.setdefault("Cache-Control", "no-store")
    return response


# Le front compilé est servi par la même application : un seul service à déployer.
dist = Path(get_settings().frontend_dist).resolve()
if dist.is_dir():
    app.mount("/assets", StaticFiles(directory=dist / "assets"), name="assets")

    @app.get("/{chemin:path}", include_in_schema=False)
    def spa(chemin: str):
        if chemin.startswith("api/"):
            raise HTTPException(404, "Introuvable")
        fichier = (dist / chemin).resolve()
        if chemin and fichier.is_file() and dist in fichier.parents:
            return FileResponse(fichier)
        return FileResponse(dist / "index.html")
