from ..serve import app


def test_server_info():
    request, response = app.test_client.get('/')
    assert response.status == 200
    for key in ('package', 'version', 'message'):
        assert key in response.json


def test_bad_projects():
    request, response = app.test_client.get('/projects/nipy')
    assert response.status == 400


def test_missing_version():
    # repo with no releases or tags
    request, response = app.test_client.get('/projects/mgxd/mytestrepo')
    assert response.status == 200
    assert response.json.get('version') == "Unknown"


def test_tagged_version():
    # repo with tag set
    request, response = app.test_client.get('/projects/mgxd/taggedrepo')
    assert response.status == 200
    assert response.json.get('version') == "0.1"
