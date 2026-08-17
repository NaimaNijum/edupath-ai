from __future__ import annotations

from app.main import app


def test_api_routes_are_registered() -> None:
    assert app.url_path_for("health") == "/health"
    assert app.url_path_for("create_profile") == "/api/v1/profiles"
    assert app.url_path_for("get_profile", profile_id="11111111-1111-1111-1111-111111111111") == "/api/v1/profiles/11111111-1111-1111-1111-111111111111"
    assert app.url_path_for("update_profile", profile_id="11111111-1111-1111-1111-111111111111") == "/api/v1/profiles/11111111-1111-1111-1111-111111111111"
    assert app.url_path_for("list_opportunities") == "/api/v1/opportunities"
    assert app.url_path_for("get_opportunity", opportunity_id="11111111-1111-1111-1111-111111111111") == "/api/v1/opportunities/11111111-1111-1111-1111-111111111111"
    assert app.url_path_for("get_memory", profile_id="11111111-1111-1111-1111-111111111111") == "/api/v1/memory/11111111-1111-1111-1111-111111111111"
    assert app.url_path_for("generate_sop") == "/api/v1/sop/generate"
    assert app.url_path_for("revise_sop") == "/api/v1/sop/revise"
    assert app.url_path_for("create_workflow") == "/api/v1/workflows"
    assert app.url_path_for("get_workflow", workflow_id="11111111-1111-1111-1111-111111111111") == "/api/v1/workflows/11111111-1111-1111-1111-111111111111"
