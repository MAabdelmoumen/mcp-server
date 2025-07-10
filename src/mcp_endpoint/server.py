from mcp.server.fastmcp import FastMCP
import os
import requests
from authentication import HttpClient


mcp = FastMCP(name="OICM MCP", stateless_http=True)


def get_authenticated_client():
    """
    Get an authenticated HTTP client with all required environment variables.
    Returns a tuple of (client, workspace_id) or raises an exception with error details.
    """
    # Get all parameters from environment variables, no defaults
    api_url = os.environ.get("API_URL")
    auth_url = os.environ.get("AUTH_URL")
    username = os.environ.get("API_USERNAME")
    password = os.environ.get("API_PASSWORD")
    tenant_id = os.environ.get("TENANT_ID")
    workspace_id = os.environ.get("WORKSPACE_ID")

    # Validate required parameters
    missing = []
    if not api_url:
        missing.append("API_URL")
    if not auth_url:
        missing.append("AUTH_URL")
    if not username:
        missing.append("API_USERNAME")
    if not password:
        missing.append("API_PASSWORD")
    if not tenant_id:
        missing.append("TENANT_ID")
    if not workspace_id:
        missing.append("WORKSPACE_ID")
    if missing:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing)}"
        )

    # Initialize HTTP client and authenticate
    client = HttpClient(
        api_url=api_url,
        auth_url=auth_url,
        username=username,
        password=password,
        tenant_id=tenant_id,
    )

    # Authenticate to get token
    client.authenticate()

    return client, workspace_id


@mcp.tool()
async def get_deployments():
    try:
        # Get authenticated client and workspace_id
        client, workspace_id = get_authenticated_client()

        # Call the deployments endpoint
        deployments_url = f"/workspaces/{workspace_id}/deployments"

        # Use requests directly with the same pattern as HttpClient
        response = requests.get(
            client.get_api_url() + deployments_url,
            headers={"Authorization": f"Bearer {client.get_token()}"},
        )

        if response.status_code == 200:
            return response.text
        else:
            return f"Error: Failed to get deployments. Status: {response.status_code}, Response: {response.text}"

    except ValueError as e:
        return f"Error: {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"
