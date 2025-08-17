import re

class ParseEmails:

    def __init__(self, save_dir):
        self.save_dir = save_dir

    def parse_email_body(self, message, from_address):
        html_text = ""

        # The emails are made of multiple parts, one of which is TXT and it's the one we are interested in
        for part in message.walk():

            # Get the content from the plain text version
            content_type = part.get_content_type()

            try:
                # Use the plain text version of the email
                if content_type == "text/plain":
                    # Get text
                    charset = part.get_content_charset() or "utf-8" # Get the correct encoding                    
                    content = part.get_payload(decode=True).decode(charset, errors="replace")

                elif content_type == "text/html":
                    charset = part.get_content_charset() or "utf-8"
                    html_text += part.get_payload(decode=True).decode(charset, errors="replace")


            except Exception as e:
                print(f"Error processing part {content_type}: {str(e)}")
                continue
        
        # Use a switch to invoke the different parsers for each email 
        if from_address == "news@daily.therundown.ai" or from_address == "therundownai@mail.beehiiv.com":
            ok = self.rundown_ai(content)

            # Find and save the Read Online link
            match = re.search(r'<a[^>]+href="([^"]+)"[^>]*>\s*(?:<span[^>]*>)?Read Online(?:</span>)?\s*</a>', html_text, re.IGNORECASE)
            if match:
                # Save TXT summary
                target_path = self.save_dir / "read_online_urls.txt"
                with open(target_path, 'a', encoding='utf-8') as f:
                    f.write(f"The Rundown AI={match.group(1).strip()}\n")

                print("The Rundown AI link has been saved.")

            else:
                print("The Rundown AI link not found.")

        elif from_address == "dan@tldrnewsletter.com":
            ok = self.tldr(content)

            # Find and save the View Online link
            match = re.search(r'<a[^>]+href="([^"]+)"[^>]*>\s*(?:<span[^>]*>)?View Online(?:</span>)?\s*</a>', html_text, re.IGNORECASE)
            if match:
                # Save TXT summary
                target_path = self.save_dir / "read_online_urls.txt"
                with open(target_path, 'a', encoding='utf-8') as f:
                    f.write(f"TL;DR={match.group(1).strip()}\n")

                print("TL;DR link has been saved.")

            else:
                print("TL;DR link not found.")

        elif from_address == "joe@readthejoe.com":
            ok = self.average_joe(content)

        elif from_address == "theneuron@newsletter.theneurondaily.com":
            ok = self.neuron(content)

            # Find and save the Read Online link
            match = re.search(r'<a[^>]+href="([^"]+)"[^>]*>\s*(?:<span[^>]*>)?Read Online(?:</span>)?\s*</a>', html_text, re.IGNORECASE)
            if match:
                # Save TXT summary
                target_path = self.save_dir / "read_online_urls.txt"
                with open(target_path, 'a', encoding='utf-8') as f:
                    f.write(f"The Neuron={match.group(1).strip()}\n")

                print("The Neuron link has been saved.")

            else:
                print("The Neuron link not found.")

        elif from_address == "news@myanalitica.it":
            ok = self.analitica(content)

        elif from_address == "community@datapizza.it":
            ok = self.datapizza(content)

        if not ok: 
            raise("Some errors during the parsing of the email")
    
    # Rundown AI
    def rundown_ai(self, content):

        # Isolate only the part that is relevant
        content = content.split("**Good morning, AI enthusiasts.** ")[-1].split("**COMMUNITY**")[0]

        # Remove the links
        pattern = r'\(http.*?\)'
        content = re.sub(pattern, '', content)

        # Remove the intro
        pattern = r'———————————————————————————.*?\*\*LATEST DEVELOPMENTS\*\*'
        content = re.sub(pattern, '', content, flags=re.DOTALL)

        # Remove images
        pattern = r'\n#### .*?\*\*The Rundown:'
        content = re.sub(pattern, '\n \n', content, flags=re.DOTALL)

        # Remove details
        # pattern = r'\*\*The details.*?Why'
        # content = re.sub(pattern, 'Why', content, flags=re.DOTALL)

        # Remove emojis
        emoji_pattern = re.compile("["
            u"\U0001F600-\U0001F64F"  # emoticons
            u"\U0001F300-\U0001F5FF"  # symbols & pictographs
            u"\U0001F680-\U0001F6FF"  # transport & map symbols
            u"\U0001F700-\U0001F77F"  # alchemical symbols
            u"\U0001F780-\U0001F7FF"  # Geometric Shapes
            u"\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
            u"\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
            u"\U0001FA00-\U0001FA6F"  # Chess Symbols
            u"\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
            u"\U0001F004-\U0001F0CF"  # Additional emoticons
            u"\U0001F170-\U0001F251"  # Enclosed characters
            u"\U00002702-\U000027B0"  # Dingbats
            u"\U000024C2-\U0001F251"  # Enclosed characters
            u"\U0001F300-\U0001F5FF"  # Misc Symbols & Pictographs
            u"\U0001F900-\U0001F9FF"  # Supplemental Symbols & Pictographs
            u"\U0001FA00-\U0001FA6F"  # Chess Symbols
            u"\U0001FA70-\U0001FAFF"  # Symbols & Pictographs Extended-A
            u"\U00002600-\U000026FF"  # Miscellaneous Symbols
            u"\U00002700-\U000027BF"  # Dingbats
            u"\U0000FE0F"             # Variation Selector
            u"\U0001F1E0-\U0001F1FF"  # Flags (iOS)
            "]+", flags=re.UNICODE)
            
        # Remove emojis
        content = emoji_pattern.sub('', content)

        # Remove the sponsored parts
        pattern = r'###### TOGETHER WITH.*?----------'
        content = re.sub(pattern, '', content, flags=re.DOTALL)

        pattern = r'###### AI TRAINING.*?----------'
        content = re.sub(pattern, '', content, flags=re.DOTALL)

        pattern = r'###### PRESENTED BY.*?----------'
        content = re.sub(pattern, '', content, flags=re.DOTALL)

        # Remove Trending tools & Jobs
        pattern = r'###\s+_\*\*\[Trending AI Tools\]\*\*_.*?----------'
        content = re.sub(pattern, '', content, flags=re.DOTALL)

        pattern = r'###\s+_\*\*\[AI Job Opportunities\]\*\*_.*?----------'
        content = re.sub(pattern, '', content, flags=re.DOTALL)        

        # Format the titles
        pattern = r'#+'
        content = re.sub(pattern, '#', content, flags=re.DOTALL)    

        # Remove some empty substrings
        content = content.replace("----------", "") 
        content = content.replace("**QUICK HITS**", "")
        content = content.replace("\r\n\r\n", "\n")
        content = re.sub(r'\n\s*[\n\s*]+', '\n\n', content)
        content = content.replace("[", "")
        content = content.replace("]", "")
        content = content.replace("_", "")
        content = content.replace("**", "")

        # Improve readability of last part
        first_part, second_part = content.split("#  Everything else in AI today")

        improved_second_part = []
        for line in second_part.split('\n'):
            if not line.strip():
                continue
            else:
                improved_second_part.append('- ' + line)

        second_part = '\n'.join(improved_second_part)
        content = '\n\n'.join([first_part,"#  Everything else in AI today",  second_part])

        # Save TXT summary
        target_path = self.save_dir / "english.txt"
        with open(target_path, 'a', encoding='utf-8') as f:
            f.write(f'\n\n\n#+#\n\nThe Rundown AI\n\n{content.strip()}')

        return True
    
    # TL;DR
    def tldr(self, content):

        # Isolate only the part that is relevant
        content = content.split("BIG TECH & STARTUPS")[-1].split("Love TLDR?")[0]

        # Join split all-caps lines
        content = re.sub(r'([A-Z0-9][A-Z0-9\s,\'&-]+)\n+?([A-Z0-9][A-Z0-9\s,\'&-]+)', r'\1 \2', content)

        # Remove emojis
        emoji_pattern = re.compile("["
            u"\U0001F600-\U0001F64F"  # emoticons
            u"\U0001F300-\U0001F5FF"  # symbols & pictographs
            u"\U0001F680-\U0001F6FF"  # transport & map symbols
            u"\U0001F700-\U0001F77F"  # alchemical symbols
            u"\U0001F780-\U0001F7FF"  # Geometric Shapes
            u"\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
            u"\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
            u"\U0001FA00-\U0001FA6F"  # Chess Symbols
            u"\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
            u"\U0001F004-\U0001F0CF"  # Additional emoticons
            u"\U0001F170-\U0001F251"  # Enclosed characters
            u"\U00002702-\U000027B0"  # Dingbats
            u"\U000024C2-\U0001F251"  # Enclosed characters
            u"\U0001F300-\U0001F5FF"  # Misc Symbols & Pictographs
            u"\U0001F900-\U0001F9FF"  # Supplemental Symbols & Pictographs
            u"\U0001FA00-\U0001FA6F"  # Chess Symbols
            u"\U0001FA70-\U0001FAFF"  # Symbols & Pictographs Extended-A
            u"\U00002600-\U000026FF"  # Miscellaneous Symbols
            u"\U00002700-\U000027BF"  # Dingbats
            u"\U0000FE0F"             # Variation Selector
            u"\U0001F1E0-\U0001F1FF"  # Flags (iOS)
            "]+", flags=re.UNICODE)
        
        # Remove emojis
        content = emoji_pattern.sub('', content)

        # Remove the parentheses with the reading time
        content = re.sub(r'\(\d+\s*?MINUTE\s*?READ\)', '', content)

        # Remove the links numbers
        content = re.sub(r'\[\d+\]', '', content)

        # # Remove one space lines
        # content = re.sub(r'\n ', ' ', content)

        # Keep only the titles
        # Step 1: Split at the substring while preserving it in one part
        split_text = "SCIENCE & FUTURISTIC TECHNOLOGY"
        split_index = content.find(split_text)
        
        if split_index == -1:
            return False
                
        first_part = content[:split_index + len(split_text)]
        first_part = first_part.replace(split_text, "OTHER NEWS")
        second_part = content[split_index + len(split_text):]
        
        # Step 2: Process the second part line by line
        lines = second_part.strip().split('\n')
        
        # New filtering logic:
        # forbidden_substrings = ["(SPONSOR)", "(GITHUB REPO)", "(WEBSITE)", "PROGRAMMING, DESIGN & DATA SCIENCE", "MISCELLANEOUS", "QUICK LINKS", "HIRING"]
        forbidden_substrings = ["(SPONSOR)", "(GITHUB REPO)", "(WEBSITE)", "HIRING"]
        filtered_lines = []
        skip_mode = False

        for idx, line in enumerate(lines):
            stripped_line = line.strip()
            is_all_caps = stripped_line and stripped_line == stripped_line.upper()

            if skip_mode:
                if is_all_caps:
                    skip_mode = False
                    # Start a new block with this ALL CAPS line
                    filtered_lines.append('\n- ' + line + '\n' if len(filtered_lines) == 0 else '- ' + line + '\n')
                # Otherwise, keep skipping
                continue

            if is_all_caps and any(substring in line for substring in forbidden_substrings):
                skip_mode = True
                # Do not add this line, start skipping
                continue

            # Add line (ALL CAPS or not) if not skipping
            if is_all_caps:
                filtered_lines.append('\n- ' + line + '\n' if len(filtered_lines) == 0 else '- ' + line + '\n')
            else:
                filtered_lines.append(line + '\n')

        filtered_second_part = '\n'.join(filtered_lines)
        content = '\n'.join([first_part, filtered_second_part])

        content = content.replace("\n ", "\n")

        # Remove empty lines while keeping paragraph separation
        paragraphs = content.split('\n')
        cleaned_paragraphs = []

        for paragraph in paragraphs:
            # Remove newline characters within paragraphs
            cleaned_paragraph = ' '.join(paragraph.split())
            cleaned_paragraphs.append(cleaned_paragraph)

        cleaned_paragraphs = [paragraph.strip() if len(paragraph) != 0 else "\n"  for paragraph in cleaned_paragraphs]
        # Join the cleaned paragraphs with double newlines to keep separation
        content = '\n'.join(cleaned_paragraphs)

        # 1. Remove single newlines between words with lowercase letters
        content = re.sub(r'(?<=[a-z\.])\n(?=[A-Za-z])', ' ', content)

        # 2. Remove double newlines between all-caps words
        content = re.sub(r'(?<=[A-Z])[\n]+(?=[A-Z])', '\n', content)

        # Remove multiple newlines between bullet points in OTHER NEWS section
        content = re.sub(r'(-[^\n]+)\n\n+(?=-)', r'\1\n', content)

        # Final clean up
        content = re.sub(r'\n\n+', '\n\n', content)

        # Save TXT summary
        target_path = self.save_dir / "english.txt"
        with open(target_path, 'a', encoding='utf-8') as f:
            f.write(f"\n\n\n#+#\n\nToo Long; Don't Read\n\n{content.strip()}")

        return True

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
        content = re.sub(pattern, 'LARGECAP RECAP\n', content, flags=re.DOTALL)

        pattern = r"JOE'S MARKET PULSE.*?Markets & Economy"
        content = re.sub(pattern, 'Markets & Economy\n', content, flags=re.DOTALL)

        pattern = r"PARTNERED WITH.*?CHART"
        content = re.sub(pattern, 'CHART', content, flags=re.DOTALL)

        pattern = r"PARTNERED.*?SUNDAY"
        content = re.sub(pattern, '', content, flags=re.DOTALL)

        # Some other clean up
        content = content.replace("[ Read ]", "")
        content = content.replace(" OF THE DAY DIGIT OF THE DAY", "")
        content = re.sub(r'\n\s*?\n\s*?\n\s*?\n\s*?', '\n\n', content)
        content = content.replace("*Thanks to our sponsors for keeping the newsletter free.", "")

        ####################################
        ##### Remove undesired content #####
        ####################################

        # First part: keep introduction and the title of the long article
        first_part, second_part = content.split("LARGECAP RECAP\n")

        lines = first_part.split('\n')
        cont = 0
        lines_of_interest = []
        for line in lines: 

            if cont == 2:
                break
            if not line.strip():
                continue
            else: 
                lines_of_interest.append('- ' + line)
                cont += 1

        first_part = "\n\n".join(lines_of_interest)

        # Second part: there are two articles whose title starts with an emoji. Keep only the title
        second_part, third_part = second_part.split('Markets & Economy')

        lines = second_part.split("\n")
        
        emoji_pattern = re.compile("["
            u"\U0001F600-\U0001F64F"  # emoticons
            u"\U0001F300-\U0001F5FF"  # symbols & pictographs
            u"\U0001F680-\U0001F6FF"  # transport & map symbols
            u"\U0001F700-\U0001F77F"  # alchemical symbols
            u"\U0001F780-\U0001F7FF"  # Geometric Shapes
            u"\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
            u"\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
            u"\U0001FA00-\U0001FA6F"  # Chess Symbols
            u"\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
            u"\U0001F004-\U0001F0CF"  # Additional emoticons
            u"\U0001F170-\U0001F251"  # Enclosed characters
            u"\U00002702-\U000027B0"  # Dingbats
            u"\U000024C2-\U0001F251"  # Enclosed characters
            u"\U0001F300-\U0001F5FF"  # Misc Symbols & Pictographs
            u"\U0001F900-\U0001F9FF"  # Supplemental Symbols & Pictographs
            u"\U0001FA00-\U0001FA6F"  # Chess Symbols
            u"\U0001FA70-\U0001FAFF"  # Symbols & Pictographs Extended-A
            u"\U00002600-\U000026FF"  # Miscellaneous Symbols
            u"\U00002700-\U000027BF"  # Dingbats
            u"\U0000FE0F"             # Variation Selector
            u"\U0001F1E0-\U0001F1FF"  # Flags (iOS)
            "]+", flags=re.UNICODE)
        
        # Filter lines that start with an emoji
        emoji_lines = []
        for line in lines:
            # Skip empty lines
            if not line.strip():
                continue
                
            # Check if the line starts with an emoji
            if emoji_pattern.match(line.strip()):
                temp = emoji_pattern.sub('', line)
                emoji_lines.append("- " + temp.strip())
        
        # Join the filtered lines and return
        second_part = '\n\n'.join(emoji_lines)    

        content = '\n\n'.join([first_part, second_part, third_part])

        # Third part: Keep only the title, except when mentioning EU or Europe
        third_part, fourth_part = third_part.split("CHART")

        lines_of_interest = []
        for line in third_part.split("\n"):

            # Skip empty lines or unexpected ones
            if not line.strip() or ":" not in line:
                continue
            
            title, _ = line.split(':')

            if "EU" in title or "europe" in title.lower():
                lines_of_interest.append('- ' + line.strip())
            else: 
                lines_of_interest.append('- ' + title.strip())

        third_part = '\n\n'.join(lines_of_interest)

        # Fourth part: keep only the title
        fourth_part = '- ' + fourth_part.split('\n')[0].strip()

        content = '\n\n'.join([first_part, second_part, third_part, fourth_part])

        # Save TXT summary
        target_path = self.save_dir / "english.txt"
        with open(target_path, 'a', encoding='utf-8') as f:
            f.write(f'\n\n\n#+#\n\nThe Average Joe\n\n{content.strip()}')

        return True

    # The Neuron
    def neuron(self, content):

        # Remove the partnerships
        pattern = r'\*\*FROM OUR PARTNERS\*\*.*?# Prompt Tip of the Day'
        content = re.sub(pattern, '# Prompt Tip of the Day', content, flags=re.DOTALL)

        # Remove the partnerships
        pattern = r'\*\*FROM OUR PARTNERS\*\*.*?# Intelligent Insights'
        content = re.sub(pattern, '# Intelligent Insights', content, flags=re.DOTALL)

        content = content.split("Welcome, humans. ")[-1].strip()
        content = content.replace("’", "'")
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
        pattern = r'\*\*'
        content = re.sub(pattern, '', content)

        # Remove the images
        pattern = r'View image:.*?Caption:'
        content = re.sub(pattern, '', content, flags=re.DOTALL)

        # Remove the agenda
        pattern = r'Here’s what you need to know about AI today.*?#'
        content = re.sub(pattern, '\r\n   \r\n#', content, flags=re.DOTALL)

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
        elif '# Where do you #Neuron' in content:
            content = content.split("# Where do you #Neuron")[0].strip()

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

        content = content.replace("[", "")
        content = content.replace("]", "")
        content = content.replace("_", "")

        # Save TXT summary
        target_path = self.save_dir / "english.txt"
        with open(target_path, 'a', encoding='utf-8') as f:
            f.write(f'\n\n\n#+#\n\nThe Neuron\n\n{content.strip()}')

        return True
    
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

        # Save TXT summary
        target_path = self.save_dir / "italiano.txt"
        with open(target_path, 'a', encoding='utf-8') as f:
            f.write(f'\n\n\n#+#\n\nAnalitica\n\n{content.strip()}')

        return True

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
            u"\U0001F700-\U0001F77F"  # alchemical symbols
            u"\U0001F780-\U0001F7FF"  # Geometric Shapes
            u"\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
            u"\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
            u"\U0001FA00-\U0001FA6F"  # Chess Symbols
            u"\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
            u"\U0001F004-\U0001F0CF"  # Additional emoticons
            u"\U0001F170-\U0001F251"  # Enclosed characters
            u"\U00002702-\U000027B0"  # Dingbats
            u"\U000024C2-\U0001F251"  # Enclosed characters
            u"\U0001F300-\U0001F5FF"  # Misc Symbols & Pictographs
            u"\U0001F900-\U0001F9FF"  # Supplemental Symbols & Pictographs
            u"\U0001FA00-\U0001FA6F"  # Chess Symbols
            u"\U0001FA70-\U0001FAFF"  # Symbols & Pictographs Extended-A
            u"\U00002600-\U000026FF"  # Miscellaneous Symbols
            u"\U00002700-\U000027BF"  # Dingbats
            u"\U0000FE0F"             # Variation Selector
            u"\U0001F1E0-\U0001F1FF"  # Flags (iOS)
            "]+", flags=re.UNICODE)
        
        # Remove emojis
        content = emoji_pattern.sub('', content)

        # Remove Signature
        pattern = r"---------------------------.*?By.*?alt=''''"
        content = re.sub(pattern, '', content, flags=re.DOTALL)

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

        # Save TXT summary
        target_path = self.save_dir / "italiano.txt"
        with open(target_path, 'a', encoding='utf-8') as f:
            f.write(f'\n\n\n#+#\n\nDatapizza\n\n{content.strip()}')

        return True





