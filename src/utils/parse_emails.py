from bs4 import BeautifulSoup
import requests
import os
from urllib.parse import urljoin, urlparse

def recursive_function(table):

    print("################ IN RECURSIVE FUNCTION ######################")

    # Since the input is a <table>, we expect it to have rows and data. We cycle through them 
    for tr in table.find_all("tr", recursive=False):  # Only direct <tr> children
        for td in tr.find_all("td", recursive=False):  # Only direct <td> children
            
            # Cycle through the tags of the TD 
            for tag in td.children:
                if tag.name == "h3":
                    print(f'H3 found: {tag}')
                elif tag.name == "h6":
                    print(f'H6 found: {tag}')
                elif tag.name == "p":
                    print(f'P found: {tag}')
                elif tag.name == "table":
                    print("TABLE")
                    ok = recursive_function(tag)
                else:
                    if tag.name:
                        print(f'Tag Name: {tag.name}')
                    print(f'Tag: {tag}')

    return True

class ParseEmails:

    def __init__(self):
        pass

    def parse_email_body(self, message, from_address):

        # The emails are made of multiple parts, one of which is HTML and it's the one we are interested in
        for part in message.walk():

            content_type = part.get_content_type()
            
            try:
                # Use the HTML version of the email - it is easier to parse
                if content_type == "text/html":
                    charset = part.get_content_charset()  # Get the correct encoding
                    if charset is None:
                        charset = "utf-8"  # Default to UTF-8 if unknown
                    
                    content = part.get_payload(decode=True).decode(charset, errors="replace")

            except Exception as e:
                print(f"Error processing part {content_type}: {str(e)}")
                continue
        
        # Use a switch to invoke the different parsers for each email 
        if from_address == "news@daily.therundown.ai":
            content = self.rundown_ai(content)

        return content
    
    # Rundown AI
    def rundown_ai(self, content):

        soup = BeautifulSoup(content, 'html.parser')
        soup = soup.find("body")

        for tag in soup.div.children:

            if tag.name == "table":
                ok = recursive_function(tag)

                if ok:
                    print('PORCODDIO')

            else:
                if tag.name == "div":
                    print(tag)
                elif tag.name:
                    print(f'Tag Name: {tag.name}')
                else:
                    print(f'Tag: {tag}')

        return "dhn"

        # Find all cells that contain a header
        # We need to use an auxiliary function to do it, it is defined above outside the class
        header_cells = soup.find_all(contains_header) # <- THIS IS STILL NOT WORKING PORCODDIO CANE MADONNA PUTTANA
        
        for header_cell in header_cells:
            # Get the section title from the header
            header = header_cell.find(['h3', 'h6'])
            section_title = header.get_text().strip()
                
            if "presented by" in section_title or "together with" in section_title:
                continue
            # Only process this section if it's of interest
            else:
                print("#########################")
                print(section_title)
                print(header_cell)
                break

                # Get all following sibling tds in the same row
                content_parts = []
                current_cell = header_cell.find_next_sibling('td')
                
                while current_cell:
                    content = current_cell.get_text().strip()
                    if content:  # Only add non-empty content
                        content_parts.append(content)
                    current_cell = current_cell.find_next_sibling('td')

                print('\n'.join(content_parts))

        print("Success!")
        return content