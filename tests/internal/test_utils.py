import unittest

try:
    from unittest.mock import Mock, patch
except ImportError:
    from mock import Mock, patch

from pyOutlook.internal.utils import get_valid_filename, get_response_data, check_response
from pyOutlook.internal.errors import AuthError, RequestError, APIError


class GetValidFilenameTestCase(unittest.TestCase):
    """Test cases for get_valid_filename function"""

    def test_get_valid_filename__simple_string(self):
        """Test that a simple string is returned unchanged"""
        result = get_valid_filename("simple")
        self.assertEqual(result, "simple")

    def test_get_valid_filename__with_spaces(self):
        """Test that spaces are converted to underscores"""
        result = get_valid_filename("file with spaces.txt")
        self.assertEqual(result, "file_with_spaces.txt")

    def test_get_valid_filename__with_leading_spaces(self):
        """Test that leading spaces are removed"""
        result = get_valid_filename("  leading.txt")
        self.assertEqual(result, "leading.txt")

    def test_get_valid_filename__with_trailing_spaces(self):
        """Test that trailing spaces are removed"""
        result = get_valid_filename("trailing.txt  ")
        self.assertEqual(result, "trailing.txt")

    def test_get_valid_filename__with_leading_and_trailing_spaces(self):
        """Test that both leading and trailing spaces are removed"""
        result = get_valid_filename("  both  ")
        self.assertEqual(result, "both")

    def test_get_valid_filename__with_apostrophe(self):
        """Test that apostrophes are removed"""
        result = get_valid_filename("john's portrait in 2004.jpg")
        self.assertEqual(result, "johns_portrait_in_2004.jpg")

    def test_get_valid_filename__with_special_characters(self):
        """Test that special characters are removed"""
        result = get_valid_filename("file!@#$%^&*()+={}[]|\\:;\"'<>,?/name.txt")
        self.assertEqual(result, "filename.txt")

    def test_get_valid_filename__with_alphanumeric_dash_underscore_dot(self):
        """Test that alphanumeric, dash, underscore, and dot are kept"""
        result = get_valid_filename("file-name_123.txt")
        self.assertEqual(result, "file-name_123.txt")

    def test_get_valid_filename__with_unicode_characters(self):
        """Test that unicode characters are removed"""
        result = get_valid_filename("file\u2018name\u2019.txt")
        self.assertEqual(result, "filename.txt")

    def test_get_valid_filename__integer_input(self):
        """Test that integer input is converted to string"""
        result = get_valid_filename(12345)
        self.assertEqual(result, "12345")

    def test_get_valid_filename__float_input(self):
        """Test that float input is converted to string"""
        result = get_valid_filename(123.45)
        self.assertEqual(result, "123.45")

    def test_get_valid_filename__only_spaces(self):
        """Test that a string with only spaces returns empty string"""
        result = get_valid_filename("     ")
        self.assertEqual(result, "")

    def test_get_valid_filename__only_special_characters(self):
        """Test that a string with only special characters returns empty string"""
        result = get_valid_filename("!@#$%^&*()")
        self.assertEqual(result, "")

    def test_get_valid_filename__empty_string(self):
        """Test that an empty string returns empty string"""
        result = get_valid_filename("")
        self.assertEqual(result, "")

    def test_get_valid_filename__multiple_dots(self):
        """Test that multiple dots are preserved"""
        result = get_valid_filename("file.name.with.dots.txt")
        self.assertEqual(result, "file.name.with.dots.txt")

    def test_get_valid_filename__multiple_consecutive_spaces(self):
        """Test that multiple consecutive spaces are converted to single underscore"""
        result = get_valid_filename("file    name.txt")
        self.assertEqual(result, "file____name.txt")

    def test_get_valid_filename__mixed_case(self):
        """Test that case is preserved"""
        result = get_valid_filename("FileNameMixedCase.TXT")
        self.assertEqual(result, "FileNameMixedCase.TXT")


