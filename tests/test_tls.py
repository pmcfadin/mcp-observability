import asyncio
import os
import random
import ssl
import subprocess
import sys
import time
from pathlib import Path

import pytest
import trustme
from httpx import AsyncClient

TOKEN = "secret"


async def _wait_for_server(port: int, timeout: float = 5.0) -> None:
    """Poll the /health endpoint until the server responds or timeout."""
    start = time.perf_counter()
    while time.perf_counter() - start < timeout:
        try:
            async with AsyncClient(verify=False) as ac:  # disable cert check in poll
                await ac.get(f"https://127.0.0.1:{port}/health", timeout=0.5)
            return
        except Exception:
            await asyncio.sleep(0.1)
    raise RuntimeError("Server did not start in time")


@pytest.mark.asyncio
async def test_tls_termination_success(tmp_path: Path) -> None:
    """mcp-server should accept HTTPS connections with valid bearer token."""

    ca = trustme.CA()
    server_cert = ca.issue_cert("localhost")

    key_file = tmp_path / "tls.key"
    cert_file = tmp_path / "tls.crt"
    ca_cert_file = tmp_path / "ca.crt"

    server_cert.private_key_pem.write_to_path(key_file)
    server_cert.cert_chain_pems[0].write_to_path(cert_file)
    ca.cert_pem.write_to_path(ca_cert_file)

    port = random.randint(9000, 9999)

    env = os.environ.copy()
    env["MCP_TOKEN"] = TOKEN

    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "0.0.0.0",
            "--port",
            str(port),
            "--ssl-keyfile",
            str(key_file),
            "--ssl-certfile",
            str(cert_file),
        ],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        await _wait_for_server(port)

        ssl_context = ssl.create_default_context(cafile=str(ca_cert_file))

        async with AsyncClient(verify=ssl_context) as ac:
            response = await ac.get(
                f"https://localhost:{port}/health",
                headers={"Authorization": f"Bearer {TOKEN}"},
            )
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
    finally:
        proc.terminate()
        proc.wait()


# ---------------------------------------------------------------------------
# Mutual TLS
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_mutual_tls_success(tmp_path: Path) -> None:
    """Server should require and validate client certificate when CA is provided."""

    ca = trustme.CA()
    server_cert = ca.issue_cert("localhost")
    client_cert = ca.issue_cert("client")

    # Write server key/cert and CA
    key_file = tmp_path / "server.key"
    cert_file = tmp_path / "server.crt"
    ca_cert_file = tmp_path / "ca.crt"

    server_cert.private_key_pem.write_to_path(key_file)
    server_cert.cert_chain_pems[0].write_to_path(cert_file)
    ca.cert_pem.write_to_path(ca_cert_file)

    # Write client key/cert
    client_key_file = tmp_path / "client.key"
    client_cert_file = tmp_path / "client.crt"

    client_cert.private_key_pem.write_to_path(client_key_file)
    client_cert.cert_chain_pems[0].write_to_path(client_cert_file)

    port = random.randint(9000, 9999)

    env = os.environ.copy()
    env["MCP_TOKEN"] = TOKEN

    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "0.0.0.0",
            "--port",
            str(port),
            "--ssl-keyfile",
            str(key_file),
            "--ssl-certfile",
            str(cert_file),
            "--ssl-ca-certs",
            str(ca_cert_file),
        ],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        await _wait_for_server(port)

        ssl_context = ssl.create_default_context(cafile=str(ca_cert_file))
        # Present client cert for mutual TLS
        ssl_context.load_cert_chain(
            certfile=str(client_cert_file), keyfile=str(client_key_file)
        )

        async with AsyncClient(verify=ssl_context) as ac:
            response = await ac.get(
                f"https://localhost:{port}/health",
                headers={"Authorization": f"Bearer {TOKEN}"},
            )

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
    finally:
        proc.terminate()
        proc.wait()
