from website import create_app

def test_config():
    assert not create_app().testing
    assert create_app({'TESTING': True}).testing

def test_log_in(client):
    response = client.get('/home')
    assert response.status_code == 200
    assert b'Sign In' in response.data