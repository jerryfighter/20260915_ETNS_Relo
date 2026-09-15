def test_area_search_by_name(client, area):
    resp = client.get("/areas?q=Gangnam")
    assert resp.status_code == 200
    assert b"Gangnam" in resp.data


def test_area_search_no_match(client, area):
    resp = client.get("/areas?q=Nonexistent")
    assert resp.status_code == 200
    assert b"No areas match" in resp.data


def test_area_detail_page(client, area, review):
    resp = client.get(f"/areas/{area.id}")
    assert resp.status_code == 200
    assert b"Gangnam" in resp.data
    assert b"Great area" in resp.data


def test_area_detail_not_found(client):
    resp = client.get("/areas/9999")
    assert resp.status_code == 404


def test_api_list_areas(client, area):
    resp = client.get("/api/areas")
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data) == 1
    assert data[0]["name"] == "Gangnam"


def test_api_search_areas(client, area):
    resp = client.get("/api/areas/search?q=gang")
    data = resp.get_json()
    assert len(data) == 1


def test_area_compare_page(client, area):
    resp = client.get(f"/areas/compare?ids={area.id}")
    assert resp.status_code == 200
    assert b"Gangnam" in resp.data
