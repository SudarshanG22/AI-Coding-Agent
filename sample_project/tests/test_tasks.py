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

def test_login_username_validation(client):
    # Valid username
    response = client.post('/login', json={'username': 'JohnDoe', 'password': 'password123'})
    assert response.status_code == 200

    # Username with numbers
    response = client.post('/login', json={'username': 'John123', 'password': 'password123'})
    assert response.status_code == 400
    assert response.json == {'error': 'Username must contain only alphabetic characters'}

    # Username with special characters
    response = client.post('/login', json={'username': 'John@Doe', 'password': 'password123'})
    assert response.status_code == 400
    assert response.json == {'error': 'Username must contain only alphabetic characters'}

    # Username with spaces
    response = client.post('/login', json={'username': 'John Doe', 'password': 'password123'})
    assert response.status_code == 400
    assert response.json == {'error': 'Username must contain only alphabetic characters'}

    # Empty username
    response = client.post('/login', json={'username': '', 'password': 'password123'})
    assert response.status_code == 400

    # Missing username
    response = client.post('/login', json={'password': 'password123'})
    assert response.status_code == 400