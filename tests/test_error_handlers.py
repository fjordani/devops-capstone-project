"""
Test Cases for Error Handlers

This module contains test cases for verifying the behavior of custom error handlers
in the service. It ensures that the application responds with the correct HTTP
status codes and messages for various error scenarios, such as:

- 400 Bad Request
- 404 Not Found
- 405 Method Not Allowed
- 415 Unsupported Media Type
- 500 Internal Server Error

Each test case uses the Flask test client to simulate requests and validate
responses, ensuring robust error handling in the application.
"""

import unittest
from unittest.mock import patch
from service import app
from service.common import status
from service.models import DataValidationError

class TestErrorHandlers(unittest.TestCase):
    """Test Cases for Error Handlers"""

    def setUp(self):
        """Runs before each test"""
        self.client = app.test_client()

    def test_bad_request(self):
        """It should return 400_BAD_REQUEST"""
        with patch("service.common.error_handlers.app.logger.warning") as mock_logger:
            response = self.client.post("/accounts", json={"invalid": "data"})
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            mock_logger.assert_called()

    def test_not_found(self):
        """It should return 404_NOT_FOUND"""
        with patch("service.common.error_handlers.app.logger.warning") as mock_logger:
            response = self.client.get("/accounts/0")
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
            mock_logger.assert_called()

    def test_method_not_allowed(self):
        """It should return 405_METHOD_NOT_ALLOWED"""
        with patch("service.common.error_handlers.app.logger.warning") as mock_logger:
            response = self.client.delete("/accounts")
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
            mock_logger.assert_called()

    def test_unsupported_media_type(self):
        """It should return 415_UNSUPPORTED_MEDIA_TYPE"""
        with patch("service.common.error_handlers.app.logger.warning") as mock_logger:
            response = self.client.post(
                "/accounts", data="invalid data", content_type="text/plain"
            )
            self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)
            mock_logger.assert_called()

    def test_internal_server_error(self):
        """It should return 500_INTERNAL_SERVER_ERROR"""
        with patch("service.common.error_handlers.app.logger.error") as mock_logger:
            with patch("service.routes.Account.find", side_effect=Exception("DB Error")):
                response = self.client.get("/accounts/1")
                self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
                mock_logger.assert_called()