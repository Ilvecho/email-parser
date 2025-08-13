import os
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv 
from utils import YahooEmailManager, TTS, ClaudeSonnetAPI                     # My utils


if __name__ == "__main__":

    load_dotenv()

    EMAIL = os.getenv("EMAIL")
    APP_PASSWORD = os.getenv("APP_PASSWORD")
    UNREAL_SPEECH_API = os.getenv("UNREAL_SPEECH_API")
    CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")

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

    content = f"<input_text>{content}</input_text>"

    print(len(content.strip()))

    # Call Claude API
    claude_api = ClaudeSonnetAPI(CLAUDE_API_KEY)
    result = claude_api.process_content(content)

    with open(save_path / "llm_output.txt", 'w', encoding='utf-8') as f:
        f.write(result)

    with open(save_path / "llm_output.txt", 'r', encoding='utf-8') as f:
        content = f.read()

    # Add signature and credits
    signature = """
    <p><br />Until tomorrow,<br>
    Massimo</p>

    <strong>Credits</strong>
    <p>The above content in derived from the following Newsletters:</p>
    <ul>
        <li>The Neuron</li>
        <li>TL;DR</li>
        <li>The Rundown AI</li>
    </ul>
    """

    content += signature

    success = manager.send_yahoo_email(recipient="massimo.terzi@swift.com", subject="Daily AI News", html_body=content)

    if not success:
        print("Failed to send email.")
        # text_to_speech = TTS(UNREAL_SPEECH_API, save_path)
        # text_to_speech.transform_content(content)

