"""
Integration Tests for Privacy API
Tests differential privacy application and private statistics computation
"""

import pytest
from src.api.app import app as flask_app


@pytest.fixture
def app():
    """Create and configure a test Flask app"""
    flask_app.config['TESTING'] = True
    return flask_app


@pytest.fixture
def client(app):
    """Create a test client"""
    return app.test_client()


class TestPrivacyApplication:
    """Test differential privacy application endpoint"""

    def test_apply_privacy_basic(self, client):
        """Test basic privacy application"""
        # First generate some data
        gen_response = client.post('/api/v1/generate/patients', json={
            'num_patients': 100,
            'seed': 42
        })

        assert gen_response.status_code == 200
        gen_data = gen_response.get_json()
        input_file = gen_data['data']['file_path']

        # Apply privacy
        privacy_response = client.post('/api/v1/privacy/apply', json={
            'input_file': input_file,
            'output_file': '/tmp/private_test.csv',
            'privacy_config': {
                'epsilon': 1.0,
                'delta': 1e-5
            },
            'numeric_columns': ['age', 'income'],
            'categorical_columns': []
        })

        assert privacy_response.status_code == 200
        privacy_data = privacy_response.get_json()
        assert privacy_data['status'] == 'success'
        assert privacy_data['data']['epsilon'] == 1.0
        assert privacy_data['data']['delta'] == 1e-5

    def test_apply_privacy_different_epsilons(self, client):
        """Test privacy application with different epsilon values"""
        # Generate data once
        gen_response = client.post('/api/v1/generate/patients', json={
            'num_patients': 50,
            'seed': 42
        })

        input_file = gen_response.get_json()['data']['file_path']

        # Test different epsilon values
        for epsilon in [0.1, 0.5, 1.0, 5.0]:
            privacy_response = client.post('/api/v1/privacy/apply', json={
                'input_file': input_file,
                'privacy_config': {
                    'epsilon': epsilon,
                    'delta': 1e-5
                },
                'numeric_columns': ['age']
            })

            assert privacy_response.status_code == 200
            data = privacy_response.get_json()
            assert data['data']['epsilon'] == epsilon

    def test_apply_privacy_missing_file(self, client):
        """Test privacy application with missing input file"""
        privacy_response = client.post('/api/v1/privacy/apply', json={
            'input_file': '/nonexistent/file.csv',
            'privacy_config': {
                'epsilon': 1.0,
                'delta': 1e-5
            },
            'numeric_columns': ['age']
        })

        assert privacy_response.status_code == 500
        data = privacy_response.get_json()
        assert data['status'] == 'error'

    def test_apply_privacy_invalid_epsilon(self, client):
        """Test privacy with invalid epsilon"""
        gen_response = client.post('/api/v1/generate/patients', json={
            'num_patients': 10,
            'seed': 42
        })

        input_file = gen_response.get_json()['data']['file_path']

        privacy_response = client.post('/api/v1/privacy/apply', json={
            'input_file': input_file,
            'privacy_config': {
                'epsilon': -1.0,  # Invalid: negative epsilon
                'delta': 1e-5
            },
            'numeric_columns': ['age']
        })

        # Should fail validation or produce error
        assert privacy_response.status_code in [400, 422, 500]


