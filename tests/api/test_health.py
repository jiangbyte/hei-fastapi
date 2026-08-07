""" Author: Charlie """

async def test_root_health(client):
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


async def test_cors_headers_present_for_frontend_origin(client):
    response = await client.get("/", headers={"Origin": "http://localhost:5173"})

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


async def test_cors_headers_present_for_unhandled_500(client):
    response = await client.get("/__test/error", headers={"Origin": "http://localhost:5173"})

    assert response.status_code == 500
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


async def test_openapi_422_uses_unified_error_schema(client):
    response = await client.get("/openapi.json")

    assert response.status_code == 200
    data = response.json()
    login_422 = data["paths"]["/api/v1/portal/login"]["post"]["responses"]["422"]
    assert login_422["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/ApiErrorResponse"
    }
    assert (
        data["components"]["schemas"]["ApiErrorResponse"]["properties"]["code"]["type"] == "string"
    )
    assert (
        data["components"]["schemas"]["ApiResponse_LoginResponse_"]["properties"]["code"]["type"]
        == "string"
    )


async def test_openapi_protected_route_declares_401_403_500_error_schema(client):
    response = await client.get("/openapi.json")

    assert response.status_code == 200
    data = response.json()
    responses = data["paths"]["/api/v1/admin/sys/accounts/page"]["get"]["responses"]
    assert responses["401"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/ApiErrorResponse"
    }
    assert responses["403"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/ApiErrorResponse"
    }
    assert responses["500"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/ApiErrorResponse"
    }


async def test_unhandled_exception_uses_unified_500_response(client):
    response = await client.get("/__test/error")

    assert response.status_code == 500
    assert response.json() == {
        "code": "500",
        "message": "Internal server error",
        "data": None,
    }
    assert "Traceback" not in response.text
