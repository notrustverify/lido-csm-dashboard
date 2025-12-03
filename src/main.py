"""Main entry point for the CSM Dashboard application."""

import typer

from .cli.commands import app as cli_app

# Create main app that includes all CLI commands
app = typer.Typer(
    name="csm-dashboard",
    help="Lido CSM Operator Dashboard - Track your validator earnings",
)

# Add all CLI commands from the commands module
app.add_typer(cli_app, name="")


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", help="Host to bind to"),
    port: int = typer.Option(8080, help="Port to bind to"),
    reload: bool = typer.Option(False, "--reload", help="Enable auto-reload for development"),
):
    """Start the web dashboard server."""
    import uvicorn

    from .web.app import create_app

    web_app = create_app()
    uvicorn.run(
        web_app if not reload else "src.web.app:create_app",
        host=host,
        port=port,
        reload=reload,
        factory=reload,
    )


if __name__ == "__main__":
    app()
