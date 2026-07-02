from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from gnxthire_common.errors import AppError, build_error_envelope

from gnxthire_identity.api.platform_routes import router as platform_admin_router
from gnxthire_identity.api.platform_user_routes import router as platform_users_router
from gnxthire_identity.api.tenant_routes import router as tenant_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="gNxtHire Identity Service",
        version="0.0.0-phase2",
        description="Identity service for tenant-user and platform-admin authentication.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
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

    app.include_router(tenant_router)
    app.include_router(platform_admin_router)
    app.include_router(platform_users_router)
    return app


app = create_app()
