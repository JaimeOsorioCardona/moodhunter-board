"""Integration tests for Requests API endpoints and business rules."""

import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_create_and_get_request(client: AsyncClient):
    # 1. Create request
    response = await client.post(
        "/api/v1/requests",
        json={"title": "Test nueva solicitud", "description": "Detalles de prueba"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test nueva solicitud"
    assert data["status"] == "created"
    assert data["allowed_transitions"] == ["in_review"]
    public_id = data["public_id"]

    # 2. Get by public ID
    get_res = await client.get(f"/api/v1/requests/{public_id}")
    assert get_res.status_code == 200
    get_data = get_res.json()
    assert get_data["public_id"] == public_id
    assert len(get_data["history"]) == 1
    assert get_data["history"][0]["to_status"] == "created"


@pytest.mark.anyio
async def test_invalid_transition_returns_409_conflict(client: AsyncClient):
    # Create request (starts in 'created')
    create_res = await client.post(
        "/api/v1/requests",
        json={"title": "Solicitud para probar salto invalido"},
    )
    public_id = create_res.json()["public_id"]

    # Attempt illegal jump: created -> in_progress
    trans_res = await client.post(
        f"/api/v1/requests/{public_id}/transitions",
        json={"target_status": "in_progress"},
    )
    assert trans_res.status_code == 409
    err = trans_res.json()
    assert err["error"] == "transition_not_allowed"
    assert "No se permite la transición" in err["message"]
    assert err["details"]["current"] == "created"
    assert err["details"]["target"] == "in_progress"
    assert err["details"]["allowed"] == ["in_review"]


@pytest.mark.anyio
async def test_full_request_lifecycle_and_paused_rules(client: AsyncClient):
    # Create -> starts in created
    req = (await client.post("/api/v1/requests", json={"title": "Ciclo completo"})).json()
    public_id = req["public_id"]

    # created -> in_review (OK)
    res1 = await client.post(f"/api/v1/requests/{public_id}/transitions", json={"target_status": "in_review"})
    assert res1.status_code == 200
    assert res1.json()["status"] == "in_review"

    # in_review -> paused (OK)
    res2 = await client.post(f"/api/v1/requests/{public_id}/transitions", json={"target_status": "paused"})
    assert res2.status_code == 200
    assert res2.json()["status"] == "paused"

    # paused -> done (ILLEGAL, MUST FAIL with 409)
    res3 = await client.post(f"/api/v1/requests/{public_id}/transitions", json={"target_status": "done"})
    assert res3.status_code == 409
    assert res3.json()["error"] == "transition_not_allowed"

    # paused -> in_progress (OK, resume work)
    res4 = await client.post(f"/api/v1/requests/{public_id}/transitions", json={"target_status": "in_progress"})
    assert res4.status_code == 200
    assert res4.json()["status"] == "in_progress"

    # in_progress -> done (OK, finish work)
    res5 = await client.post(f"/api/v1/requests/{public_id}/transitions", json={"target_status": "done"})
    assert res5.status_code == 200
    assert res5.json()["status"] == "done"

    # done -> in_progress (ILLEGAL, done is terminal)
    res6 = await client.post(f"/api/v1/requests/{public_id}/transitions", json={"target_status": "in_progress"})
    assert res6.status_code == 409


@pytest.mark.anyio
async def test_patch_request_details(client: AsyncClient):
    create_res = await client.post("/api/v1/requests", json={"title": "Título inicial"})
    public_id = create_res.json()["public_id"]

    patch_res = await client.patch(
        f"/api/v1/requests/{public_id}",
        json={"title": "Título actualizado", "description": "Nueva descripción"},
    )
    assert patch_res.status_code == 200
    data = patch_res.json()
    assert data["title"] == "Título actualizado"
    assert data["description"] == "Nueva descripción"


@pytest.mark.anyio
async def test_not_found_returns_404(client: AsyncClient):
    res = await client.get("/api/v1/requests/00000000-0000-0000-0000-000000000000")
    assert res.status_code == 404
    assert res.json()["error"] == "request_not_found"


@pytest.mark.anyio
async def test_unknown_status_returns_422(client: AsyncClient):
    create_res = await client.post("/api/v1/requests", json={"title": "Test status desconocido"})
    public_id = create_res.json()["public_id"]

    res = await client.post(
        f"/api/v1/requests/{public_id}/transitions",
        json={"target_status": "estado_inexistente"},
    )
    assert res.status_code == 422
    assert res.json()["error"] == "unknown_status"


@pytest.mark.anyio
async def test_ai_summary_endpoint_returns_200_fallback(client: AsyncClient):
    res = await client.post("/api/v1/requests/ai-summary")
    assert res.status_code == 200
    data = res.json()
    assert data["source"] in ("llm", "fallback")
    assert "headline" in data
    assert "highlights" in data
    assert "risks" in data
    assert "next_actions" in data

