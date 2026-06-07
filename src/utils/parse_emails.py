import re

# URLs that are admin/image/referral links (not article content)
_EXCLUDE_URL_RE = re.compile(
    r'media\.beehiiv\.com|unsubscribe|refer\.tldr\.tech|hub\.sparklp\.co'
    r'|advertise\.|/manage\?|tldr\.tech/signup|tldr\.tech/ai\?|tldr\.tech/tech\?'
)

_EMOJI_RE = re.compile(
    "["
    "\U0001F600-\U0001F64F"
    "\U0001F300-\U0001F5FF"
    "\U0001F680-\U0001F6FF"
    "\U0001F700-\U0001F77F"
    "\U0001F780-\U0001F7FF"
    "\U0001F800-\U0001F8FF"
    "\U0001F900-\U0001F9FF"
    "\U0001FA00-\U0001FA6F"
    "\U0001FA70-\U0001FAFF"
    "\U0001F004-\U0001F0CF"
    "\U0001F170-\U0001F251"
    "\U00002702-\U000027B0"
    "\U000024C2-\U0001F251"
    "\U00002600-\U000026FF"
    "\U00002700-\U000027BF"
    "\U0000FE0F"
    "\U0001F1E0-\U0001F1FF"
    "]+",
    flags=re.UNICODE,
)


