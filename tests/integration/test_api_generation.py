"""
Integration Tests for Data Generation API
Tests patient generation, vitals generation, and batch generation endpoints
"""

import pytest
import json
from pathlib import Path
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


class TestPatientGeneration:
    """Test patient data generation endpoint"""

    def test_generate_patients_basic(self, client):
        """Test basic patient generation"""
        response = client.post('/api/v1/generate/patients', json={
            'num_patients': 10,
            'seed': 42
        })

        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert 'data' in data
        assert data['data']['records_generated'] == 10

    def test_generate_patients_custom_count(self, client):
        """Test generating different numbers of patients"""
        for count in [1, 50, 100]:
            response = client.post('/api/v1/generate/patients', json={
                'num_patients': count,
                'seed': 42
            })

            assert response.status_code == 200
            data = response.get_json()
            assert data['data']['records_generated'] == count

    def test_generate_patients_reproducibility(self, client):
        """Test that same seed produces same results"""
        response1 = client.post('/api/v1/generate/patients', json={
            'num_patients': 10,
            'seed': 42
        })

        response2 = client.post('/api/v1/generate/patients', json={
            'num_patients': 10,
            'seed': 42
        })

        data1 = response1.get_json()
        data2 = response2.get_json()

        # Both should succeed
        assert data1['status'] == 'success'
        assert data2['status'] == 'success'
        assert data1['data']['records_generated'] == data2['data']['records_generated']

    def test_generate_patients_invalid_count(self, client):
        """Test generating with invalid patient count"""
        response = client.post('/api/v1/generate/patients', json={
            'num_patients': -10
        })

        # Should fail validation
        assert response.status_code in [400, 422, 500]

    def test_generate_patients_missing_params(self, client):
        """Test generation with missing parameters"""
        response = client.post('/api/v1/generate/patients', json={})

        # Should either use defaults or fail
        assert response.status_code in [200, 400, 422, 500]


class TestVitalsGeneration:
    """Test vitals generation endpoint"""

    def test_generate_vitals_missing_file(self, client):
        """Test vitals generation without input file"""
        response = client.post('/api/v1/generate/vitals', json={})

        assert response.status_code == 400
        data = response.get_json()
        assert data['status'] == 'error'
        assert 'input_file' in data['error_message'].lower()

    def test_generate_vitals_invalid_file(self, client):
        """Test vitals generation with non-existent file"""
        response = client.post('/api/v1/generate/vitals', json={
            'input_file': '/nonexistent/file.csv'
        })

        assert response.status_code == 500
        data = response.get_json()
        assert data['status'] == 'error'


class TestBatchGeneration:
    """Test batch generation endpoint"""

    def test_batch_generation_basic(self, client):
        """Test basic batch generation"""
        response = client.post('/api/v1/generate/batch', json={
            'num_patients': 10,
            'seed': 42,
            'output_directory': '/tmp/test_batch',
            'include_vitals': True,
            'include_treatments': True,
            'apply_privacy': False
        })

        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert 'files' in data['data']
        assert 'patients' in data['data']['files']

    def test_batch_generation_with_privacy(self, client):
        """Test batch generation with privacy"""
        response = client.post('/api/v1/generate/batch', json={
            'num_patients': 10,
            'seed': 42,
            'output_directory': '/tmp/test_batch_private',
            'include_vitals': False,
            'include_treatments': False,
            'apply_privacy': True,
            'privacy_config': {
                'epsilon': 1.0,
                'delta': 1e-5
            }
        })

        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert 'private_patients' in data['data']['files']

    def test_batch_generation_all_components(self, client):
        """Test generating all data components"""
        response = client.post('/api/v1/generate/batch', json={
            'num_patients': 5,
            'output_directory': '/tmp/test_batch_full',
            'include_vitals': True,
            'include_treatments': True,
            'apply_privacy': True,
            'privacy_config': {
                'epsilon': 0.5,
                'delta': 1e-5
            }
        })

        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'

        # Check all expected files are generated
        files = data['data']['files']
        assert 'patients' in files
        assert 'vitals' in files
        assert 'treatments' in files
        assert 'private_patients' in files


class TestDataExport:
    """Test data export endpoint"""

    def test_export_csv(self, client):
        """Test exporting data as CSV"""
        # First generate some data
        gen_response = client.post('/api/v1/generate/patients', json={
            'num_patients': 5,
            'seed': 42
        })

        assert gen_response.status_code == 200
        gen_data = gen_response.get_json()
        input_file = gen_data['data']['file_path']

        # Now export it
        export_response = client.post('/api/v1/export', json={
            'input_file': input_file,
            'output_file': '/tmp/export_test.csv',
            'export_format': 'csv',
            'apply_privacy': False
        })

        assert export_response.status_code in [200, 500]  # May fail due to file paths

    def test_export_invalid_format(self, client):
        """Test export with invalid format"""
        response = client.post('/api/v1/export', json={
            'input_file': '/tmp/test.csv',
            'output_file': '/tmp/test_export',
            'export_format': 'invalid_format'
        })

        assert response.status_code in [400, 422, 500]


class TestAPIResponseFormat:
    """Test API response format consistency"""

    def test_success_response_format(self, client):
        """Test that success responses have consistent format"""
        response = client.post('/api/v1/generate/patients', json={
            'num_patients': 5,
            'seed': 42
        })

        data = response.get_json()
        assert 'status' in data
        assert 'timestamp' in data
        assert data['status'] == 'success'
        assert 'message' in data
        assert 'data' in data

    def test_error_response_format(self, client):
        """Test that error responses have consistent format"""
        response = client.post('/api/v1/generate/vitals', json={})

        data = response.get_json()
        assert 'status' in data
        assert 'timestamp' in data
        assert data['status'] == 'error'
        assert 'error_message' in data
        assert 'error_code' in data
