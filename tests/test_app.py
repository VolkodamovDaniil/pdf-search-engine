import pytest
from app import app

def test_app_creation():
    assert app is not None
    assert app.name == 'app'

def test_app_config():
    assert app.config['TESTING'] == False
    assert 'SQLALCHEMY_DATABASE_URI' in app.config

def test_index_route():
    with app.test_client() as client:
        response = client.get('/')
        assert response.status_code == 200

def test_search_route():
    with app.test_client() as client:
        response = client.get('/search?q=test')
        assert response.status_code == 200