class GetResponseDataTestCase(unittest.TestCase):
    """Test cases for get_response_data function"""

    def test_get_response_data__valid_json(self):
        """Test that valid JSON is returned as dict"""
        mock_response = Mock()
        mock_response.json.return_value = {"key": "value"}

        result = get_response_data(mock_response)

        self.assertEqual(result, {"key": "value"})
        mock_response.json.assert_called_once()

    def test_get_response_data__invalid_json_returns_text(self):
        """Test that when JSON parsing fails, text is returned"""
        mock_response = Mock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.text = "Plain text response"

        result = get_response_data(mock_response)

        self.assertEqual(result, "Plain text response")
        mock_response.json.assert_called_once()

    def test_get_response_data__empty_json(self):
        """Test that empty JSON dict is returned correctly"""
        mock_response = Mock()
        mock_response.json.return_value = {}

        result = get_response_data(mock_response)

        self.assertEqual(result, {})

    def test_get_response_data__json_array(self):
        """Test that JSON array is returned correctly"""
        mock_response = Mock()
        mock_response.json.return_value = [1, 2, 3]

        result = get_response_data(mock_response)

        self.assertEqual(result, [1, 2, 3])

    def test_get_response_data__json_null(self):
        """Test that JSON null is returned correctly"""
        mock_response = Mock()
        mock_response.json.return_value = None

        result = get_response_data(mock_response)

        self.assertIsNone(result)

    def test_get_response_data__empty_text(self):
        """Test that empty text is returned when JSON parsing fails"""
        mock_response = Mock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.text = ""

        result = get_response_data(mock_response)

        self.assertEqual(result, "")


