import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv
from emd import sync_emails_to_weaviate

load_dotenv()

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


from datetime import datetime

from dataclasses import dataclass
from typing import List

from typing import Optional

@dataclass
class StructuredEmail:
    subject: str
    sender: str
    recipient: str
    date: datetime
    body: str
    message_id: str
    thread_id: str
    reply_body: Optional[str] = None

def get_structured_emails(AFTER_DATE: datetime, MAX_EMAILS: int) -> List[StructuredEmail]:
    """
    Authenticates, fetches threads after AFTER_DATE with at least one reply (up to MAX_EMAILS),
    and returns structured email objects (original + first reply) for each thread.
    """
    import os
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError

    SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    structured = []
    try:
        service = build("gmail", "v1", credentials=creds)
        threads = get_threads_with_replies_after_date(service, "me", AFTER_DATE, MAX_EMAILS)
        for t in threads:
            orig = get_email_content(service, "me", t['original_id'])
            reply = get_email_content(service, "me", t['first_reply_id'])
            # Get message dates and sender/recipient from metadata
            orig_msg = service.users().messages().get(userId="me", id=t['original_id'], format='metadata').execute()
            reply_msg = service.users().messages().get(userId="me", id=t['first_reply_id'], format='metadata').execute()
            # Extract sender, recipient, and date
            def extract_headers(msg):
                headers = msg.get('payload', {}).get('headers', [])
                sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), None)
                recipient = next((h['value'] for h in headers if h['name'].lower() == 'to'), None)
                date_str = next((h['value'] for h in headers if h['name'].lower() == 'date'), None)
                from email.utils import parsedate_to_datetime
                date = parsedate_to_datetime(date_str) if date_str else None
                return sender, recipient, date
            orig_sender, orig_recipient, orig_date = extract_headers(orig_msg)
            reply_sender, reply_recipient, reply_date = extract_headers(reply_msg)
            orig_message_id = orig_msg.get('id')
            orig_thread_id = orig_msg.get('threadId')
            reply_message_id = reply_msg.get('id')
            reply_thread_id = reply_msg.get('threadId')
            # Build StructuredEmail for the original message, include first reply's body as reply_body
            structured.append(
                StructuredEmail(
                    subject=orig['subject'],
                    sender=orig_sender,
                    recipient=orig_recipient,
                    date=orig_date,
                    message_id=orig_message_id,
                    thread_id=orig_thread_id,
                    body=orig['body'],
                    reply_body=reply['body'] if reply and reply.get('body') else None
                )
            )
            if len(structured) >= MAX_EMAILS:
                break
    except HttpError as error:
        print(f"An error occurred: {error}")
    return structured[:MAX_EMAILS]


def get_threads_with_replies_before(service, user_id, cutoff_date):
    """
    Fetch all email threads that have at least one reply before the given cutoff_date.
    cutoff_date: datetime object (UTC)
    Returns: List of thread IDs
    """
    threads_with_replies = []
    cutoff_ts = int(cutoff_date.timestamp())
    next_page_token = None
    while True:
        threads_response = service.users().threads().list(userId=user_id, pageToken=next_page_token, maxResults=100).execute()
        threads = threads_response.get('threads', [])
        for thread in threads:
            thread_id = thread['id']
            thread_data = service.users().threads().get(userId=user_id, id=thread_id, format='metadata').execute()
            messages = thread_data.get('messages', [])
            if len(messages) > 1:  # Has replies
                # The first message is the original, the rest are replies
                for msg in messages[1:]:
                    internal_date = int(msg['internalDate']) // 1000  # Gmail gives ms
                    if internal_date < cutoff_ts:
                        threads_with_replies.append(thread_id)
                        break
        next_page_token = threads_response.get('nextPageToken')
        if not next_page_token:
            break
    return threads_with_replies

def get_threads_with_replies_after_date(service, user_id, after_date, max_threads):
    """
    Fetch threads after a specific date that have at least one reply.
    Args:
        service: Gmail API service instance.
        user_id: Gmail user ID (usually 'me').
        after_date: datetime object (UTC), only threads after this date are fetched.
        max_threads: int, maximum number of threads to fetch.
    Returns:
        List of dicts: [{ 'thread_id': str, 'original_id': str, 'first_reply_id': str }]
    """
    threads_with_replies = []
    after_ts = int(after_date.timestamp())
    next_page_token = None
    while len(threads_with_replies) < max_threads:
        # Query for threads after the given date
        query = f"after:{after_ts}"
        response = service.users().threads().list(
            userId=user_id,
            q=query,
            pageToken=next_page_token,
            maxResults=min(100, max_threads - len(threads_with_replies))
        ).execute()
        threads = response.get('threads', [])
        for thread in threads:
            thread_id = thread['id']
            thread_data = service.users().threads().get(userId=user_id, id=thread_id, format='metadata').execute()
            messages = thread_data.get('messages', [])
            if len(messages) > 1:
                # Has at least one reply
                original_id = messages[0]['id']
                first_reply_id = messages[1]['id']
                threads_with_replies.append({
                    'thread_id': thread_id,
                    'original_id': original_id,
                    'first_reply_id': first_reply_id
                })
                if len(threads_with_replies) >= max_threads:
                    break
        next_page_token = response.get('nextPageToken')
        if not next_page_token or len(threads_with_replies) >= max_threads:
            break
    return threads_with_replies

def get_email_content(service, user_id, msg_id):
    """
    Fetch the subject and plain text content of an email message by its ID.
    Args:
        service: Gmail API service instance.
        user_id: Gmail user ID (usually 'me').
        msg_id: The message ID to fetch.
    Returns:
        Dict with 'subject' and 'body' (plain text, or None if not found).
    """
    msg = service.users().messages().get(userId=user_id, id=msg_id, format='full').execute()
    # Extract subject from headers
    headers = msg.get('payload', {}).get('headers', [])
    subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), None)
    # Extract plain text body
    def get_plain_body(payload):
        if payload.get('mimeType') == 'text/plain' and 'data' in payload.get('body', {}):
            import base64
            return base64.urlsafe_b64decode(payload['body']['data']).decode(errors='replace')
        elif 'parts' in payload:
            for part in payload['parts']:
                text = get_plain_body(part)
                if text:
                    return text
        return None
    body = get_plain_body(msg.get('payload', {}))
    return {'subject': subject, 'body': body}


if __name__ == "__main__":
    # --- User-defined variables ---
    AFTER_DATE = datetime(2025, 1, 1)  # Change as needed
    MAX_EMAILS = 100  # Change as needed
    # Fetch emails in structured format
    emails = get_structured_emails(AFTER_DATE, MAX_EMAILS)
    # Sync emails to Weaviate
    sync_emails_to_weaviate(emails)
    