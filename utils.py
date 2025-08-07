import os
from azure.communication.email import EmailClient
import logging

def send_email_via_acs(to_email: str, subject: str, plain_text: str, html_content: str) -> bool:
    """
    Sends an email using Azure Communication Services Email.
    Returns True if sent successfully, False otherwise.
    """
    acs_conn_str = os.getenv('AZURE_COMMUNICATION_EMAIL_CONNECTION_STRING')
    sender = os.getenv('AZURE_COMMUNICATION_EMAIL_SENDER')
    if not acs_conn_str or not sender:
        logging.error("Email service not configured.")
        return False
    try:
        email_client = EmailClient.from_connection_string(acs_conn_str)
        message = {
            "senderAddress": sender,
            "recipients": {"to": [{"address": to_email}]},
            "content": {
                "subject": subject,
                "plainText": plain_text,
                "html": html_content
            }
        }
        poller = email_client.begin_send(message)
        poller.result()
        return True
    except Exception as e:
        logging.error(f"Failed to send email: {e}")
        return False