class CheckResponseTestCase(unittest.TestCase):
    """Test cases for check_response function"""

    def test_check_response__status_200_returns_true(self):
        """Test that status code 200 returns True"""
        mock_response = Mock()
        mock_response.status_code = 200

        result = check_response(mock_response)

        self.assertTrue(result)

    def test_check_response__status_201_returns_true(self):
        """Test that status code 201 returns True"""
        mock_response = Mock()
        mock_response.status_code = 201

        result = check_response(mock_response)

        self.assertTrue(result)

    def test_check_response__status_204_returns_true(self):
        """Test that status code 204 returns True"""
        mock_response = Mock()
        mock_response.status_code = 204

        result = check_response(mock_response)

        self.assertTrue(result)

    def test_check_response__status_298_returns_true(self):
        """Test that status code 298 returns True (upper boundary)"""
        mock_response = Mock()
        mock_response.status_code = 298

        result = check_response(mock_response)

        self.assertTrue(result)

    def test_check_response__status_102_returns_true(self):
        """Test that status code 102 returns True (lower boundary)"""
        mock_response = Mock()
        mock_response.status_code = 102

        result = check_response(mock_response)

        self.assertTrue(result)

    def test_check_response__status_401_raises_auth_error(self):
        """Test that status code 401 raises AuthError"""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"error": "Unauthorized"}

        with self.assertRaises(AuthError) as context:
            check_response(mock_response)

        self.assertIn("401", str(context.exception.value))
        self.assertIn("Access Token Error", str(context.exception.value))

    def test_check_response__status_403_raises_auth_error(self):
        """Test that status code 403 raises AuthError"""
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.json.return_value = {"error": "Forbidden"}

        with self.assertRaises(AuthError) as context:
            check_response(mock_response)

        self.assertIn("403", str(context.exception.value))
        self.assertIn("Access Token Error", str(context.exception.value))

    def test_check_response__status_401_with_text_message(self):
        """Test that status code 401 with text response includes message"""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.text = "Authentication failed"

        with self.assertRaises(AuthError) as context:
            check_response(mock_response)

        self.assertIn("Authentication failed", str(context.exception.value))

    def test_check_response__status_403_with_json_message(self):
        """Test that status code 403 with JSON response includes message"""
        mock_response = Mock()
        mock_response.status_code = 403
        error_message = {"error": {"code": "Forbidden", "message": "Access denied"}}
        mock_response.json.return_value = error_message

        with self.assertRaises(AuthError) as context:
            check_response(mock_response)

        self.assertIn(str(error_message), str(context.exception.value))

    def test_check_response__status_400_raises_request_error(self):
        """Test that status code 400 raises RequestError"""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"error": "Bad request"}

        with self.assertRaises(RequestError) as context:
            check_response(mock_response)

        self.assertIn("invalid", str(context.exception.value))

    def test_check_response__status_400_with_text_message(self):
        """Test that status code 400 with text response includes message"""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.text = "Invalid request parameters"

        with self.assertRaises(RequestError) as context:
            check_response(mock_response)

        self.assertIn("Invalid request parameters", str(context.exception.value))

    def test_check_response__status_400_with_json_message(self):
        """Test that status code 400 with JSON response includes message"""
        mock_response = Mock()
        mock_response.status_code = 400
        error_message = {"error": {"code": "BadRequest", "message": "Missing parameter"}}
        mock_response.json.return_value = error_message

        with self.assertRaises(RequestError) as context:
            check_response(mock_response)

        self.assertIn(str(error_message), str(context.exception.value))

    def test_check_response__status_500_raises_api_error(self):
        """Test that status code 500 raises APIError"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"error": "Internal server error"}

        with self.assertRaises(APIError) as context:
            check_response(mock_response)

        self.assertIn("unknown error", str(context.exception.value))

    def test_check_response__status_404_raises_api_error(self):
        """Test that status code 404 raises APIError"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"error": "Not found"}

        with self.assertRaises(APIError) as context:
            check_response(mock_response)

        self.assertIn("unknown error", str(context.exception.value))

    def test_check_response__status_405_raises_api_error(self):
        """Test that status code 405 raises APIError"""
        mock_response = Mock()
        mock_response.status_code = 405
        mock_response.json.return_value = {"error": "Method not allowed"}

        with self.assertRaises(APIError) as context:
            check_response(mock_response)

        self.assertIn("unknown error", str(context.exception.value))

    def test_check_response__status_502_raises_api_error(self):
        """Test that status code 502 raises APIError"""
        mock_response = Mock()
        mock_response.status_code = 502
        mock_response.json.return_value = {"error": "Bad gateway"}

        with self.assertRaises(APIError) as context:
            check_response(mock_response)

        self.assertIn("unknown error", str(context.exception.value))

    def test_check_response__status_503_raises_api_error(self):
        """Test that status code 503 raises APIError"""
        mock_response = Mock()
        mock_response.status_code = 503
        mock_response.json.return_value = {"error": "Service unavailable"}

        with self.assertRaises(APIError) as context:
            check_response(mock_response)

        self.assertIn("unknown error", str(context.exception.value))

    def test_check_response__api_error_with_text_message(self):
        """Test that APIError with text response includes message"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.text = "Server error occurred"

        with self.assertRaises(APIError) as context:
            check_response(mock_response)

        self.assertIn("Server error occurred", str(context.exception.value))

    def test_check_response__status_100_boundary(self):
        """Test that status code 100 (boundary) does not return True"""
        mock_response = Mock()
        mock_response.status_code = 100
        mock_response.json.return_value = {"error": "Continue"}

        with self.assertRaises(APIError):
            check_response(mock_response)

    def test_check_response__status_101_boundary(self):
        """Test that status code 101 (boundary) does not return True"""
        mock_response = Mock()
        mock_response.status_code = 101
        mock_response.json.return_value = {"error": "Switching Protocols"}

        # 101 is in the range 100 < status_code < 299, so it should return True
        result = check_response(mock_response)
        self.assertTrue(result)

    def test_check_response__status_299_boundary(self):
        """Test that status code 299 (boundary) does not return True"""
        mock_response = Mock()
        mock_response.status_code = 299
        mock_response.json.return_value = {"error": "Custom"}

        with self.assertRaises(APIError):
            check_response(mock_response)

    def test_check_response__status_300_raises_api_error(self):
        """Test that status code 300 raises APIError"""
        mock_response = Mock()
        mock_response.status_code = 300
        mock_response.json.return_value = {"error": "Multiple choices"}

        with self.assertRaises(APIError) as context:
            check_response(mock_response)

        self.assertIn("unknown error", str(context.exception.value))


if __name__ == '__main__':
    unittest.main()