class ParseEmails:

    def __init__(self, save_dir):
        self.save_dir = save_dir

    def parse_email_body(self, message, from_address):
        html_text = ""
        content = ""

        for part in message.walk():
            content_type = part.get_content_type()
            try:
                if content_type == "text/plain":
                    charset = part.get_content_charset() or "utf-8"
                    content = part.get_payload(decode=True).decode(charset, errors="replace")
                    content = content.replace('\r\n', '\n').replace('\r', '\n')
                elif content_type == "text/html":
                    charset = part.get_content_charset() or "utf-8"
                    html_text += part.get_payload(decode=True).decode(charset, errors="replace")
            except Exception as e:
                print(f"Error processing part {content_type}: {str(e)}")
                continue

        ok = True
        read_online_name = None
        read_online_pattern = None

        if from_address in ("news@daily.therundown.ai", "therundownai@mail.beehiiv.com"):
            ok = self.rundown_ai(content)
            read_online_name = "The Rundown AI"
            read_online_pattern = r'<a[^>]+href="([^"]+)"[^>]*>\s*(?:<span[^>]*>)?Read Online(?:</span>)?\s*</a>'

        elif from_address == "dan@tldrnewsletter.com":
            ok = self.tldr(content)
            read_online_name = "TL;DR"
            read_online_pattern = r'<a[^>]+href="([^"]+)"[^>]*>\s*(?:<span[^>]*>)?View Online(?:</span>)?\s*</a>'

        elif from_address == "theneuron@newsletter.theneurondaily.com":
            ok = self.neuron(content)
            read_online_name = "The Neuron"
            read_online_pattern = r'<a[^>]+href="([^"]+)"[^>]*>\s*(?:<span[^>]*>)?Read Online(?:</span>)?\s*</a>'

        # Italian newsletters - out of scope
        # elif from_address == "news@myanalitica.it":
        #     ok = self.analitica(content)
        # elif from_address == "community@datapizza.it":
        #     ok = self.datapizza(content)

        else:
            print(f"Unknown sender: {from_address}, skipping.")
            return

        if read_online_name and html_text:
            match = re.search(read_online_pattern, html_text, re.IGNORECASE)
            if match:
                with open(self.save_dir / "read_online_urls.txt", 'a', encoding='utf-8') as f:
                    f.write(f"{read_online_name}={match.group(1).strip()}\n")
                print(f"{read_online_name} link saved.")
            else:
                print(f"{read_online_name} link not found.")

        if not ok:
            print(f"Warning: parsing issue for {from_address}")

    # ── The Rundown AI ────────────────────────────────────────────────────────

    def rundown_ai(self, content):
        # Keep content between intro and COMMUNITY section
        content = content.split("**Good morning, AI enthusiasts.**")[-1]
        content = content.split("**COMMUNITY**")[0]

        # Remove image/media lines
        content = re.sub(r'^View image:.*$', '', content, flags=re.MULTILINE)
        content = re.sub(r'^Follow image link:.*$', '', content, flags=re.MULTILINE)
        content = re.sub(r'^Caption:.*$', '', content, flags=re.MULTILINE)

        # Remove sponsor and tutorial sections (TOGETHER WITH, PRESENTED BY, AI TRAINING)
        for marker in ("TOGETHER WITH", "PRESENTED BY", "AI TRAINING"):
            content = re.sub(
                r'#{1,6}\s+' + marker + r'.*?(?=#{1,6}|\Z)',
                '', content, flags=re.DOTALL
            )

        # Remove Trending AI Tools section
        content = re.sub(r'###.*?Trending AI Tools.*?(?=###|\Z)', '', content, flags=re.DOTALL)

        # Remove CDN image URLs but keep article inline links [text](url)
        content = re.sub(r'\(https://media\.beehiiv\.com[^)]*\)', '', content)

        # Remove standalone URLs not part of [text](url) markdown
        content = re.sub(r'(?<!\])\(https?://[^)\s]+\)', '', content)

        # Remove the header line (Read Online / Sign Up / Advertise superscripts)
        content = re.sub(r'^\^?\*\*\[.*?\]\(.*?\)\*\*\^.*$', '', content, flags=re.MULTILINE)

        # Remove plain text ending notice
        content = re.sub(r'———.*$', '', content, flags=re.DOTALL)

        # Remove separator lines
        content = content.replace("----------", "")

        # Remove emojis
        content = _EMOJI_RE.sub('', content)

        # Flatten deep headings to max ##
        content = re.sub(r'#{3,}', '##', content)

        # Clean up whitespace
        content = re.sub(r'\n{3,}', '\n\n', content)
        content = content.strip()

        with open(self.save_dir / "english.txt", 'a', encoding='utf-8') as f:
            f.write(f'\n\n\n#+#\n\nThe Rundown AI\n\n{content}')

        return True

    # ── TL;DR ─────────────────────────────────────────────────────────────────

    def tldr(self, content):
        is_ai_edition = "HEADLINES & LAUNCHES" in content

        # Parse the Links section into {N: url} before any other processing
        link_map = {}
        if "Links:\n------" in content:
            links_raw = content.split("Links:\n------")[-1]
            for line in links_raw.split('\n'):
                m = re.match(r'\[(\d+)\]\s+(https?://\S+)', line.strip())
                if m:
                    n, url = int(m.group(1)), m.group(2)
                    if not _EXCLUDE_URL_RE.search(url):
                        link_map[n] = url

        # Isolate the relevant content block
        if is_ai_edition:
            content = content.split("HEADLINES & LAUNCHES")[-1]
        elif "BIG TECH & STARTUPS" in content:
            content = content.split("BIG TECH & STARTUPS")[-1]

        content = content.split("Love TLDR?")[0]

        # For the main (non-AI) edition, drop the PROGRAMMING section (mostly non-AI)
        if not is_ai_edition and "PROGRAMMING, DESIGN & DATA SCIENCE" in content:
            prog_idx = content.find("PROGRAMMING, DESIGN & DATA SCIENCE")
            misc_idx = content.find("MISCELLANEOUS", prog_idx)
            if misc_idx != -1:
                content = content[:prog_idx] + content[misc_idx:]
            else:
                content = content[:prog_idx]

        # Remove emojis
        content = _EMOJI_RE.sub('', content)

        # Join split ALL-CAPS lines caused by email word-wrap before further processing
        content = re.sub(
            r'([A-Z0-9][A-Z0-9\s,\'"&:()\-./"]+)\n([A-Z0-9])',
            r'\1 \2', content
        )

        # Remove (X MINUTE READ) markers from article titles
        content = re.sub(r'\s*\(\d+\s*MINUTE\s*READ\)\s*', ' ', content)

        # Filter out forbidden sections (sponsors, repos, quick links) before linkifying
        forbidden = {"(SPONSOR)", "(GITHUB REPO)", "(WEBSITE)", "HIRING", "QUICK LINKS"}
        lines = content.split('\n')
        filtered, skip = [], False
        for line in lines:
            stripped = line.strip()
            is_caps = stripped and stripped.upper() == stripped and len(stripped) > 3 and not stripped.startswith('[')
            if skip:
                if is_caps and not any(f in stripped for f in forbidden):
                    skip = False
                    filtered.append(line)
                continue
            if is_caps and any(f in stripped for f in forbidden):
                skip = True
                continue
            filtered.append(line)
        content = '\n'.join(filtered)

        # Convert article title [N] references to markdown hyperlinks
        def _make_link(m):
            title = m.group(1).strip()
            n = int(m.group(2))
            url = link_map.get(n)
            if url:
                return f'[{title}]({url})'
            return title

        # Article lines: optional leading spaces, CAPS title, [N]
        # [ \t] instead of \s in the character class prevents matching across line boundaries
        content = re.sub(
            r'^ *([A-Z][A-Z0-9 \t,\'"&:()\-./\u2014%\u2019"]+?)[ \t]*\[(\d+)\][ \t]*',
            _make_link,
            content,
            flags=re.MULTILINE
        )

        # Remove any remaining standalone [N] link references
        content = re.sub(r'\s*\[\d+\]\s*', ' ', content)

        # Reformat [CAPS TITLE](url)Body text → Body text [Read more](url)
        # so Claude receives the article URL as a trailing inline link it can embed naturally
        content = re.sub(
            r'\[([A-Z][A-Z0-9 \t,\'"&:()\-./\u2014%\u2019"]+)\]\(([^)]+)\)(.*?)(?=\n\n|\Z)',
            lambda m: m.group(3).strip() + ' [Read more](' + m.group(2) + ')',
            content,
            flags=re.DOTALL
        )

        # Clean up
        content = re.sub(r'\n{3,}', '\n\n', content)
        content = content.strip()

        label = "TLDR AI" if is_ai_edition else "Too Long; Don't Read"
        with open(self.save_dir / "english.txt", 'a', encoding='utf-8') as f:
            f.write(f'\n\n\n#+#\n\n{label}\n\n{content}')

        return True

    # ── The Neuron ────────────────────────────────────────────────────────────

    def neuron(self, content):
        # Strip the plain-text ending notice
        content = re.sub(r'———.*$', '', content, flags=re.DOTALL)

        # Cut off at low-value sections
        for cutoff in [
            "# A Cat's Commentary",
            "# Thursday Trivia", "# Monday Trivia", "# Tuesday Trivia",
            "# Wednesday Trivia", "# Friday Trivia",
        ]:
            if cutoff in content:
                content = content.split(cutoff)[0]

        # Remove image/media lines
        content = re.sub(r'^View image:.*$', '', content, flags=re.MULTILINE)
        content = re.sub(r'^Follow image link:.*$', '', content, flags=re.MULTILINE)
        content = re.sub(r'^Caption:.*$', '', content, flags=re.MULTILINE)

        # Remove FROM OUR PARTNERS blocks.
        # Pattern handles two formats:
        #   Case A: **FROM OUR PARTNERS** \n\n # Ad heading \n ad content \n\n # Next real section
        #   Case B: **FROM OUR PARTNERS** \n\n ad content (no # heading) \n\n # Next real section
        # The optional group (?:\n+#[^\n]*)? consumes the ad heading if present,
        # then .*? (lazy + DOTALL) eats the body up to the next \n# or end of string.
        content = re.sub(
            r'\*\*FROM OUR PARTNERS\s*\*\*[^\n]*(?:\n+#[^\n]*)?\n.*?(?=\n#|\Z)',
            '', content, flags=re.DOTALL
        )
        content = re.sub(
            r'THIS EPISODE WAS BROUGHT TO YOU BY.*?(?=^#|\Z)',
            '', content, flags=re.DOTALL | re.MULTILINE
        )

        # Remove Treats to Try section
        content = re.sub(
            r'^#+\s*(?:🍪\s*)?Treats to Try.*?(?=^#|\Z)',
            '', content, flags=re.DOTALL | re.MULTILINE
        )

        # Remove Podcast / In Case You Missed It sections
        content = re.sub(
            r'^#+\s*(?:🎙️\s*).*?(?=^#|\Z)',
            '', content, flags=re.DOTALL | re.MULTILINE
        )
        content = re.sub(
            r'^#+\s*\*\*NEW Podcast:.*?(?=^#|\Z)',
            '', content, flags=re.DOTALL | re.MULTILINE
        )
        content = re.sub(
            r'^#+ NEW Podcast:.*?(?=^#|\Z)',
            '', content, flags=re.DOTALL | re.MULTILINE
        )

        # Remove LIVE promo sections (inline within regular newsletters)
        content = re.sub(
            r'^#+\s*(?:🔴\s*).*?(?=^#|\Z)',
            '', content, flags=re.DOTALL | re.MULTILINE
        )

        # Remove CDN image URLs but keep article inline links [text](url)
        content = re.sub(r'\(https://media\.beehiiv\.com[^)]*\)', '', content)

        # Remove standalone URLs not part of [text](url) markdown
        content = re.sub(r'(?<!\])\(https?://[^)\s]+\)', '', content)

        # Get content after "Welcome, humans." greeting
        if "Welcome, humans." in content:
            content = content.split("Welcome, humans.")[-1]

        # Remove P.S / P.P.S lines
        content = re.sub(r'^\*\*P\.P?\.S.*$', '', content, flags=re.MULTILINE)

        # Clean up mixed bold/italic markers (_** and **_)
        content = re.sub(r'_\*\*', '**', content)
        content = re.sub(r'\*\*_', '**', content)

        # Clean up whitespace
        content = re.sub(r'\n{3,}', '\n\n', content)
        content = content.strip()

        with open(self.save_dir / "english.txt", 'a', encoding='utf-8') as f:
            f.write(f'\n\n\n#+#\n\nThe Neuron\n\n{content}')

        return True
