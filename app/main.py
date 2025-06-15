from fastapi import FastAPI, status

app = FastAPI(title="MCP Observability API")


@app.get("/health", status_code=status.HTTP_200_OK)
async def health() -> dict[str, str]:
    """Simple health check endpoint."""
    return {"status": "ok"}


def run() -> None:  # pragma: no cover
    """Run the application using uvicorn when executed as a module."""
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":  # pragma: no cover
    run() 