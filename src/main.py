import os
from datetime import datetime
from pathlib import Path
from utils import YahooEmailExtractor, TTS                     # My utils


if __name__ == "__main__":

    EMAIL = os.getenv("EMAIL")
    APP_PASSWORD = os.getenv("APP_PASSWORD")
    UNREAL_SPEECH_API = os.getenv("UNREAL_SPEECH_API")

    today = datetime.now().strftime('%Y-%m-%d')  
    save_path = Path(__file__).parent.parent / f"email_content_{str(today)}"
    
    extractor = YahooEmailExtractor(EMAIL, APP_PASSWORD)
    
    if extractor.connect():
        save_path.mkdir(parents=True, exist_ok=True)
        extractor.parse_emails(num_emails=10, save_path=save_path)
        extractor.disconnect()
        print("Email content extraction completed!")

        # Add the closing
        target_path = save_path / "english.txt"
        with open(target_path, 'a', encoding='utf-8') as f:
            f.write(f'\n\n\n*Thank you for listening, until next time!*')

    # Create the Audio file
    with open(save_path / "english.txt", 'r', encoding='utf-8') as f:
        content = f.read()

    print(len(content.strip()))
    
    # text_to_speech = TTS(UNREAL_SPEECH_API, save_path)
    # text_to_speech.transform_content(content)

