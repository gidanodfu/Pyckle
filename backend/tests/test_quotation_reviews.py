import pytest

from tests.conftest import auth_header, complete_order, drive_order, run_flow

pytestmark = pytest.mark.asyncio


async def _create_request_and_quote(client, customer_token, technician_token, specialty_id):
    request = await client.post(
        "/api/v1/repair-requests",
        headers=auth_header(customer_token),
        json={
            "title": "Segunda reparación para reseñas",
            "description": "Solicitud creada para validar las reseñas en cotizaciones.",
            "specialty_id": specialty_id,
            "modality": "home",
            "address": "Av. Reseñas 321",
        },
    )
    assert request.status_code == 201, request.text
    request_id = request.json()["id"]
    quotation = await client.post(
        "/api/v1/quotations",
        headers=auth_header(technician_token),
        json={
            "request_id": request_id,
            "price": 200,
            "preliminary_diagnosis": "Diagnóstico preliminar para la segunda cotización.",
        },
    )
    assert quotation.status_code == 201, quotation.text
    return request_id


async def test_quotation_shows_technician_reviews(client, customer_token, technician_ready):
    technician_token, specialty_id = technician_ready
    _, _, order_id = await run_flow(client, customer_token, technician_token, specialty_id)

    await drive_order(client, technician_token, order_id, "ready")
    completed = await complete_order(client, technician_token, order_id)
    assert completed.status_code == 200, completed.text
    review = await client.post(
        "/api/v1/reviews",
        headers=auth_header(customer_token),
        json={"order_id": order_id, "rating": 5, "comment": "Excelente servicio, muy puntual."},
    )
    assert review.status_code == 201, review.text

    request_id = await _create_request_and_quote(
        client, customer_token, technician_token, specialty_id
    )
    quotations = await client.get(
        f"/api/v1/quotations/request/{request_id}",
        headers=auth_header(customer_token),
    )
    assert quotations.status_code == 200, quotations.text
    quotation = quotations.json()[0]

    assert len(quotation["technician_reviews"]) == 1
    embedded = quotation["technician_reviews"][0]
    assert embedded["rating"] == 5
    assert embedded["comment"] == "Excelente servicio, muy puntual."
    assert embedded["customer_name"] == "Usuario customer"
    assert "email" not in embedded

    technician = quotation["technician"]
    assert float(technician["rating_avg"]) == 5.0
    assert technician["rating_count"] == 1
    assert technician["district_name"] == "José Leonardo Ortiz"


async def test_public_reviews_hide_customer_email(client, customer_token, technician_ready):
    technician_token, specialty_id = technician_ready
    _, _, order_id = await run_flow(client, customer_token, technician_token, specialty_id)
    await drive_order(client, technician_token, order_id, "ready")
    completed = await complete_order(client, technician_token, order_id)
    assert completed.status_code == 200, completed.text
    await client.post(
        "/api/v1/reviews",
        headers=auth_header(customer_token),
        json={"order_id": order_id, "rating": 4},
    )
    technician_id = (
        await client.get("/api/v1/technicians/me", headers=auth_header(technician_token))
    ).json()["id"]

    response = await client.get(f"/api/v1/technicians/{technician_id}/reviews")
    assert response.status_code == 200
    reviews = response.json()
    assert len(reviews) == 1
    assert "email" not in reviews[0]
    assert reviews[0]["customer_name"]
