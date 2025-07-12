import unittest
from unittest.mock import patch, MagicMock
from name_game.app import app, get_available_names, initialize_database
import json

class TestApp(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        
        # Mock database connection
        self.patcher = patch('name_game.app.psycopg2.connect')
        self.mock_connect = self.patcher.start()
        self.mock_conn = MagicMock()
        self.mock_connect.return_value = self.mock_conn
        self.mock_cursor = MagicMock()
        self.mock_conn.cursor.return_value = self.mock_cursor

    def tearDown(self):
        self.patcher.stop()

    def test_initialize_database_success(self):
        """Test database initialization creates table"""
        initialize_database()
        self.mock_cursor.execute.assert_called_once()
        self.mock_conn.commit.assert_called_once()

    def test_initialize_database_failure(self):
        """Test database initialization handles errors"""
        self.mock_conn.cursor.side_effect = Exception("DB error")
        initialize_database()
        self.mock_conn.rollback.assert_called_once()

    def test_index_route(self):
        """Test index route returns available names"""
        self.mock_cursor.fetchall.return_value = [{'name': 'TestName'}]
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'TestName', response.data)

    def test_available_names_route(self):
        """Test available_names returns JSON with names"""
        self.mock_cursor.fetchall.return_value = [{'name': 'Name1'}, {'name': 'Name2'}]
        response = self.app.get('/available_names')
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Name1', data['names'])
        self.assertIn('timestamp', data)
        self.assertEqual(response.headers['Cache-Control'], 'no-cache, no-store, must-revalidate')

    def test_select_name_valid(self):
        """Test name selection with valid data"""
        self.mock_cursor.fetchone.return_value = None
        data = {
            'name': 'TestName',
            'email': 'test@example.com',
            'first_name': 'John',
            'last_name': 'Doe',
            'payment_method': 'venmo'
        }
        response = self.app.post('/select_name', json=data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), {"message": "Name selected successfully"})

    def test_select_name_missing_fields(self):
        """Test name selection with missing fields"""
        data = {'name': 'TestName', 'email': 'test@example.com'}
        response = self.app.post('/select_name', json=data)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Missing required fields", json.loads(response.data)['error'])

    def test_select_name_invalid_email(self):
        """Test name selection with invalid email"""
        data = {
            'name': 'TestName',
            'email': 'invalid-email',
            'first_name': 'John',
            'last_name': 'Doe',
            'payment_method': 'venmo'
        }
        response = self.app.post('/select_name', json=data)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid email format", json.loads(response.data)['error'])

    def test_select_name_duplicate(self):
        """Test duplicate name selection"""
        self.mock_cursor.fetchone.return_value = True
        data = {
            'name': 'TakenName',
            'email': 'test@example.com',
            'first_name': 'John',
            'last_name': 'Doe',
            'payment_method': 'venmo'
        }
        response = self.app.post('/select_name', json=data)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Name already selected", json.loads(response.data)['error'])

    def test_random_name_route(self):
        """Test random name selection"""
        with patch('name_game.app.random.choice') as mock_choice:
            mock_choice.return_value = 'RandomName'
            response = self.app.get('/random_name')
            data = json.loads(response.data)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(data['name'], 'RandomName')

    def test_random_name_no_available(self):
        """Test random name with no available names"""
        with patch('name_game.app.get_available_names') as mock_available:
            mock_available.return_value = []
            response = self.app.get('/random_name')
            self.assertEqual(response.status_code, 400)
            self.assertIn("No names available", json.loads(response.data)['error'])

if __name__ == '__main__':
    unittest.main()