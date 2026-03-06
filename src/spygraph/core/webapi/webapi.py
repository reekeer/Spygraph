import json
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI

from spygraph.core.webapi.middleware import SecurityHeadersMiddleware, TelemetryMiddleware, api_security_headers
from spygraph.utils import random_token


class WebApi(FastAPI):
    def __init__(self, config, **kwargs):
        self.api_token = random_token()
        self.silent_start = config.get("silent_start", False) if isinstance(config, dict) else False

        forced_uuid = config.get("forced_uuid") if isinstance(config, dict) else None
        self.UUID: str = forced_uuid if isinstance(forced_uuid, str) else str(uuid.uuid4())

        self.ipwhois: bool = bool(config.get("ipwhois")) if isinstance(config, dict) else False

        self.API_BASE_URL = "/api/v1/pictures"

        @asynccontextmanager
        async def lifespan(app):
            if not self.silent_start:
                status = {"status": "started", "api_token": self.api_token, "base_url": self.API_BASE_URL, "uuid": f"{self.UUID}"}
                print(json.dumps(status))

            yield

            if not self.silent_start:
                status = {"status": "stopped"}
                print(json.dumps(status))

        try:
            super().__init__(
                docs_url=f"/{self.api_token}/docs",
                redoc_url=f"/{self.api_token}/redoc",
                root_path=self.API_BASE_URL,
                lifespan=lifespan,
                **kwargs,
            )

            self.add_middleware(TelemetryMiddleware, uuid=self.UUID, ipwhois=self.ipwhois)

            self.add_middleware(SecurityHeadersMiddleware, headers=api_security_headers())

        except Exception:
            raise
