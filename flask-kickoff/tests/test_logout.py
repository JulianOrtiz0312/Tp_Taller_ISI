def test_logout_clears_session(client):
    with client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["user_name"] = "Claudio"

    response = client.post("/users/logout", follow_redirects=True)

    assert response.status_code == 200
    assert "sesion cerrada correctamente" in response.get_data(as_text=True)
    with client.session_transaction() as sess:
        assert "user_id" not in sess


def test_logout_without_active_session(client):
    response = client.post("/users/logout", follow_redirects=True)

    assert response.status_code == 200
    assert "no hay sesion activa" in response.get_data(as_text=True)
