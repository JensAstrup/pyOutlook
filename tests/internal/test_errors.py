"""
Comprehensive unit tests for pyOutlook.internal.errors module.
Tests all error classes and their initialization logic branches.
"""

import unittest

from pyOutlook.internal.errors import (
    OutlookError,
    APIError,
    AuthError,
    RequestError,
    MiscError
)


class OutlookErrorTestCase(unittest.TestCase):
    """Test case for OutlookError base exception class."""

    def test_init__with_value(self):
        """Test OutlookError initialization with a value parameter."""
        error_value = "Test error message"
        error = OutlookError(value=error_value)

        self.assertEqual(error.value, error_value)
        self.assertIsInstance(error, Exception)

    def test_init__without_value(self):
        """Test OutlookError initialization without a value parameter (defaults to None)."""
        error = OutlookError()

        self.assertIsNone(error.value)
        self.assertIsInstance(error, Exception)

    def test_init__with_none_value(self):
        """Test OutlookError initialization with explicit None value."""
        error = OutlookError(value=None)

        self.assertIsNone(error.value)
        self.assertIsInstance(error, Exception)

    def test_init__with_complex_value(self):
        """Test OutlookError initialization with complex value types."""
        complex_value = {"error": "message", "code": 500}
        error = OutlookError(value=complex_value)

        self.assertEqual(error.value, complex_value)
        self.assertIsInstance(error.value, dict)

    def test_inheritance__is_exception(self):
        """Test that OutlookError is a subclass of Exception."""
        error = OutlookError()

        self.assertIsInstance(error, Exception)

    def test_raise__can_be_raised(self):
        """Test that OutlookError can be raised and caught."""
        error_value = "Test error"

        with self.assertRaises(OutlookError) as context:
            raise OutlookError(value=error_value)

        self.assertEqual(context.exception.value, error_value)


class APIErrorTestCase(unittest.TestCase):
    """Test case for APIError exception class."""

    def test_init__with_value(self):
        """Test APIError initialization with a value parameter."""
        error_value = "API error message"
        error = APIError(value=error_value)

        self.assertEqual(error.value, error_value)
        self.assertIsInstance(error, OutlookError)
        self.assertIsInstance(error, Exception)

    def test_init__without_value(self):
        """Test APIError initialization without a value parameter (defaults to None)."""
        error = APIError()

        self.assertIsNone(error.value)

    def test_init__with_none_value(self):
        """Test APIError initialization with explicit None value."""
        error = APIError(value=None)

        self.assertIsNone(error.value)

    def test_inheritance__is_outlook_error(self):
        """Test that APIError is a subclass of OutlookError."""
        error = APIError()

        self.assertIsInstance(error, OutlookError)
        self.assertIsInstance(error, Exception)

    def test_raise__can_be_raised(self):
        """Test that APIError can be raised and caught."""
        error_value = "API test error"

        with self.assertRaises(APIError) as context:
            raise APIError(value=error_value)

        self.assertEqual(context.exception.value, error_value)

    def test_raise__can_be_caught_as_outlook_error(self):
        """Test that APIError can be caught as OutlookError."""
        error_value = "API test error"

        with self.assertRaises(OutlookError) as context:
            raise APIError(value=error_value)

        self.assertEqual(context.exception.value, error_value)


