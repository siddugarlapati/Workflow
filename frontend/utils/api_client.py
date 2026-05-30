"""
WorkFlow — API Client for Streamlit
===================================
Manages state, JWT headers, and raw requests to the FastAPI backend.
"""
import os
from typing import Any, Dict, List, Optional
import httpx
import streamlit as st

BACKEND_URL = os.getenv("VITE_API_URL", "http://localhost:8000")


class APIClient:
    """Helper client to talk to the FastAPI backend with token auth."""

    @staticmethod
    def get_headers() -> Dict[str, str]:
        headers = {}
        if "token" in st.session_state and st.session_state.token:
            headers["Authorization"] = f"Bearer {st.session_state.token}"
        return headers

    @classmethod
    def request(
        self,
        method: str,
        path: str,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
    ) -> httpx.Response:
        url = f"{BACKEND_URL}{path}"
        headers = self.get_headers()
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.request(
                    method=method,
                    url=url,
                    json=json_data,
                    data=data,
                    files=files,
                    params=params,
                    headers=headers,
                )
                return response
        except httpx.RequestError as exc:
            st.error(f"Backend connection error: {exc}")
            raise

    @classmethod
    def get(cls, path: str, params: Optional[Dict[str, Any]] = None) -> httpx.Response:
        return cls.request("GET", path, params=params)

    @classmethod
    def post(cls, path: str, json_data: Optional[Dict[str, Any]] = None) -> httpx.Response:
        return cls.request("POST", path, json_data=json_data)

    @classmethod
    def post_multipart(
        cls,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
    ) -> httpx.Response:
        return cls.request("POST", path, data=data, files=files)

    @classmethod
    def patch(cls, path: str, json_data: Optional[Dict[str, Any]] = None) -> httpx.Response:
        return cls.request("PATCH", path, json_data=json_data)

    @classmethod
    def delete(cls, path: str) -> httpx.Response:
        return cls.request("DELETE", path)


def init_session_state() -> None:
    """Initializes Streamlit session states for security and role management."""
    if "token" not in st.session_state:
        st.session_state.token = None
    if "user" not in st.session_state:
        st.session_state.user = None
    if "page" not in st.session_state:
        st.session_state.page = "Login"


def logout() -> None:
    """Clears the session state and returns to login."""
    st.session_state.token = None
    st.session_state.user = None
    st.session_state.page = "Login"
    st.rerun()
