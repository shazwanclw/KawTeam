import pytest


def test_contact_requires_literal_address_and_service_evidence_on_same_website():
    from kawteam.contacts import verified_contact
    vendor = {"sourceUrl": "https://www.print.example.com/shirts"}
    page = {"url": "https://print.example.com/contact", "raw_content": "We offer custom shirt printing. Email sales@print.example.com"}
    assessment = {"eligible": True, "evidence": "custom shirt printing"}
    contact = verified_contact(vendor, [page], assessment)
    assert contact["email"] == "sales@print.example.com"
    assert contact["verifiedBy"] == "public_source"
    assert verified_contact(vendor, [{**page, "url": "https://directory.example.com/contact"}], assessment) is None
    assert verified_contact(vendor, [page], {"eligible": True, "evidence": "catering services"}) is None
    assert verified_contact(vendor, [page], {"eligible": False, "evidence": "custom shirt printing"}) is None


@pytest.mark.parametrize("url", ["http://127.0.0.1/contact", "https://localhost/contact", "https://user:pass@example.com", "https://10.0.0.1", "https://facebook.com/a", "https://example.com:8000/a"])
def test_non_business_and_private_urls_are_rejected(url):
    from kawteam.contacts import supplier_url
    with pytest.raises(ValueError):
        supplier_url(url)


def test_no_address_is_invented_from_company_domain():
    from kawteam.contacts import verified_contact
    assert verified_contact({"sourceUrl": "https://print.example.com"}, [{"url": "https://print.example.com", "raw_content": "Custom shirt printing. Call us."}], {"eligible": True, "evidence": "shirt printing"}) is None


def test_multiple_personal_addresses_are_ambiguous_and_no_reply_is_not_contact():
    from kawteam.contacts import verified_contact
    vendor = {"sourceUrl": "https://print.example.com"}
    page = {"url": "https://print.example.com", "raw_content": "Shirt printing a@gmail.com b@gmail.com noreply@print.example.com"}
    assert verified_contact(vendor, [page], {"eligible": True, "evidence": "Shirt printing"}) is None
