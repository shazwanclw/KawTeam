import pytest


def test_contact_requires_literal_address_and_service_evidence_on_same_website():
    from kawteam.contacts import verified_contact

    vendor = {"sourceUrl": "https://www.print.example.com/shirts"}
    page = {
        "url": "https://print.example.com/contact",
        "raw_content": "We offer custom shirt printing. Email sales@print.example.com",
    }
    assessment = {"eligible": True, "evidence": "custom shirt printing"}
    contact = verified_contact(vendor, [page], assessment)
    assert contact["email"] == "sales@print.example.com"
    assert contact["verifiedBy"] == "public_source"
    assert (
        verified_contact(
            vendor, [{**page, "url": "https://directory.example.com/contact"}], assessment
        )
        is None
    )
    assert (
        verified_contact(vendor, [page], {"eligible": True, "evidence": "catering services"})
        is None
    )
    assert (
        verified_contact(vendor, [page], {"eligible": False, "evidence": "custom shirt printing"})
        is None
    )


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1/contact",
        "https://localhost/contact",
        "https://user:pass@example.com",
        "https://10.0.0.1",
        "https://facebook.com/a",
        "https://example.com:8000/a",
    ],
)
def test_non_business_and_private_urls_are_rejected(url):
    from kawteam.contacts import supplier_url

    with pytest.raises(ValueError):
        supplier_url(url)


def test_no_address_is_invented_from_company_domain():
    from kawteam.contacts import verified_contact

    assert (
        verified_contact(
            {"sourceUrl": "https://print.example.com"},
            [
                {
                    "url": "https://print.example.com",
                    "raw_content": "Custom shirt printing. Call us.",
                }
            ],
            {"eligible": True, "evidence": "shirt printing"},
        )
        is None
    )


def test_multiple_personal_addresses_are_ambiguous_and_no_reply_is_not_contact():
    from kawteam.contacts import verified_contact

    vendor = {"sourceUrl": "https://print.example.com"}
    page = {
        "url": "https://print.example.com",
        "raw_content": "Shirt printing a@gmail.com b@gmail.com noreply@print.example.com",
    }
    assert (
        verified_contact(vendor, [page], {"eligible": True, "evidence": "Shirt printing"}) is None
    )


def test_sales_is_preferred_over_general_info_without_discarding_both():
    from kawteam.contacts import verified_contact

    page = {
        "url": "https://print.example.com/contact",
        "raw_content": "Shirt printing sales@print.example.com info@print.example.com",
    }
    contact = verified_contact(
        {"sourceUrl": page["url"]}, [page], {"eligible": True, "evidence": "Shirt printing"}
    )
    assert contact["email"] == "sales@print.example.com"


def test_discovery_searches_actual_contact_page_when_guessed_paths_have_no_email(monkeypatch):
    import json

    import httpx

    from kawteam.config import Settings
    from kawteam.contacts import contact_valid, discover_contact

    page = {
        "url": "https://print.example.com/get-in-touch",
        "raw_content": "Custom shirt printing. sales@print.example.com info@print.example.com",
    }
    searches = []

    def handle(request):
        payload = json.loads(request.content)
        if request.url.path == "/extract":
            return httpx.Response(
                200,
                json={
                    "results": [page]
                    if page["url"] in payload["urls"]
                    else [
                        {
                            "url": "https://print.example.com",
                            "raw_content": "Custom shirt printing.",
                        }
                    ]
                },
            )
        if request.url.path == "/search":
            searches.append(payload)
            return httpx.Response(
                200,
                json={
                    "results": [
                        page,
                        {
                            "url": "https://evil.example.com",
                            "raw_content": "sales@evil.example.com",
                        },
                    ]
                },
            )
        return httpx.Response(
            200,
            json={
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {
                                    "text": json.dumps(
                                        {"eligible": True, "evidence": "Custom shirt printing."}
                                    )
                                }
                            ]
                        }
                    }
                ]
            },
        )

    monkeypatch.setattr(
        "kawteam.contacts.client", lambda: httpx.Client(transport=httpx.MockTransport(handle))
    )
    vendor = {"sourceUrl": "https://print.example.com", "name": "Printer"}
    contact = discover_contact(
        vendor, {"goal": "50 shirts"}, Settings(tavily_key="test", gemini_key="test")
    )
    assert searches[0]["include_domains"] == ["print.example.com"]
    assert contact["email"] == "sales@print.example.com"
    assert contact_valid({**vendor, "contact": contact})
