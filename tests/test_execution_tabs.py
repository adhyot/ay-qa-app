def test_index_redirects_to_runs(client):
    r = client.get('/execution/', follow_redirects=False)
    assert r.status_code == 302
    assert '/execution/runs' in r.headers['Location']