class AuthErrorTestCase(unittest.TestCase):
    """Test case for AuthError exception class."""

    def test_init__with_value(self):
        """Test AuthError initialization with a custom value parameter."""
        error_value = "Custom auth error message"
        error = AuthError(value=error_value)

        self.assertEqual(error.value, error_value)
        self.assertIsInstance(error, APIError)
        self.assertIsInstance(error, OutlookError)

    def test_init__without_value(self):
        """Test AuthError initialization without value parameter (uses default message)."""
        error = AuthError()

        self.assertEqual(error.value, 'Access Token Error, double check your access token.')
        self.assertIsInstance(error, APIError)

    def test_init__with_none_value(self):
        """Test AuthError initialization with explicit None value (uses default message)."""
        error = AuthError(value=None)

        self.assertEqual(error.value, 'Access Token Error, double check your access token.')

    def test_init__with_empty_string_value(self):
        """Test AuthError initialization with empty string value."""
        error = AuthError(value="")

        self.assertEqual(error.value, "")
        # Empty string is truthy False in boolean context, but not None

    def test_init__with_zero_value(self):
        """Test AuthError initialization with zero value (falsy but not None)."""
        error = AuthError(value=0)

        self.assertEqual(error.value, 0)

    def test_init__with_false_value(self):
        """Test AuthError initialization with False value (falsy but not None)."""
        error = AuthError(value=False)

        self.assertEqual(error.value, False)

    def test_inheritance__is_api_error(self):
        """Test that AuthError is a subclass of APIError."""
        error = AuthError()

        self.assertIsInstance(error, APIError)
        self.assertIsInstance(error, OutlookError)
        self.assertIsInstance(error, Exception)

    def test_raise__can_be_raised(self):
        """Test that AuthError can be raised and caught."""
        error_value = "401 Unauthorized"

        with self.assertRaises(AuthError) as context:
            raise AuthError(value=error_value)

        self.assertEqual(context.exception.value, error_value)

    def test_raise__can_be_caught_as_api_error(self):
        """Test that AuthError can be caught as APIError."""
        with self.assertRaises(APIError):
            raise AuthError()

    def test_raise__can_be_caught_as_outlook_error(self):
        """Test that AuthError can be caught as OutlookError."""
        with self.assertRaises(OutlookError):
            raise AuthError()

    def test_default_message__exact_text(self):
        """Test that the default message text is exactly as specified."""
        error = AuthError()
        expected_message = 'Access Token Error, double check your access token.'

        self.assertEqual(error.value, expected_message)


class RequestErrorTestCase(unittest.TestCase):
    """Test case for RequestError exception class."""

    def test_init__with_value(self):
        """Test RequestError initialization with a value parameter."""
        error_value = "400 Bad Request"
        error = RequestError(value=error_value)

        self.assertEqual(error.value, error_value)
        self.assertIsInstance(error, APIError)
        self.assertIsInstance(error, OutlookError)

    def test_init__without_value(self):
        """Test RequestError initialization without a value parameter (defaults to None)."""
        error = RequestError()

        self.assertIsNone(error.value)

    def test_init__with_none_value(self):
        """Test RequestError initialization with explicit None value."""
        error = RequestError(value=None)

        self.assertIsNone(error.value)

    def test_init__with_dict_value(self):
        """Test RequestError initialization with dictionary value."""
        error_value = {"error_code": 400, "message": "Bad Request"}
        error = RequestError(value=error_value)

        self.assertEqual(error.value, error_value)
        self.assertIsInstance(error.value, dict)

    def test_inheritance__is_api_error(self):
        """Test that RequestError is a subclass of APIError."""
        error = RequestError()

        self.assertIsInstance(error, APIError)
        self.assertIsInstance(error, OutlookError)
        self.assertIsInstance(error, Exception)

    def test_raise__can_be_raised(self):
        """Test that RequestError can be raised and caught."""
        error_value = "Invalid request format"

        with self.assertRaises(RequestError) as context:
            raise RequestError(value=error_value)

        self.assertEqual(context.exception.value, error_value)

    def test_raise__can_be_caught_as_api_error(self):
        """Test that RequestError can be caught as APIError."""
        with self.assertRaises(APIError):
            raise RequestError(value="Test error")

    def test_raise__can_be_caught_as_outlook_error(self):
        """Test that RequestError can be caught as OutlookError."""
        with self.assertRaises(OutlookError):
            raise RequestError(value="Test error")


