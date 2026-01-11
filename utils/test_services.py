#!/usr/bin/env python
"""
Comprehensive test script for pyOutlook library services.

This script tests all methods from MessageService, FolderService, and ContactService
using a real Outlook account access token.

Usage:
    python test_services.py [access_token]
    ACCESS_TOKEN=your_token python test_services.py
"""

import sys
import os
import base64
from pathlib import Path
from typing import Optional

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from pyOutlook import OutlookAccount, Contact, Attachment

# Default test email address
TEST_EMAIL = 'jensaiden@gmail.com'


def get_access_token() -> Optional[str]:
    """Get access token from command line argument or environment variable."""
    if len(sys.argv) > 1:
        return sys.argv[1]
    return os.environ.get('ACCESS_TOKEN')


def print_section(title: str):
    """Print a formatted section header."""
    print('\n' + '=' * 80)
    print(f'  {title}')
    print('=' * 80)


def print_success(message: str, indent: int = 0):
    """Print a success message."""
    prefix = '  ' * indent
    print(f'{prefix}✓ {message}')


def print_error(message: str, indent: int = 0):
    """Print an error message."""
    prefix = '  ' * indent
    print(f'{prefix}✗ {message}')


def test_account_creation(access_token: str) -> Optional[OutlookAccount]:
    """Test creating an OutlookAccount instance."""
    print_section('Testing Account Creation')
    
    try:
        account = OutlookAccount(access_token)
        print_success('OutlookAccount created successfully')
        print(f'  - Messages service: {account.messages}')
        print(f'  - Folders service: {account.folders}')
        print(f'  - Contacts service: {account.contacts}')
        return account
    except Exception as e:
        print_error(f'Failed to create OutlookAccount: {e}')
        return None


def test_folder_service(account: OutlookAccount) -> bool:
    """Test FolderService methods."""
    print_section('Testing Folder Service')
    success = True
    
    # Test: Get all folders
    try:
        folders = account.folders.all()
        print_success(f'Retrieved {len(folders)} folders')
        for folder in folders[:5]:  # Show first 5
            print(f'  - {folder.name}: {folder.unread_count} unread, {folder.total_items} total')
    except Exception as e:
        print_error(f'Failed to get all folders: {e}')
        success = False
    
    # Test: Get specific folder by name
    try:
        inbox_folder = account.folders.get('Inbox')
        print_success('Retrieved Inbox folder')
        print(f'  - Name: {inbox_folder.name}')
        print(f'  - ID: {inbox_folder.id}')
        print(f'  - Unread: {inbox_folder.unread_count}')
        print(f'  - Total: {inbox_folder.total_items}')
    except Exception as e:
        print_error(f'Failed to get Inbox folder: {e}')
        success = False
    
    return success


def test_message_service_retrieval(account: OutlookAccount) -> bool:
    """Test MessageService retrieval methods."""
    print_section('Testing Message Service - Retrieval')
    success = True
    messages = []
    
    # Test: Get all messages (page 0)
    try:
        messages = account.messages.all()
        print_success(f'Retrieved {len(messages)} messages from all()')
        if messages:
            msg = messages[0]
            print(f'  - First message: "{msg.subject}"')
            print(f'    From: {msg.sender.email}')
            print(f'    Is read: {msg.is_read}')
    except Exception as e:
        print_error(f'Failed to get all messages: {e}')
        success = False
    
    # Test: Get inbox messages
    try:
        inbox_messages = account.inbox()
        print_success(f'Retrieved {len(inbox_messages)} messages from inbox()')
        if inbox_messages:
            msg = inbox_messages[0]
            print(f'  - First inbox message: "{msg.subject}"')
            if not messages:
                messages = inbox_messages
    except Exception as e:
        print_error(f'Failed to get inbox messages: {e}')
        success = False
    
    # Test: Get sent messages
    try:
        sent_messages = account.sent_messages()
        print_success(f'Retrieved {len(sent_messages)} sent messages')
        if sent_messages:
            msg = sent_messages[0]
            print(f'  - First sent message: "{msg.subject}"')
    except Exception as e:
        print_error(f'Failed to get sent messages: {e}')
        success = False
    
    # Test: Get draft messages
    try:
        draft_messages = account.draft_messages()
        print_success(f'Retrieved {len(draft_messages)} draft messages')
    except Exception as e:
        print_error(f'Failed to get draft messages: {e}')
        success = False
    
    # Test: Get messages from a specific folder
    try:
        folder_messages = account.messages.from_folder('Inbox')
        print_success(f'Retrieved {len(folder_messages)} messages from folder "Inbox"')
    except Exception as e:
        print_error(f'Failed to get messages from folder: {e}')
        success = False
    
    # Test: Get a specific message by ID (if we have one)
    if messages:
        try:
            message_id = messages[0].id
            retrieved_message = account.messages.get(message_id)
            print_success('Retrieved specific message by ID')
            print(f'  - Subject: "{retrieved_message.subject}"')
            preview = retrieved_message.body_preview[:50] if retrieved_message.body_preview else 'N/A'
            print(f'  - Body preview: {preview}...')
        except Exception as e:
            print_error(f'Failed to get message by ID: {e}')
            success = False
    
    return success


