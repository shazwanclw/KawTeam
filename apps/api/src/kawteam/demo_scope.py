"""Presentation-only provenance; never qualifies a supplier for live liaison."""


def controlled_demo_offer(case, vendor):
    if vendor.get("executionMode", "demo") != "demo":
        return False
    if case["id"] == "case-totes":
        return True
    return (
        case.get("sample") is True
        and case.get("demoScenarioVersion") == 1
        and vendor.get("sample") is True
        and vendor.get("scenarioCaseId") == case["id"]
    )
