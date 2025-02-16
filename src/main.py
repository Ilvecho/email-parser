import imaplib
import email
import os
import requests
from pathlib import Path
from dotenv import load_dotenv
from email.header import decode_header
from bs4 import BeautifulSoup
from urllib.parse import unquote
import hashlib
import re
from urllib.parse import urljoin, urlparse
from utils import ParseEmails                       # My utils

load_dotenv(override=True)

TARGET_ADDRESS_ENG = [
    "theneuron@newsletter.theneurondaily.com",      # The Neuron - AI (ENG)
    "joe@readthejoe.com",                           # The Average Joe - Business and Finance(ENG)
    "news@daily.therundown.ai",                     # The rundown - AI (ENG)
    "dan@tldrnewsletter.com",                       # TL;DR - AI and tech (ENG)
    "chamath@substack.com",                         # Chamath Palihapitiya - Business, Tech, AI (ENG)
]

TARGET_ADDRESS_ITA = [
    # "team@ilpuntonewsletter.com",                   # Il Punto - Economia Italiana (ITA) <- Too unpredictable and with several meaningful images, not worth parsing
    "news@myanalitica.it",                          # My Analitica di Pietro Michelangeli - Finanza (ITA)
    "community@datapizza.it"                        # Datapizza - AI e Data Science (ITA)
]

class YahooEmailExtractor:
    def __init__(self, email_address, app_password):
        """
        Initialize the Yahoo email extractor.
        
        Args:
            email_address: Your Yahoo email address
            app_password: App-specific password generated from Yahoo account settings
        """
        self.email_address = email_address
        self.password = app_password
        self.imap_server = "imap.mail.yahoo.com"
        
    def connect(self):
        """Establish connection to Yahoo's IMAP server"""
        self.imap = imaplib.IMAP4_SSL(self.imap_server)
        try:
            self.imap.login(self.email_address, self.password)
            return True
        except Exception as e:
            print(f"Login failed: {str(e)}")
            return False

    def extract_email_address(self, header_value):
        if not header_value:
            return ""
            
        # Handle multiple email addresses
        if ',' in header_value:
            addresses = header_value.split(',')
            return [self._extract_single_email(addr.strip()) for addr in addresses]
        
        return self._extract_single_email(header_value)
    
    def _extract_single_email(self, address):
        # Handle format: "Name" <email@example.com>
        if '<' in address and '>' in address:
            start = address.find('<') + 1
            end = address.find('>')
            return address[start:end]
        return address.strip()

    def parse_emails(self, num_emails, save_path):
        """
        Extract text and images from emails.
        
        Args:
            num_emails: Number of recent emails to process
            save_path: Directory to save extracted content
        """

        # Select inbox
        self.imap.select("INBOX", readonly=True)
        
        # Search for all emails
        _, message_numbers = self.imap.search(None, "UNSEEN")
        
        # Get the list of email IDs
        email_ids = message_numbers[0].split()
        
        if not email_ids:
            print("No unread emails found")
            return []
        
        # Process the most recent emails first
        emails_to_process = email_ids[-num_emails:] if num_emails else email_ids
        
        newsletters = []

        for email_id in emails_to_process:
            try:
                _, msg_data = self.imap.fetch(email_id, "(RFC822)")
                email_body = msg_data[0][1]
                message = email.message_from_bytes(email_body)
                
                # Extract email addresses
                from_address = self.extract_email_address(message['from'])
            
                # If not in scope, skip
                if not from_address in TARGET_ADDRESS_ENG and not from_address in TARGET_ADDRESS_ITA:
                    continue
                
                # Extract subject
                decoded_subject = decode_header(message["subject"])
                subject = ""

                for part, charset in decoded_subject:
                    if isinstance(part, bytes):
                        subject += part.decode(charset or 'utf-8', errors='replace')
                    else:
                        subject += str(part)

                newsletters.append({
                    'subject': subject,
                    'from': from_address
                })

                # print("\n####################")
                # print(str(newsletters[-1]))

                # Create a unique directory for each email
                email_dir = save_path / f"email_{email_id.decode()}"
                os.makedirs(email_dir, exist_ok=True)
                
                # Extract content and create summary
                parser = ParseEmails()
                content = parser.parse_email_body(message, from_address, email_dir)

                # # Save HTML summary
                # summary_path = os.path.join(email_dir, 'summary.html')
                # with open(summary_path, 'w', encoding='utf-8') as f:
                #     f.write(content)

                # Save TXT summary
                summary_path = os.path.join(email_dir, 'summary.txt')
                with open(summary_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
            except Exception as e:
                print(f"Error processing email {email_id}: {str(e)}")
                continue


    def disconnect(self):
        """Close the IMAP connection"""
        self.imap.close()
        self.imap.logout()

# Example usage
if __name__ == "__main__":

    EMAIL = os.getenv("EMAIL")
    APP_PASSWORD = os.getenv("APP_PASSWORD")
    
    extractor = YahooEmailExtractor(EMAIL, APP_PASSWORD)
    
    if extractor.connect():
        save_path = Path(__file__).parent / "email_content"
        extractor.parse_emails(num_emails=10, save_path=save_path)
        extractor.disconnect()
        print("Email content extraction completed!")

    # file_path = Path("C:/Users/massi/Documents/PythonProjects/email-parser/src/email_content/email_1780/summary.html")

    # with open(file_path, 'r', encoding='utf-8') as file:
    #     html_content = file.read()

    # parser = ParseEmails()
    # _ = parser.rundown_ai(html_content)