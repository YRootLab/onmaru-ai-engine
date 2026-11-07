import asyncio
from typing import Any

from httpx import ASGITransport, AsyncClient, Response

from onmaru_ai.config.secrets import FakeSecretProvider
from onmaru_ai.main import create_app


async def request(path: str) -> Response:
    transport = ASGITransport(app=create_app(secret_provider=FakeSecretProvider()))
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.get(path)


def test_health_reports_process_is_alive() -> None:
    response = asyncio.run(request("/health"))

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_reports_service_can_accept_requests() -> None:
    response = asyncio.run(request("/ready"))

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_readiness_fails_when_required_secret_missing() -> None:
    class MissingTokenProvider(FakeSecretProvider):
        def get(self, name: str) -> Any:
            if name == "internal-ai.service-token":
                raise RuntimeError(f"missing: {name}")
            return super().get(name)

    transport = ASGITransport(app=create_app(secret_provider=MissingTokenProvider()))

    async def check() -> Response:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.get("/ready")

    response = asyncio.run(check())
    assert response.status_code == 503
    assert response.json()["status"] == "not_ready"
