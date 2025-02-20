import re
from bs4 import BeautifulSoup
import requests
import os
from urllib.parse import urljoin, urlparse


class ParseEmails:

    def __init__(self):
        pass

    def parse_email_body(self, message, from_address, email_dir):

        # The emails are made of multiple parts, one of which is HTML and it's the one we are interested in
        for part in message.walk():

            content_type = part.get_content_type()

            try:
                # # Use the HTML version of the email - it is easier to parse <- Actually it's not, it's a shitshow
                # if content_type == "text/html":
                #     charset = part.get_content_charset()  # Get the correct encoding
                #     if charset is None:
                #         charset = "utf-8"  # Default to UTF-8 if unknown
                    
                #     content = part.get_payload(decode=True).decode(charset, errors="replace")
                
                if content_type == "text/plain":
                    # Get text
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

        elif from_address == "dan@tldrnewsletter.com":
            content = self.tldr(content)

        elif from_address == "joe@readthejoe.com":
            content = self.average_joe(content)

        elif from_address == "theneuron@newsletter.theneurondaily.com":
            content = self.neuron(content)
        
        elif from_address == "news@myanalitica.it":
            content = self.analitica(content)

        elif from_address == "community@datapizza.it":
            content = self.datapizza(content)

        return content
    
    # Rundown AI
    def rundown_ai(self, content):

        # Isolate only the part that is relevant
        content = content.split("**Good morning, AI enthusiasts.** ")[-1].split("**COMMUNITY**")[0]

        # Remove the links
        pattern = r'\(http.*?\)'
        content = re.sub(pattern, '', content)

        # Remove the sponsored parts
        pattern = r'###### TOGETHER WITH.*?----------'
        content = re.sub(pattern, '', content, flags=re.DOTALL)

        pattern = r'###### AI TRAINING.*?----------'
        content = re.sub(pattern, '', content, flags=re.DOTALL)

        pattern = r'###### PRESENTED BY.*?----------'
        content = re.sub(pattern, '', content, flags=re.DOTALL)

        # Remove Trending tools & Jobs
        pattern = r'### 🛠️ _\*\*\[Trending AI Tools\]\*\*_.*?----------'
        content = re.sub(pattern, '', content, flags=re.DOTALL)

        pattern = r'### 💼 _\*\*\[AI Job Opportunities\]\*\*_.*?----------'
        content = re.sub(pattern, '', content, flags=re.DOTALL)        

        # Remove some empty substrings
        content = content.replace("----------", "") 
        content = content.replace("**QUICK HITS**", "")
        content = content.replace("\r\n\r\n", "\n")
        content = content.replace("\n\n", "\n")

        return content
    
    # TL;DR
    def tldr(self, content):

        # Isolate only the part that is relevant
        content = content.split("BIG TECH & STARTUPS")[-1].split("Love TLDR?")[0]


        # Remove leading and trailing whitespace characters
        text = content.strip()

        # Remove empty lines while keeping paragraph separation
        paragraphs = text.split('\r\n')
        cleaned_paragraphs = []

        for paragraph in paragraphs:
            # Remove newline characters within paragraphs
            cleaned_paragraph = ' '.join(paragraph.split())
            cleaned_paragraphs.append(cleaned_paragraph)

        cleaned_paragraphs = [paragraph.strip() if len(paragraph) != 0 else "\n"  for paragraph in cleaned_paragraphs]
        # Join the cleaned paragraphs with double newlines to keep separation
        content = ''.join(cleaned_paragraphs)

        # Remove the parentheses with the reading time
        content = re.sub(r'\(\d+\s?MINUTE\s?READ\)', '', content)

        # Remove the links numbers
        content = re.sub(r'\[\d+\]', '', content)

        return content

    # The Average Joe
    def average_joe(self, content):

        content = content.split("EXTRA")[0].strip()
        content = content.split("Good morning.")[-1].strip()

        # Remove the links
        pattern = r'\[http.*?\]'
        content = re.sub(pattern, '', content)

        # Remove the stock symbols
        pattern = r'\(\s?\$.*?\)'
        content = re.sub(pattern, '', content)

        # Remove empty lines while keeping paragraph separation
        paragraphs = content.split('\r\n')
        cleaned_paragraphs = []

        for paragraph in paragraphs:
            # Remove newline characters within paragraphs
            cleaned_paragraph = ' '.join(paragraph.split())
            cleaned_paragraphs.append(cleaned_paragraph)

        cleaned_paragraphs = [paragraph.strip() if len(paragraph) != 0 else "\n\n"  for paragraph in cleaned_paragraphs]
        # Join the cleaned paragraphs with double newlines to keep separation
        content = ''.join(cleaned_paragraphs)

        # Remove the Partnership
        pattern = r'PARTNERED WITH.*?LARGECAP RECAP'
        content = re.sub(pattern, '', content, flags=re.DOTALL)

        pattern = r"JOE'S MARKET PULSE.*?Markets & Economy"
        content = re.sub(pattern, '', content, flags=re.DOTALL)

        pattern = r"PARTNERED WITH.*?CHART"
        content = re.sub(pattern, '', content, flags=re.DOTALL)

        pattern = r"PARTNERED.*?SUNDAY"
        content = re.sub(pattern, '', content, flags=re.DOTALL)

        # Some other clean up
        content = content.replace("[ Read ]", "")
        content = content.replace(" OF THE DAY DIGIT OF THE DAY", "")
        content = re.sub(r'\n\s*?\n\s*?\n\s*?\n\s*?', '\n\n', content)
        content = content.replace("*Thanks to our sponsors for keeping the newsletter free.", "")

        return content.strip()

    # The Neuron
    def neuron(self, content):

        content = content.split("Welcome, humans. ")[-1].strip()
        content = content.split("# A Cat's Commentary.")[0].strip()

        # Remove the links
        pattern = r'\(http.*?\)'
        content = re.sub(pattern, '', content)
        pattern = r'\(s:.*?\)'
        content = re.sub(pattern, '', content)
        # pattern = r'(//.*?)'
        # content = re.sub(pattern, '', content)
        pattern = r'\(www.*?/\)'
        content = re.sub(pattern, '', content)
        # pattern = r'(.*?/)'
        # content = re.sub(pattern, '', content)

        # Remove the images
        pattern = r'View image:.*?Caption:.*?\n'
        content = re.sub(pattern, '', content, flags=re.DOTALL)

        # Remove the partnerships
        pattern = r'###### \*\*FROM OUR PARTNERS\*\*.*#.*#'
        content = re.sub(pattern, '#', content, flags=re.DOTALL)

        # Remove Treats to try
        pattern = r'# Treats To Try\..*# Around the Horn'
        content = re.sub(pattern, '# Around the Horn', content, flags=re.DOTALL)

        # Remove the daily special, as it is always based on images
        if '# Monday' in content:
            content = content.split("# Monday")[0].strip()
        elif '# Tuesday' in content:
            content = content.split("# Tuesday")[0].strip()
        elif '# Wednesday' in content:
            content = content.split("# Wednesday")[0].strip()
        elif '# Thursday' in content:
            content = content.split("# Thursday")[0].strip()
        elif '# Friday' in content:
            content = content.split("# Friday")[0].strip()

        # Remove empty lines while keeping paragraph separation
        paragraphs = content.split('\r\n')
        cleaned_paragraphs = []

        for paragraph in paragraphs:
            # Remove newline characters within paragraphs
            cleaned_paragraph = ' '.join(paragraph.split())
            cleaned_paragraphs.append(cleaned_paragraph)

        cleaned_paragraphs = [paragraph.strip() if len(paragraph) > 2 else "\n"  for paragraph in cleaned_paragraphs]
        # Join the cleaned paragraphs with double newlines to keep separation
        content = ''.join(cleaned_paragraphs)

        return content.strip()
    
    # Analitica
    def analitica(self, content):

        content = content.split("Buona lettura!")[-1].strip()
        content = content.split("Uno sguardo ai mercati")[0].strip()

        # Remove the links
        pattern = r'http.*?[\s\n]'
        content = re.sub(pattern, '', content)

        # Remove non interesting sections
        pattern = r'Video YouTube.*?Notizie'
        content = re.sub(pattern, '', content, flags=re.DOTALL)

        pattern = r'In collaborazione con.*?News'
        content = re.sub(pattern, 'News', content, flags=re.DOTALL)

        pattern = r'La trimestrale.*?Extra'
        content = re.sub(pattern, 'Extra', content, flags=re.DOTALL)

        # Remove empty lines while keeping paragraph separation
        paragraphs = content.split('\r\n')
        cleaned_paragraphs = []

        for paragraph in paragraphs:
            # Remove newline characters within paragraphs
            cleaned_paragraph = ' '.join(paragraph.split())
            cleaned_paragraphs.append(cleaned_paragraph)

        cleaned_paragraphs = [paragraph.strip() if len(paragraph) > 2 else "\n"  for paragraph in cleaned_paragraphs]
        # Join the cleaned paragraphs with double newlines to keep separation
        content = ''.join(cleaned_paragraphs)

        return content.strip()

    # Datapizza
    def datapizza(self, content):

        # content = content.split("Buona lettura!")[-1].strip()
        content = content.split("Datapizza Selection")[0].strip()

        content = content.replace("Image\r", "").strip()

        # Remove the links
        pattern = r'\( http.*?\)'
        content = re.sub(pattern, '', content)

        # Remove emojis
        emoji_pattern = re.compile("["
            u"\U0001F600-\U0001F64F"  # emoticons
            u"\U0001F300-\U0001F5FF"  # symbols & pictographs
            u"\U0001F680-\U0001F6FF"  # transport & map symbols
            u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
            u"\U00002702-\U000027B0"  # dingbats
            u"\U000024C2-\U0001F251"  # misc symbols
            u"\U0000FE0F"  # variation selector
            u"\U0000231A-\U0000231B"  # watch symbols
            u"\U000023E9-\U000023EC"  # play/pause symbols
            u"\U000023F0-\U000023F3"  # clock symbols
            u"\U000023F8-\U000023FA"  # media symbols
            u"\U00002300-\U000023FF"  # technical symbols
            u"\U00002600-\U000027BF"  # misc symbols and arrows
            u"\U00002934-\U00002935"  # arrow symbols
            u"\U00002B05-\U00002B07"  # arrow symbols
            u"\U00002B1B-\U00002B1C"  # square symbols
            u"\U00002B50-\U00002B55"  # star symbols
            "]+", flags=re.UNICODE)
        
        # Remove emojis
        content = emoji_pattern.sub('', content)

        # Remove Signature
        pattern = r"---------------------------.*?By.*?alt=''''"
        content = re.sub(pattern, '', content, flags=re.DOTALL)

        # pattern = r'In collaborazione con.*?News'
        # content = re.sub(pattern, 'News', content, flags=re.DOTALL)

        # pattern = r'La trimestrale.*?Extra'
        # content = re.sub(pattern, 'Extra', content, flags=re.DOTALL)

        # Remove empty lines while keeping paragraph separation
        paragraphs = content.split('\r\n')
        cleaned_paragraphs = []

        for paragraph in paragraphs:
            # Remove newline characters within paragraphs
            cleaned_paragraph = ' '.join(paragraph.split())
            cleaned_paragraphs.append(cleaned_paragraph)

        cleaned_paragraphs = [paragraph.strip() if len(paragraph) > 2 else "\n"  for paragraph in cleaned_paragraphs]
        # Join the cleaned paragraphs with double newlines to keep separation
        content = ''.join(cleaned_paragraphs)

        content = content.replace("alt=''''", "")

        content = '\n'.join(content.split('\n')[:-2])

        return content.strip()





