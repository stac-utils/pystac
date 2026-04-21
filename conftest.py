from typing import Any
from urllib.request import Request

import pytest


@pytest.fixture(scope="module")
def vcr_config() -> dict[str, Any]:
    def scrub_response_headers(response: dict[str, Any]) -> dict[str, Any]:
        retain = ["location"]
        response["headers"] = {
            key: value
            for (key, value) in response["headers"].items()
            if key.lower() in retain
        }
        return response

    def scrub_request_headers(request: Request) -> Request:
        drop = ["User-Agent"]
        for header in drop:
            request.headers.pop(header, None)
        return request

    return {
        "before_record_response": scrub_response_headers,
        "before_record_request": scrub_request_headers,
    }
