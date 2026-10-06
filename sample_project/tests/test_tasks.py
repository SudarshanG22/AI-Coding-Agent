def test_example():
    assert 1 + 1 == 2


def test_create_task_empty_or_whitespace_title_returns_400(client):
    # Test with empty title
    response = client.post('/tasks', json={'title': '', 'description': 'Some description'})
    assert response.status_code == 400
    assert response.json == {'error': 'Title cannot be empty or whitespace only'}

    # Test with whitespace-only title
    response = client.post('/tasks', json={'title': '   ', 'description': 'Another description'})
    assert response.status_code == 400
    assert response.json == {'error': 'Title cannot be empty or whitespace only'}