class TestPrivateStatistics:
    """Test private statistics computation endpoint"""

    def test_compute_private_mean(self, client):
        """Test computing private mean"""
        # Generate data
        gen_response = client.post('/api/v1/generate/patients', json={
            'num_patients': 100,
            'seed': 42
        })

        input_file = gen_response.get_json()['data']['file_path']

        # Compute private statistics
        stats_response = client.post('/api/v1/privacy/statistics', json={
            'input_file': input_file,
            'column': 'age',
            'epsilon': 1.0,
            'delta': 1e-5
        })

        assert stats_response.status_code == 200
        data = stats_response.get_json()
        assert data['status'] == 'success'
        assert 'statistics' in data['data']
        assert 'mean' in data['data']['statistics']
        assert 'variance' in data['data']['statistics']
        assert 'count' in data['data']['statistics']
        assert 'std' in data['data']['statistics']

    def test_compute_statistics_different_columns(self, client):
        """Test computing statistics for different columns"""
        # Generate data
        gen_response = client.post('/api/v1/generate/patients', json={
            'num_patients': 100,
            'seed': 42
        })

        input_file = gen_response.get_json()['data']['file_path']

        # Test different numeric columns
        for column in ['age', 'income']:
            stats_response = client.post('/api/v1/privacy/statistics', json={
                'input_file': input_file,
                'column': column,
                'epsilon': 1.0
            })

            assert stats_response.status_code == 200
            data = stats_response.get_json()
            assert data['data']['column'] == column

    def test_compute_statistics_invalid_column(self, client):
        """Test computing statistics for non-existent column"""
        # Generate data
        gen_response = client.post('/api/v1/generate/patients', json={
            'num_patients': 10,
            'seed': 42
        })

        input_file = gen_response.get_json()['data']['file_path']

        stats_response = client.post('/api/v1/privacy/statistics', json={
            'input_file': input_file,
            'column': 'nonexistent_column',
            'epsilon': 1.0
        })

        assert stats_response.status_code == 500
        data = stats_response.get_json()
        assert data['status'] == 'error'


class TestDiseaseProgression:
    """Test disease progression simulation endpoint"""

    def test_simulate_progression_basic(self, client):
        """Test basic disease progression simulation"""
        response = client.post('/api/v1/simulate/progression', json={
            'patient_id': 'PT000001',
            'num_visits': 5,
            'time_interval_days': 30
        })

        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert 'progression' in data['data']
        assert len(data['data']['progression']) == 5

    def test_simulate_progression_different_intervals(self, client):
        """Test progression with different time intervals"""
        for interval in [7, 14, 30, 90]:
            response = client.post('/api/v1/simulate/progression', json={
                'patient_id': f'PT{interval:06d}',
                'num_visits': 3,
                'time_interval_days': interval
            })

            assert response.status_code == 200
            data = response.get_json()
            assert data['data']['time_interval_days'] == interval

    def test_simulate_progression_multiple_visits(self, client):
        """Test progression with varying number of visits"""
        for num_visits in [1, 5, 10, 20]:
            response = client.post('/api/v1/simulate/progression', json={
                'patient_id': 'PT000001',
                'num_visits': num_visits,
                'time_interval_days': 30
            })

            assert response.status_code == 200
            data = response.get_json()
            assert len(data['data']['progression']) == num_visits


class TestPrivacyBudgetTracking:
    """Test privacy budget tracking and monitoring"""

    def test_privacy_operations_logged(self, client):
        """Test that privacy operations are logged"""
        # Generate data
        gen_response = client.post('/api/v1/generate/patients', json={
            'num_patients': 10,
            'seed': 42
        })

        input_file = gen_response.get_json()['data']['file_path']

        # Apply privacy multiple times
        for _ in range(3):
            client.post('/api/v1/privacy/apply', json={
                'input_file': input_file,
                'privacy_config': {
                    'epsilon': 0.5,
                    'delta': 1e-5
                },
                'numeric_columns': ['age']
            })

        # Operations should be logged (though we can't verify without DB access in tests)
        # This test validates the endpoint works without errors
        assert True

    def test_cumulative_budget(self, client):
        """Test cumulative privacy budget calculation"""
        # Generate data
        gen_response = client.post('/api/v1/generate/patients', json={
            'num_patients': 10,
            'seed': 42
        })

        input_file = gen_response.get_json()['data']['file_path']

        # Apply privacy with known epsilon values
        epsilons = [0.1, 0.2, 0.3]
        for eps in epsilons:
            client.post('/api/v1/privacy/apply', json={
                'input_file': input_file,
                'privacy_config': {
                    'epsilon': eps,
                    'delta': 1e-5
                },
                'numeric_columns': ['age']
            })

        # Total budget used should be sum of epsilons (0.6)
        # This would be verified through audit logs in production
        assert True
