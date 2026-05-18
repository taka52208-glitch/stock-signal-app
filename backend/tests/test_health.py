"""ヘルスチェックの基本テスト（テスト基盤の動作確認用）"""


def test_health_check(client):
    res = client.get('/api/health')
    assert res.status_code == 200
    assert res.json() == {'status': 'healthy'}
