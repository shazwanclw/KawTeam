from test_api import HEADERS, client


def test_email_routes_require_session_and_contact_verification_requires_organiser():
    with client() as api:
        assert api.get("/email/status", headers=HEADERS).status_code == 401
        api.post("/session", headers=HEADERS, json={"profile": "observer"})
        result = api.post(
            "/cases/case-totes/email/sync", headers=HEADERS, json={"expectedRevision": 1}
        )
        assert result.status_code == 403
        api.post("/session", headers=HEADERS, json={"profile": "teammate"})
        result = api.post(
            "/cases/case-totes/email/contact",
            headers=HEADERS,
            json={"vendorId": "campus", "email": "test@gmail.com", "expectedRevision": 1},
        )
        assert result.status_code == 403


def test_email_body_rejects_unknown_fields():
    with client() as api:
        api.post("/session", headers=HEADERS, json={"profile": "organiser"})
        result = api.post(
            "/cases/case-totes/email/send",
            headers=HEADERS,
            json={
                "vendorId": "campus",
                "subject": "Test",
                "body": "Body",
                "expectedRevision": 1,
                "requestId": "test",
                "approveVendor": True,
            },
        )
        assert result.status_code == 422