def test_message_service_sending(account: OutlookAccount, test_email: str) -> bool:
    """Test MessageService sending methods."""
    print_section('Testing Message Service - Sending')
    success = True
    
    # Test: Send simple email
    try:
        account.messages.send(
            subject='Test Email from pyOutlook',
            body='<p>This is a test email sent using the pyOutlook library.</p><p>Best regards,<br>Test Script</p>',
            to=[test_email]
        )
        print_success(f'Sent simple email to {test_email}')
    except Exception as e:
        print_error(f'Failed to send simple email: {e}')
        success = False
    
    # Test: Send email with Contact object
    try:
        account.messages.send(
            subject='Test Email with Contact Object',
            body='<p>This email uses a Contact object for the recipient.</p>',
            to=[Contact(test_email, name='Jens Test')]
        )
        print_success(f'Sent email with Contact object to {test_email}')
    except Exception as e:
        print_error(f'Failed to send email with Contact: {e}')
        success = False
    
    # Test: Send email with CC and BCC
    try:
        account.messages.send(
            subject='Test Email with CC and BCC',
            body='<p>This email includes CC and BCC recipients (both to the same address for testing).</p>',
            to=[test_email],
            cc=[test_email],
            bcc=[test_email]
        )
        print_success(f'Sent email with CC and BCC to {test_email}')
    except Exception as e:
        print_error(f'Failed to send email with CC/BCC: {e}')
        success = False
    
    # Test: Send email with attachment
    try:
        # Create a simple text file attachment
        test_content = 'This is a test attachment from pyOutlook library.'
        encoded_content = base64.b64encode(test_content.encode('utf-8')).decode('utf-8')
        
        attachment = Attachment(
            name='test_attachment.txt',
            content=encoded_content,
            content_type='text/plain'
        )
        
        account.messages.send(
            subject='Test Email with Attachment',
            body='<p>This email includes a text file attachment.</p>',
            to=[test_email],
            attachments=[attachment]
        )
        print_success(f'Sent email with attachment to {test_email}')
    except Exception as e:
        print_error(f'Failed to send email with attachment: {e}')
        success = False
    
    return success


def test_contact_service(account: OutlookAccount) -> bool:
    """Test ContactService methods."""
    print_section('Testing Contact Service')
    success = True
    
    # Test: Get contact overrides
    try:
        overrides = account.contacts.get_overrides()
        print_success(f'Retrieved {len(overrides)} contact overrides')
        for contact in overrides[:5]:  # Show first 5
            if contact:
                focused_status = 'Focused' if contact.focused else 'Other'
                print(f'  - {contact.email} ({contact.name}): {focused_status}')
    except Exception as e:
        print_error(f'Failed to get contact overrides: {e}')
        success = False
    
    return success


def test_contact_operations(account: OutlookAccount, test_email: str) -> bool:
    """Test Contact class operations."""
    print_section('Testing Contact Operations')
    success = True
    
    # Test: Create a Contact and convert to dict
    try:
        contact = Contact(test_email, name='Test User')
        contact_dict = dict(contact)
        print_success('Created Contact and converted to dict')
        print(f'  - Contact: {contact}')
        print(f'  - Dict format: {contact_dict}')
    except Exception as e:
        print_error(f'Failed to create/convert Contact: {e}')
        success = False
    
    return success


def main():
    """Main test runner."""
    print('\n' + '█' * 80)
    print('█' + ' ' * 78 + '█')
    print('█' + '  pyOutlook Library Service Test Suite'.center(78) + '█')
    print('█' + ' ' * 78 + '█')
    print('█' * 80)
    
    # Get access token
    access_token = get_access_token()
    if not access_token:
        print('\nError: Access token required!')
        print('\nUsage:')
        print('  python test_services.py <access_token>')
        print('  ACCESS_TOKEN=<token> python test_services.py')
        sys.exit(1)
    
    # Create account
    account = test_account_creation(access_token)
    if not account:
        print('\n✗ Cannot continue without a valid account')
        sys.exit(1)
    
    # Run tests
    results = {
        'folder_service': test_folder_service(account),
        'message_retrieval': test_message_service_retrieval(account),
        'message_sending': test_message_service_sending(account, TEST_EMAIL),
        'contact_service': test_contact_service(account),
        'contact_operations': test_contact_operations(account, TEST_EMAIL),
    }
    
    # Summary
    print_section('Test Summary')
    total_tests = len(results)
    passed_tests = sum(1 for v in results.values() if v)
    failed_tests = total_tests - passed_tests
    
    print(f'Total test suites: {total_tests}')
    print(f'Passed: {passed_tests}')
    print(f'Failed: {failed_tests}')
    
    if failed_tests > 0:
        print('\nFailed test suites:')
        for test_name, result in results.items():
            if not result:
                print(f'  - {test_name}')
    
    print(f'\nTest emails sent to: {TEST_EMAIL}')
    
    # Exit with appropriate code
    sys.exit(0 if failed_tests == 0 else 1)


if __name__ == '__main__':
    main()
