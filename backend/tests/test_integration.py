"""
Integration test setup and basic flow verification.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Import app to verify it loads correctly
from backend.main import app

class TestIntegrationFlow:
    """
    Integration tests verifying the wiring of the application.
    Uses TestClient to simulate HTTP requests.
    """
    
    @pytest.fixture
    def client(self):
        # Patch dependencies that require external services
        with patch("backend.call_routes.twilio_client", MagicMock()):
            with patch("backend.shared.database.SupabaseDB") as MockDB:
                # Setup mock DB behaviors for critical paths if needed
                # For basic router wiring, the auth check handles most
                yield TestClient(app)

    def test_health_check(self, client):
        """Verify health endpoint is accessible"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "backend" in data

    def test_auth_protected_endpoints(self, client):
        """Verify protected endpoints require auth"""
        # Attempt to access protected route without token
        response = client.get("/agents")
        
        # Expect 401 Unauthorized (or 403 depending on implementation)
        # Note: FastAPI Depends(get_current_user) usually raises 401
        assert response.status_code in [401, 403]

    def test_full_startup_flow(self):
        """Verify the application can startup without errors"""
        with TestClient(app) as client:
            assert client.app is not None