class MiscErrorTestCase(unittest.TestCase):
    """Test case for MiscError exception class."""

    def test_init__with_value(self):
        """Test MiscError initialization with a value parameter (required)."""
        error_value = "Miscellaneous error message"
        error = MiscError(value=error_value)

        self.assertEqual(error.value, error_value)
        self.assertIsInstance(error, OutlookError)
        self.assertIsInstance(error, Exception)

    def test_init__with_string_value(self):
        """Test MiscError initialization with string value."""
        error_value = "Something went wrong"
        error = MiscError(value=error_value)

        self.assertEqual(error.value, error_value)

    def test_init__with_none_value(self):
        """Test MiscError initialization with None value."""
        error = MiscError(value=None)

        self.assertIsNone(error.value)

    def test_init__with_integer_value(self):
        """Test MiscError initialization with integer value."""
        error_value = 12345
        error = MiscError(value=error_value)

        self.assertEqual(error.value, error_value)

    def test_init__with_dict_value(self):
        """Test MiscError initialization with dictionary value."""
        error_value = {"type": "misc", "details": "Unknown error"}
        error = MiscError(value=error_value)

        self.assertEqual(error.value, error_value)
        self.assertIsInstance(error.value, dict)

    def test_init__with_list_value(self):
        """Test MiscError initialization with list value."""
        error_value = ["error1", "error2", "error3"]
        error = MiscError(value=error_value)

        self.assertEqual(error.value, error_value)
        self.assertIsInstance(error.value, list)

    def test_inheritance__is_outlook_error(self):
        """Test that MiscError is a subclass of OutlookError."""
        error = MiscError(value="test")

        self.assertIsInstance(error, OutlookError)
        self.assertIsInstance(error, Exception)

    def test_inheritance__is_not_api_error(self):
        """Test that MiscError is NOT a subclass of APIError."""
        error = MiscError(value="test")

        self.assertNotIsInstance(error, APIError)

    def test_raise__can_be_raised(self):
        """Test that MiscError can be raised and caught."""
        error_value = "Misc test error"

        with self.assertRaises(MiscError) as context:
            raise MiscError(value=error_value)

        self.assertEqual(context.exception.value, error_value)

    def test_raise__can_be_caught_as_outlook_error(self):
        """Test that MiscError can be caught as OutlookError."""
        error_value = "Misc test error"

        with self.assertRaises(OutlookError) as context:
            raise MiscError(value=error_value)

        self.assertEqual(context.exception.value, error_value)

    def test_raise__cannot_be_caught_as_api_error(self):
        """Test that MiscError cannot be caught as APIError (different branch)."""
        with self.assertRaises(MiscError):
            try:
                raise MiscError(value="test")
            except APIError:
                self.fail("MiscError should not be catchable as APIError")
            # Re-raise to be caught by outer assertRaises


class ErrorHierarchyTestCase(unittest.TestCase):
    """Test case for the overall error hierarchy and relationships."""

    def test_hierarchy__outlook_error_is_base(self):
        """Test that OutlookError is the base for all custom errors."""
        self.assertTrue(issubclass(APIError, OutlookError))
        self.assertTrue(issubclass(AuthError, OutlookError))
        self.assertTrue(issubclass(RequestError, OutlookError))
        self.assertTrue(issubclass(MiscError, OutlookError))

    def test_hierarchy__api_error_subclasses(self):
        """Test that APIError has the correct subclasses."""
        self.assertTrue(issubclass(AuthError, APIError))
        self.assertTrue(issubclass(RequestError, APIError))
        self.assertFalse(issubclass(MiscError, APIError))

    def test_hierarchy__all_are_exceptions(self):
        """Test that all error classes are subclasses of Exception."""
        self.assertTrue(issubclass(OutlookError, Exception))
        self.assertTrue(issubclass(APIError, Exception))
        self.assertTrue(issubclass(AuthError, Exception))
        self.assertTrue(issubclass(RequestError, Exception))
        self.assertTrue(issubclass(MiscError, Exception))

    def test_catch_order__specific_before_general(self):
        """Test that specific exceptions can be caught before general ones."""
        caught_as = None

        try:
            raise AuthError(value="test")
        except AuthError:
            caught_as = "AuthError"
        except APIError:
            caught_as = "APIError"
        except OutlookError:
            caught_as = "OutlookError"

        self.assertEqual(caught_as, "AuthError")

    def test_catch_order__api_error_before_outlook_error(self):
        """Test that APIError can be caught before OutlookError."""
        caught_as = None

        try:
            raise RequestError(value="test")
        except APIError:
            caught_as = "APIError"
        except OutlookError:
            caught_as = "OutlookError"

        self.assertEqual(caught_as, "APIError")

    def test_catch_order__misc_error_not_api_error(self):
        """Test that MiscError is not caught by APIError handler."""
        caught_as = None

        try:
            raise MiscError(value="test")
        except APIError:
            caught_as = "APIError"
        except OutlookError:
            caught_as = "OutlookError"

        self.assertEqual(caught_as, "OutlookError")


if __name__ == '__main__':
    unittest.main()
