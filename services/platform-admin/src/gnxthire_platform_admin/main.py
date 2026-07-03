from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from gnxthire_common.errors import AppError, build_error_envelope

from gnxthire_platform_admin.routes import router


def create_app() -> FastAPI:
    app = FastAPI(
        title="gNxtHire Platform Admin Service",
        version="0.0.0-phase4",
        description="Internal platform-admin control plane APIs.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5174",
            "http://127.0.0.1:5174",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(AppError)
    def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        request_id = request.headers.get("x-request-id", "missing-request-id")
        envelope = build_error_envelope(
            request_id=request_id,
            code=exc.code,
            message=exc.safe_detail,
            field_errors=exc.field_errors,
        )
        return JSONResponse(status_code=exc.status_code, content=envelope.model_dump(mode="json"))

    app.include_router(router)
    return app


app = create_app()

