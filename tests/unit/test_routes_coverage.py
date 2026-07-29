"""
Complete tests for test_routes.py to achieve 100% coverage
"""

import pytest
from fastapi.testclient import TestClient
import test_routes


class TestTestRoutesApp:
    """Test the FastAPI app defined in test_routes.py"""
    
    @pytest.fixture
    def client(self):
        """Create test client for the app"""
        return TestClient(test_routes.app)
    
    def test_index_route(self, client):
        """Test GET / endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "INDEX"}
    
    def test_health_route(self, client):
        """Test GET /health endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"message": "HEALTH"}
    
    def test_testpage_route(self, client):
        """Test GET /testpage endpoint"""
        response = client.get("/testpage")
        assert response.status_code == 200
        assert response.json() == {"message": "TESTPAGE"}
    
    def test_test_html_route(self, client):
        """Test GET /test.html endpoint"""
        response = client.get("/test.html")
        assert response.status_code == 200
        assert response.json() == {"message": "TEST HTML"}
    
    def test_nonexistent_route(self, client):
        """Test GET to nonexistent route returns 404"""
        response = client.get("/nonexistent")
        assert response.status_code == 404
    
    def test_route_method_not_allowed(self, client):
        """Test POST to GET-only route"""
        response = client.post("/")
        assert response.status_code == 405


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
