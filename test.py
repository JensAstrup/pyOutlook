import pyOutlook
import base64
import requests


# My token is stored in firebase
def get_auth(db, email):
    email64 = base64.b64encode(email)
    r = requests.get('https://' + db + '.firebaseio.com/outlookCreds/' + email64 + '.json')
    result = r.json()
    return result['access']


def test_all(db, email):
    auth = get_auth(db, email)
    account = pyOutlook.OutlookAccount(auth)

    # Get emails
    inbox = account.get_inbox()
    print(inbox)
    print(account.get_message(inbox[0].message_id))
    print(account.get_messages())
    print(account.get_more_messages(2))

    # Folders
    folder_list = account.get_folders()
    print(folder_list)
    print(account.get_folder(folder_list[0].id))
    print(account.get_folder_messages(folder_list[0].id))

    new_folder = account.create_folder(folder_list[0].id, 'Testing Folder')

    print(new_folder.id)
    new_folder.get_subfolders()
    temp_folder = new_folder.copy_folder('DeletedItems')
    temp_folder.delete_folder()
    new_folder.rename_folder('Renamed Folder')
    new_folder.delete_folder()

    # Send email
    email = account.new_email()
    email.to(email).set_subject('Test Subject').set_body('Test <br> Body').send()