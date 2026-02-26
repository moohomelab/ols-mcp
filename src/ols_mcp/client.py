"""HTTP client for OLS API communication."""

import os
from pathlib import Path

import httpx
from dotenv import load_dotenv

from .models import LLMRequest, LLMResponse

# Load environment variables from .env file
load_dotenv()

# In-cluster SA token path
SA_TOKEN_PATH = Path("/var/run/secrets/kubernetes.io/serviceaccount/token")

# Default in-cluster OLS service URL (falls back to localhost for local dev)
_DEFAULT_OLS_URL = (
    "https://lightspeed-app-server.openshift-lightspeed.svc.cluster.local:8443"
    if SA_TOKEN_PATH.exists()
    else "http://localhost:8080"
)


def _get_api_token() -> str | None:
    """Get API token from env var, falling back to SA token on cluster."""
    token = os.getenv("OLS_API_TOKEN")
    if token:
        return token
    if SA_TOKEN_PATH.exists():
        return SA_TOKEN_PATH.read_text().strip()
    return None


def _get_verify_ssl() -> bool | str:
    """Get SSL verification setting.

    Supports:
      - "true" / "false" for boolean toggle
      - A file path to a CA cert bundle
    """
    value = os.getenv("OLS_VERIFY_SSL", "true")
    if value.lower() == "false":
        return False
    if value.lower() == "true":
        return True
    # Treat as a path to a CA cert file
    return value


async def query_openshift_lightspeed(request: LLMRequest) -> LLMResponse:
    """Query the OpenShift LightSpeed API."""
    # Get configuration from environment
    api_url = os.getenv("OLS_API_URL", _DEFAULT_OLS_URL)
    api_token = _get_api_token()
    timeout = float(os.getenv("OLS_TIMEOUT", "30.0"))
    verify_ssl = _get_verify_ssl()

    # Build request URL
    url = f"{api_url.rstrip('/')}/v1/query"

    # Prepare headers
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    if api_token:
        headers["Authorization"] = f"Bearer {api_token}"

    # Prepare request data
    data = {
        "query": request.query
    }

    if request.conversation_id:
        data["conversation_id"] = request.conversation_id

    # Make HTTP request
    async with httpx.AsyncClient(timeout=timeout, verify=verify_ssl) as client:
        try:
            response = await client.post(url, json=data, headers=headers)
            response.raise_for_status()

            # Parse response
            response_data = response.json()

            # Return LLMResponse
            return LLMResponse(
                response=response_data.get("response", "No response received"),
                conversation_id=response_data.get("conversation_id", request.conversation_id)
            )

        except httpx.HTTPStatusError as e:
            raise Exception(f"HTTP error {e.response.status_code}: {e.response.text}")
        except httpx.RequestError as e:
            raise Exception(f"Request error: {str(e)}")
        except Exception as e:
            raise Exception(f"Unexpected error: {str(e)}")
