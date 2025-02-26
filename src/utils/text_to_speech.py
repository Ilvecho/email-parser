import requests
import time

class TTS():

    def __init__(self, api_key, save_path):
        self.url = "https://api.v8.unrealspeech.com/synthesisTasks"
        self.api_key = api_key
        self.save_path = save_path

    def transform_content(self, content):
        
        ############################
        ##### Post the request #####
        ############################
        payload = {
            "Text": content.strip(), 
            "VoiceId": "Sierra",
            "Bitrate": "192k",
            "Pitch": 1.00,
            "Speed": 0.3,
            "AudioFormat": "mp3",
            "OutputFormat": "uri",
            "sync": False
            }
        
        headers = {
        'Authorization': f'Bearer {self.api_key}'
        }

        # Note the .json() at the end to parse the response as a dictionary
        response = requests.request("POST", self.url, headers=headers, json=payload).json()

        task_id = response["SynthesisTask"]["TaskId"]
        output_url = response["SynthesisTask"]["OutputUri"]

        ############################
        ###### Get the status ######
        ############################

        print(task_id)
        print(output_url)

        task_status = "inProgress"
        cont = 0
        time.sleep(20)
        while task_status == "inProgress":
            time.sleep(5)
            cont += 1
            url = f"https://api.v8.unrealspeech.com/synthesisTasks/{task_id}"

            headers = {
                'Authorization': f'Bearer {self.api_key}'
            }

            response = requests.get(url, headers=headers).json()
            task_status = response["SynthesisTask"]["TaskStatus"]

            print(task_status)

            if task_status == 'completed' or cont == 40:
                break

        ############################
        ###### Get the audio #######
        ############################

        if task_status == 'completed':
            # temp_url = "https://unreal-expire-in-90-days.s3-us-west-2.amazonaws.com/e33780f8-062b-4646-9893-090229133f70-0.mp3"
            audio_response = requests.get(output_url)

            # Save the audio file locally
            with open(self.save_path / 'output.wav', 'wb') as audio_file:
                audio_file.write(audio_response.content)  
        else:
            print('Task not completed - file not saved!')   