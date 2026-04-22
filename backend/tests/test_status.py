from app import create_app
from app.extensions import db


class TestConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = "test"
    JWT_SECRET_KEY = "test-jwt-secret-key-with-32-plus-bytes"


class MaintenanceConfig(TestConfig):
    SERVICE_MAINTENANCE_MODE = True
    SERVICE_MAINTENANCE_TITLE = "定期メンテナンス"
    SERVICE_MAINTENANCE_MESSAGE = "4月末メンテナンスを実施します"
    SERVICE_MAINTENANCE_SCHEDULED_UNTIL = "2026-04-30T00:00:00Z"


def _create_client(config=TestConfig):
    app = create_app(config)
    with app.app_context():
        db.create_all()
    return app.test_client()


def test_status_endpoint_returns_components_and_overall():
    client = _create_client()

    response = client.get('/api/status')
    assert response.status_code == 200

    payload = response.get_json()['status']
    assert payload['overall'] in {'normal', 'warning', 'outage', 'maintenance'}
    assert 'updated_at' in payload
    assert 'components' in payload
    assert payload['components']['application']['status'] == 'normal'


def test_status_endpoint_maintenance_mode():
    client = _create_client(MaintenanceConfig)

    response = client.get('/api/status')
    assert response.status_code == 200

    payload = response.get_json()['status']
    assert payload['overall'] == 'maintenance'
    assert payload['maintenance']['title'] == '定期メンテナンス'


def test_admin_status_requires_provisional_header():
    client = _create_client()

    response = client.get('/api/admin/status')
    assert response.status_code == 403
    assert response.get_json()['error']['code'] == 'admin/forbidden'


def test_admin_status_returns_internal_field_when_authorized():
    client = _create_client()

    response = client.get('/api/admin/status', headers={'X-Admin-Mode': 'true'})
    assert response.status_code == 200

    payload = response.get_json()['status']
    assert payload['internal']['history'] == 'not_implemented_mvp'
