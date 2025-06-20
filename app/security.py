import os

from fastapi import Header, HTTPException, status


async def verify_bearer_token(authorization: str | None = Header(default=None)) -> None:
    """Validate the Authorization header against the expected token.

    The expected token is read from the ``MCP_TOKEN`` environment variable. All
    endpoints that include this dependency will return *401 Unauthorized* if the
    header is missing, malformed, or the token value does not match.
    """

    expected_token = os.getenv("MCP_TOKEN")

    # If no expected token is configured, always reject the request. This avoids
    # accidentally deploying an unprotected service.
    if not expected_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )

    if authorization is None or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )

    provided_token = authorization.split(" ", 1)[1]
    if provided_token != expected_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )
