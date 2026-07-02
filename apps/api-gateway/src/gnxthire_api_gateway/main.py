from fastapi import FastAPI

from gnxthire_common.service_info import ServiceInfo, build_service_info


def create_app(service_info: ServiceInfo | None = None) -> FastAPI:
    resolved_service_info = service_info or build_service_info(default_service_name="api-gateway")
    app = FastAPI(
        title="gNxtHire API Gateway",
        version=resolved_service_info.version,
        description="Phase 0 gateway shell. Business routes are intentionally absent.",
    )

    @app.get("/healthz", tags=["platform"])
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/readyz", tags=["platform"])
    def readyz() -> dict[str, str]:
        return {"status": "not_configured", "phase": "0"}

    @app.get("/version", tags=["platform"])
    def version() -> dict[str, str]:
        return {
            "service": resolved_service_info.name,
            "version": resolved_service_info.version,
            "environment": resolved_service_info.environment,
        }

    @app.get("/metrics", tags=["platform"])
    def metrics() -> str:
        return "# TODO(Phase 19 - SRE): Replace with Prometheus metrics exporter.\n"

    return app


app = create_app()
