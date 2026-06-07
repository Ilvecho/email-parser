# CLAUDE.md — email-parser project context

## What this project does

Automated daily newsletter pipeline:
1. Fetch AI/tech newsletter emails via Yahoo IMAP
2. Parse and clean each newsletter (static regex, per-sender rules)
3. Concatenate cleaned content into `english.txt`
4. Call Claude Sonnet API to summarize into HTML
5. Send the HTML email via Yahoo SMTP

Runs daily on PythonAnywhere (scheduled task). Newsletters: The Neuron, TL;DR (main + AI edition), The Rundown AI.

---

## File structure

```
email-parser/
  src/
    main.py                        # Entry point / pipeline orchestrator
    utils/
      __init__.py                  # Exports: YahooEmailManager, TTS, ClaudeSonnetAPI
      email_extractor.py           # IMAP connect, fetch, route to ParseEmails
      parse_emails.py              # Per-newsletter static parsing (ParseEmails class)
      claude_sonnet_api.py         # Claude HTTP API wrapper + SYSTEM_PROMPT
      text_to_speech.py            # TTS via Unreal Speech (not actively used)
  email_content_YYYY-MM-DD/        # Output folder per run date
    english.txt                    # Concatenated cleaned newsletter text (input to Claude)
    llm_output.txt                 # Raw Claude HTML output
    body_sent.html                 # Final HTML sent (llm_output + signature + font fixes)
    read_online_urls.txt           # "NewsletterName=URL" per newsletter (for signature credits)
  CLAUDE.md                        # This file
  README.md                        # Project overview
  .env                             # EMAIL, APP_PASSWORD, UNREAL_SPEECH_API, CLAUDE_API_KEY, RECIPIENT_EMAIL
```

---

## main.py pipeline flow

```
connect IMAP -> parse_emails() -> disconnect
  -> [exit(1) debug stop]          # currently stops here; remove to continue
read english.txt
call ClaudeSonnetAPI.process_content(today, yesterday_summary, sources)
write llm_output.txt
apply font fixes + signature -> write body_sent.html
  -> [exit(1) debug stop]          # currently stops before send; remove to continue
send_yahoo_email()
```

**Debug exits**: `main.py` currently has two `exit(1)` stops. Line ~122 stops after email fetch (so you can inspect `english.txt`). Line ~189 stops before sending. These are intentional — remove them when ready for production.

Weekend handling block is commented out (lines 45-73).

---

## english.txt format

Each newsletter section is delimited by:
```
#+#

Newsletter Name

...content...
```

Claude's system prompt knows this format — `#+#` signals a new newsletter source.

---

## read_online_urls.txt format

```
The Neuron=https://...
TL;DR=https://...
The Rundown AI=https://...
```

Used in two places:
1. `main.py` builds the `sources` block for Claude (numbered `[1]`, `[2]`, `[3]`)
2. `create_signature()` builds the credits list at the bottom of the email

The `[N]` citation numbers in Claude's output refer to these newsletter-level credits, NOT article-level links.

---

## ParseEmails — per-newsletter parsing

**File**: `src/utils/parse_emails.py`

### Key design decisions

- Pure static regex — no BeautifulSoup, no HTML parsing of the email body
- `\r\n` normalization happens immediately after MIME decode (critical — without this, string checks like `"Links:\n------"` fail against CRLF emails)
- Inline article URLs are injected into `english.txt` so Claude can embed them as `<a>` tags
- `[N]` brackets in TLDR refer to the email's own `Links:` section (article URLs), not the newsletter-level credits

### Sender routing

| From address | Method | Newsletter name |
|---|---|---|
| `news@daily.therundown.ai` or `therundownai@mail.beehiiv.com` | `rundown_ai()` | The Rundown AI |
| `dan@tldrnewsletter.com` | `tldr()` | TL;DR / TLDR AI |
| `theneuron@newsletter.theneurondaily.com` | `neuron()` | The Neuron |

### TLDR link injection (tldr method)

TLDR emails contain a `Links:\n------\n[N] url` section at the bottom. The process:
1. Parse into `link_map = {N: url}` before any content processing
2. Normalize CRLF to LF first (otherwise `"Links:\n------"` check fails)
3. Match `CAPS TITLE [N]` lines in content, replace with `[CAPS TITLE](url)`
4. Remove remaining standalone `[N]` references
5. Reformat `[CAPS TITLE](url)Body text` → `Body text [Read more](url)` — this format gives Claude a natural inline link to embed

Key regex detail: use `[ \t]` (not `\s`) in the title character class to prevent matching across line boundaries.

TLDR tracking URLs (`links.tldrnewsletter.com/xxx`) are kept as-is.

### The Neuron FROM OUR PARTNERS removal

Pattern handles two cases:
- Case A: `**FROM OUR PARTNERS**` followed by `# Ad Heading` then ad body then `# Next Section`
- Case B: `**FROM OUR PARTNERS**` followed by ad body (no heading) then `# Next Section`

Regex: `r'\*\*FROM OUR PARTNERS\s*\*\*[^\n]*(?:\n+#[^\n]*)?\n.*?(?=\n#|\Z)'`

The `\s*` before `\*\*` handles trailing spaces in `**FROM OUR PARTNERS **`.

### The Rundown AI

No inline article links available (plain text has no article URLs). Sections removed: `TOGETHER WITH`, `PRESENTED BY`, `AI TRAINING`, `Trending AI Tools`. Content trimmed between `**Good morning, AI enthusiasts.**` and `**COMMUNITY**`.

---

## Claude API

**File**: `src/utils/claude_sonnet_api.py`

- Model: `claude-sonnet-4-20250514`
- Direct HTTP via `requests` (not Anthropic SDK)
- Max tokens: 4096

### System prompt key instructions

- Output: valid HTML for email (no surrounding `<html>/<body>` tags needed)
- Structure: Major News (`<h3>` stories + `<p>`), Other News (`<h2>` + `<ul><li>`), Prompt Tip of the Day (`<h2>`)
- Citations: `[N]` at end of each item, matching newsletter source
- Inline links: render `[text](url)` as `<a href="url">text</a>` within sentences
- TLDR links: articles end with `[Read more](url)` — embed URL as hyperlink on a relevant word/phrase; do NOT use "Read more" as anchor text; do NOT place as trailing element
- Duplicate detection: compare against `<yesterday>` block, skip already-covered stories
- Reading time: max 8 minutes
- Always include "AI Skill of the Day" from The Neuron as "Prompt Tip of the Day"

---

## Output post-processing (main.py)

After Claude returns HTML:
1. Append signature with newsletter credits
2. Replace `<h3>`, `<h2>`, `<p>`, `<ul>` tags to inject inline `font-family: Arial` styles
3. Write `body_sent.html`

---

## Known limitations (accepted)

- The Rundown AI has no article-level URLs in plain text (would need HTML parsing)
- Some TLDR articles have no `[N]` reference → no link possible
- TLDR AI edition sometimes has a blank line between title and body → `[Read more](url)` ends up on its own line, but the URL is still present for Claude
- TTS (Unreal Speech) is integrated but not actively used in the pipeline
