from pathlib import Path

import aiohttp
from google_health_api.api import GoogleHealthApi
from google_health_api.auth import AbstractAuth
from google_health_api.cli.auth import CredentialsAuth, EnvAuth, load_credentials_or_env

from src.settings import GoogleHealthConfig, settings


def _resolve(path: Path) -> Path:
    return path if path.is_absolute() else settings.project_root / path


def build_health_auth(session: aiohttp.ClientSession, config: GoogleHealthConfig) -> AbstractAuth:
    """Build an auth wrapper from an existing token.json (or GOOGLE_HEALTH_CLI_TOKEN env var).

    Does not perform the interactive OAuth consent flow - that must be run once
    beforehand (see notebooks/fitbit_analysis.ipynb) to produce a token.json.
    """
    token_file = _resolve(config.TOKEN_FILE)
    result = load_credentials_or_env(token_file=str(token_file))
    if result is None:
        raise RuntimeError(
            f"No Google Health credentials found at {token_file}. "
            "Run the OAuth login flow once (see notebooks/fitbit_analysis.ipynb) "
            "before starting the server."
        )

    kind, value = result
    if kind == "env":
        return EnvAuth(session, value)
    return CredentialsAuth(session, value, token_file=str(token_file))


def build_health_api(session: aiohttp.ClientSession, config: GoogleHealthConfig) -> GoogleHealthApi:
    return GoogleHealthApi(build_health_auth(session, config))
