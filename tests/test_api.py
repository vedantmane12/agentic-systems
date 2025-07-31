"""
Tests for FastAPI Backend
"""

import pytest
from fastapi.testclient import TestClient
import sys
import os
from unittest.mock import patch, MagicMock

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from api.main import app, tasks

# Create test client
client = TestClient(app)


class TestAPI:
    """Test cases for API endpoints"""
    
    @pytest.fixture(autouse=True)
    def clear_tasks(self):
        """Clear tasks before each test"""
        tasks.clear()
        yield
        tasks.clear()
    
    def test_root_endpoint(self):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "endpoints" in data
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "environment" in data
    
    def test_execute_research_valid(self):
        """Test research execution with valid request"""
        request_data = {
            "query": "What is artificial intelligence?"
        }
        
        response = client.post("/research", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "task_id" in data
        assert data["status"] == "pending"
        assert "message" in data
        
        # Check task was created
        task_id = data["task_id"]
        assert task_id in tasks
        assert tasks[task_id]["query"] == request_data["query"]
    
    def test_execute_research_empty_query(self):
        """Test research execution with empty query"""
        request_data = {
            "query": ""
        }
        
        response = client.post("/research", json=request_data)
        assert response.status_code == 400
        assert "Query cannot be empty" in response.json()["detail"]
    
    def test_get_task_status_valid(self):
        """Test getting status of existing task"""
        # Create a task
        task_id = "test-task-123"
        tasks[task_id] = {
            "task_id": task_id,
            "status": "completed",
            "query": "Test query",
            "result": {"success": True},
            "error": None,
            "created_at": "2024-01-01T00:00:00",
            "completed_at": "2024-01-01T00:01:00"
        }
        
        response = client.get(f"/status/{task_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["task_id"] == task_id
        assert data["status"] == "completed"
        assert data["query"] == "Test query"
        assert data["result"]["success"] is True
    
    def test_get_task_status_not_found(self):
        """Test getting status of non-existent task"""
        response = client.get("/status/non-existent-task")
        assert response.status_code == 404
        assert "Task not found" in response.json()["detail"]
    
    def test_get_all_tasks(self):
        """Test getting all tasks"""
        # Add some tasks
        tasks["task1"] = {"status": "completed"}
        tasks["task2"] = {"status": "running"}
        
        response = client.get("/tasks")
        assert response.status_code == 200
        
        data = response.json()
        assert data["count"] == 2
        assert len(data["tasks"]) == 2
    
    def test_clear_completed_tasks(self):
        """Test clearing completed tasks"""
        # Add tasks with different statuses
        tasks["task1"] = {"status": "completed"}
        tasks["task2"] = {"status": "failed"}
        tasks["task3"] = {"status": "running"}
        tasks["task4"] = {"status": "pending"}
        
        response = client.delete("/tasks/clear")
        assert response.status_code == 200
        
        data = response.json()
        assert data["message"] == "Cleared 2 completed tasks"
        assert data["remaining"] == 2
        
        # Check remaining tasks
        assert "task1" not in tasks
        assert "task2" not in tasks
        assert "task3" in tasks
        assert "task4" in tasks
    
    @patch('api.main.run_research_task')
    def test_background_task_triggered(self, mock_run_task):
        """Test that background task is triggered"""
        request_data = {
            "query": "Test query",
            "config": {"verbose": False}
        }
        
        response = client.post("/research", json=request_data)
        assert response.status_code == 200
        
        # Background task should be called
        # Note: In test environment, background tasks run synchronously
        mock_run_task.assert_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])