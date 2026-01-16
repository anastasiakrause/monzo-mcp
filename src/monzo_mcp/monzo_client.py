"""Async client for the Monzo API."""

import os
from typing import Any

import httpx
from dotenv import load_dotenv

from .models import MonzoAPIError


class MonzoClient:
    """Async client for Monzo banking API.

    Read-only operations only - no money movement.
    """

    BASE_URL = "https://api.monzo.com"

    def __init__(
        self,
        access_token: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
        refresh_token: str | None = None,
    ):
        load_dotenv()

        self.access_token = access_token or os.getenv("MONZO_ACCESS_TOKEN")
        self.client_id = client_id or os.getenv("MONZO_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("MONZO_CLIENT_SECRET")
        self.refresh_token = refresh_token or os.getenv("MONZO_REFRESH_TOKEN")

        if not self.access_token:
            raise ValueError(
                "No access token provided. Run scripts/auth.py to authenticate."
            )

        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                headers={"Authorization": f"Bearer {self.access_token}"},
                timeout=30.0,
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make an authenticated request to the Monzo API."""
        client = await self._get_client()

        response = await client.request(
            method=method,
            url=endpoint,
            params=params,
            data=data,
        )

        if response.status_code == 401:
            # Token expired - try refresh if we have credentials
            if self.refresh_token and self.client_id and self.client_secret:
                await self._refresh_access_token()
                # Retry the request with new token
                client = await self._get_client()
                response = await client.request(
                    method=method,
                    url=endpoint,
                    params=params,
                    data=data,
                )
            else:
                raise MonzoAPIError(401, "Access token expired. Re-run scripts/auth.py")

        if response.status_code == 429:
            raise MonzoAPIError(429, "Rate limited. Please wait before retrying.")

        if not response.is_success:
            try:
                error_data = response.json()
                message = error_data.get("message", response.text)
            except Exception:
                message = response.text
            raise MonzoAPIError(response.status_code, message)

        return response.json()

    async def _refresh_access_token(self) -> None:
        """Refresh the access token using the refresh token."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/oauth2/token",
                data={
                    "grant_type": "refresh_token",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "refresh_token": self.refresh_token,
                },
            )

        if not response.is_success:
            raise MonzoAPIError(
                response.status_code,
                "Failed to refresh token. Re-run scripts/auth.py",
            )

        tokens = response.json()
        self.access_token = tokens["access_token"]
        self.refresh_token = tokens.get("refresh_token", self.refresh_token)

        # Update the client with new token
        if self._client and not self._client.is_closed:
            await self._client.aclose()
        self._client = None

    # ==================== Account Operations ====================

    async def list_accounts(self) -> list[dict[str, Any]]:
        """List all accounts for the authenticated user."""
        result = await self._request("GET", "/accounts")
        return result.get("accounts", [])

    async def get_balance(self, account_id: str) -> dict[str, Any]:
        """Get the balance for a specific account."""
        return await self._request("GET", "/balance", params={"account_id": account_id})

    # ==================== Transaction Operations ====================

    async def list_transactions(
        self,
        account_id: str,
        limit: int = 100,
        since: str | None = None,
        before: str | None = None,
    ) -> list[dict[str, Any]]:
        """List transactions for an account.

        Note: Due to SCA, only 90 days of history available after 5 mins.
        """
        params: dict[str, Any] = {
            "account_id": account_id,
            "limit": min(limit, 100),  # API max is 100
            "expand[]": "merchant",  # Include merchant details
        }
        if since:
            params["since"] = since
        if before:
            params["before"] = before

        result = await self._request("GET", "/transactions", params=params)
        return result.get("transactions", [])

    async def get_transaction(self, transaction_id: str) -> dict[str, Any]:
        """Get details of a specific transaction."""
        result = await self._request(
            "GET",
            f"/transactions/{transaction_id}",
            params={"expand[]": "merchant"},
        )
        return result.get("transaction", {})

    # ==================== Pot Operations ====================

    async def list_pots(self, account_id: str) -> list[dict[str, Any]]:
        """List all pots for an account (read-only)."""
        params = {"current_account_id": account_id}
        result = await self._request("GET", "/pots", params=params)
        return result.get("pots", [])

    # ==================== Feed Operations ====================

    async def create_feed_item(
        self,
        account_id: str,
        title: str,
        body: str,
        image_url: str | None = None,
    ) -> dict[str, Any]:
        """Create a feed item (notification) in the user's Monzo app."""
        data = {
            "account_id": account_id,
            "type": "basic",
            "params[title]": title,
            "params[body]": body,
            "params[image_url]": image_url or "https://monzo.com/favicon.ico",
        }
        return await self._request("POST", "/feed", data=data)
