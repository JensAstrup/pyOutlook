# Development Guide

This guide covers how to develop and test pyOutlook functionality.

## Table of Contents

- [Getting an Access Token for Testing](#getting-an-access-token-for-testing)
- [Testing the Library](#testing-the-library)
- [Running Tests](#running-tests)
- [Token Expiration](#token-expiration)

## Getting an Access Token for Testing

The quickest way to get an access token for testing is using Microsoft Graph Explorer:

### Step 1: Open Microsoft Graph Explorer

Navigate to [Microsoft Graph Explorer](https://developer.microsoft.com/en-us/graph/graph-explorer)

### Step 2: Sign In

Click **Sign in with Microsoft** and authenticate with:
- Your personal Microsoft/Outlook account, or
- Your business/organizational account (e.g., name@company.onmicrosoft.com)

### Step 3: Get Your Access Token

1. Once signed in, click the **Access Token** button in the top toolbar
2. A dialog will appear showing your current access token
3. Click **Copy** to copy the token to your clipboard

### Step 4: Use the Token

You can now use this token to test pyOutlook functionality:

```python
from pyOutlook import OutlookAccount

# Paste your token here
token = 'eyJ0eXAiOiJKV1QiLCJub25jZSI6...'  # Your token from Graph Explorer

# Create account instance
account = OutlookAccount(token)

# Test basic functionality
messages = account.inbox()
print(f'Successfully retrieved {len(messages)} messages')

# Test other features
folders = account.get_folders()
print(f'Found {len(folders)} folders')
```

## Running Tests

### Install Development Dependencies

```bash
pip install -r requirements.dev.txt
```

### Run the Test Suite

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/pyOutlook --cov-report=html

# Run specific test file
pytest tests/test_message.py

# Run with verbose output
pytest -v
```

### Manual Integration Testing

For integration tests that require a real Outlook account:

1. Get an access token using the method described above
2. Set it as an environment variable:
   ```bash
   export OUTLOOK_ACCESS_TOKEN='your_token_here'
   ```
3. Run integration tests:
   ```python
   import os
   from pyOutlook import OutlookAccount
   
   token = os.environ.get('OUTLOOK_ACCESS_TOKEN')
   if not token:
       raise ValueError('Please set OUTLOOK_ACCESS_TOKEN environment variable')
   
   account = OutlookAccount(token)
   # Run your tests here
   ```

## Token Expiration

⚠️ **Important**: Access tokens from Microsoft Graph Explorer expire after approximately **1 hour**.

### When Your Token Expires

You'll see errors like:
- `401 Unauthorized`
- `Access token has expired`
- Authentication-related error messages

## Resources

- [Microsoft Graph API Documentation](https://docs.microsoft.com/en-us/graph/api/overview)
- [Microsoft Graph Explorer](https://developer.microsoft.com/en-us/graph/graph-explorer)
- [pyOutlook Documentation](http://pyoutlook.readthedocs.io/)
- [Outlook REST API Reference](https://docs.microsoft.com/en-us/graph/api/resources/mail-api-overview)
