from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import assemblyai as aai
import threading
import asyncio
import numpy as np  # For audio processing
from constant import assemblyai_api_key

app = Flask(__name__)
socketio = SocketIO(app)

aai.settings.api_key = assemblyai_api_key
transcriber = None  
session_id = None  
transcriber_lock = threading.Lock()  

prompt = """Your task is to analyze the transcription with the following details:
1. Highlight key categories such as Names, Organizations, Questions, Important Keywords, and Numerical Values.
2. Add timestamps for each segment of the transcript.
"""

def on_open(session_opened: aai.RealtimeSessionOpened):
    global session_id
    session_id = session_opened.session_id
    print("Session ID:", session_id)

def on_data(transcript: aai.RealtimeTranscript):
    if not transcript.text:
        return

    if isinstance(transcript, aai.RealtimePartialTranscript):
        # Emit the partial transcript for real-time display
        socketio.emit('partial_transcript', {'text': transcript.text})

        # Calculate noise level ( implementation)
        noise_level = calculate_noise_level()
        socketio.emit('noise_level', {'level': noise_level})

    elif isinstance(transcript, aai.RealtimeFinalTranscript):
        # Emit final transcript
        socketio.emit('formatted_transcript', {'text': transcript.text})
        asyncio.run(analyze_transcript(transcript.text))

async def analyze_transcript(transcript):
    result = aai.Lemur().task(
        prompt, 
        input_text=transcript,
        final_model=aai.LemurModel.claude3_5_sonnet
    )
    print("Formatted Transcript Sent:", result.response)
    socketio.emit('formatted_transcript', {'text': result.response})

def calculate_noise_level():
    """
    A dummy function to simulate noise level calculation.
    Replace this with actual processing of the audio stream if required.
    """
    # Simulate noise level between 30 (low) and 90 (high)
    import random
    return random.randint(30, 90)

def on_error(error: aai.RealtimeError):
    print("An error occurred:", error)

def on_close():
    global session_id
    session_id = None
    print("Closing Session")

def transcribe_real_time():
    global transcriber  
    transcriber = aai.RealtimeTranscriber(
        sample_rate=16_000,
        on_data=on_data,
        on_error=on_error,
        on_open=on_open,
        on_close=on_close
    )

    transcriber.connect()

    # Stream audio using AssemblyAI's MicrophoneStream
    microphone_stream = aai.extras.MicrophoneStream(sample_rate=16_000)
    transcriber.stream(microphone_stream)

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('toggle_transcription')
def handle_toggle_transcription():
    global transcriber, session_id  
    with transcriber_lock:
        if session_id:
            if transcriber:
                print("Closing transcriber session")
                transcriber.close()
                transcriber = None
                session_id = None  
        else:
            print("Starting transcriber session")
            threading.Thread(target=transcribe_real_time).start()
@socketio.on('analyze_transcript')
def handle_analyze_transcript(data):
    transcript_text = data.get('text', '')
    if transcript_text:
        result = asyncio.run(analyze_transcript(transcript_text))
        socketio.emit('analysis_result', {'text': result.response})
    else:
        socketio.emit('analysis_result', {'text': "No transcript available for analysis."})



if __name__ == '__main__':
    socketio.run(app, debug=True)
