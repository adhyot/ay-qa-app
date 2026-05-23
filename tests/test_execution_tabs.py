def test_index_redirects_to_runs(client):
    r = client.get('/execution/', follow_redirects=False)
    assert r.status_code == 302
    assert '/execution/runs' in r.headers['Location']


def test_runs_page_has_tab_bar(client):
    r = client.get('/execution/runs')
    assert r.status_code == 200
    assert b'exec-tabs' in r.data
    assert b'Test Runs' in r.data
    assert b'Bugs' in r.data
    assert b'Deployments' in r.data
    assert b'Execution Hub' in r.data
