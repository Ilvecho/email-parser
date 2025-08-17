import os
import shutil
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv 
from utils import YahooEmailManager, TTS, ClaudeSonnetAPI                     # My utils


def create_signature(save_path):
    # Read newsletter links from file
    links_path = save_path / "read_online_urls.txt"
    newsletter_links = []
    if links_path.exists():
        with open(links_path, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f, 1):
                if "=" in line:
                    title, url = line.strip().split("=", 1)
                    newsletter_links.append(f'<li>[{idx}] <a href="{url.strip()}">{title.strip()}</a></li>')
    else:
        # fallback to static list if file not found
        newsletter_links = [
                "<li>[1] The Neuron</li>",
                "<li>[2] TL;DR</li>",
                "<li>[3] The Rundown AI</li>"
        ]

    signature = f"""
    <p><br />Until tomorrow,<br>
    Massimo</p>

    <strong>Credits</strong>
    <p>The above content is derived from the following Newsletters:</p>
    <ul>
        {''.join(newsletter_links)}
    </ul>
    """

    return signature

if __name__ == "__main__":

    # Saturday cleanup
    if datetime.now().weekday() == 6:  
        print("It's Saturday, time for a clean up!")

        # get the directory
        base_dir = Path(__file__).parent.parent

        # Identify email_content folders
        folders = [f for f in base_dir.iterdir() if f.is_dir() and f.name.startswith("email_content_")]
        
        # Nothing to clean up
        if len(folders) <= 1:
            exit(1)  

        # Sort by folder name 
        folders_sorted = sorted(folders, key=lambda x: x.name, reverse=True)
        # Keep the most recent, delete the rest
        for folder in folders_sorted[1:]:
            shutil.rmtree(folder)
            print(f"Removed old folder: {folder}")

        exit(1)

    # Sunday do nothing
    elif datetime.now().weekday() == 5: 
        print("It's Sunday, well deserved break!")
        exit(1)
    # If it's a weekday, execute the code
    else:
        print("It's a weekday, let's get to work!")
    
    load_dotenv()

    EMAIL = os.getenv("EMAIL")
    APP_PASSWORD = os.getenv("APP_PASSWORD")
    UNREAL_SPEECH_API = os.getenv("UNREAL_SPEECH_API")
    CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
    RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")

    today = datetime.now().strftime('%Y-%m-%d')  
    print(f"Today's date: {today}")
    save_path = Path(__file__).parent.parent / f"email_content_{str(today)}"
    manager = YahooEmailManager(EMAIL, APP_PASSWORD)
    
    if manager.connect():
        print("Connected to Yahoo email successfully!")
        save_path.mkdir(parents=True, exist_ok=True)
        manager.parse_emails(num_emails=10, save_path=save_path)
        manager.disconnect()
        print("Email content extraction completed!")

        # # Add the closing
        # target_path = save_path / "english.txt"
        # with open(target_path, 'a', encoding='utf-8') as f:
        #     f.write(f'\n\n\n*Thank you for listening, until next time!*')

    with open(save_path / "english.txt", 'r', encoding='utf-8') as f:
        content = f.read()

    # If the content is too short, we exit
    if len(content.strip()) < 200:
        print(f"Content is too short: {len(content.strip())}.")
        exit(1)

    # Else, elaborate the content and continue
    else:
        print(f"Content is of adequate length: {len(content.strip())}.")
        content = f"<input_text>{content}</input_text>"

    # Call Claude API
    claude_api = ClaudeSonnetAPI(CLAUDE_API_KEY)
    result = claude_api.process_content(content)

    with open(save_path / "llm_output.txt", 'w', encoding='utf-8') as f:
        f.write(result)

    print("Claude API call successful.")

    with open(save_path / "llm_output.txt", 'r', encoding='utf-8') as f:
        content = f.read()

    # Add signature and credits
    signature = create_signature(save_path)
    content += signature

    success = manager.send_yahoo_email(recipient=RECIPIENT_EMAIL, subject="Daily AI News", html_body=content)

    if success:
        print("Email sent successfully.")
    else:
        print("Failed to send email.")
        # text_to_speech = TTS(UNREAL_SPEECH_API, save_path)
        # text_to_speech.transform_content(content)
