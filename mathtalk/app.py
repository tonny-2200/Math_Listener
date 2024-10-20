import os
import pandas as pd
import whisper
import re
#-----------------------------------------------------------------------------

from flask import Flask, render_template, redirect, url_for
import pyaudio
import wave
import threading
import time

app = Flask(__name__)

# Audio recording parameters
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024
RECORD_SECONDS = 5
OUTPUT_FILENAME = "C:\\Users\\tanma\\OneDrive\\Desktop\\mathtalk\\static\\UPLOAD_FOLDER\\temp_audio.wav"



df_c = pd.read_excel(r"C:\Users\tanma\Downloads\data (1).xlsx")

# Function to print n choose k
# for permutation
def print_n_choose_k(n, k):
    superscript_digits = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")
    subscript_digits = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")
    n_str = str(n).translate(superscript_digits)
    k_str = str(k).translate(subscript_digits)
    return f"{n_str}P{k_str}"

# Combinations
def print_combi(n, k):
    superscript_digits = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")
    subscript_digits = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")
    n_str = str(n).translate(superscript_digits)
    k_str = str(k).translate(subscript_digits)
    return f"{n_str}C{k_str}"

# Integration
def print_integral(n, k):
    superscript_digits = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")
    subscript_digits = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")
    n_str = str(n).translate(subscript_digits)
    k_str = str(k).translate(superscript_digits)
    return f"{n_str}{chr(0x222B)}{k_str}"

# Function to escape special characters
def escape_special_characters(text):
    escaped_text = re.escape(text)
    return escaped_text

def from_microphone():
    audio = pyaudio.PyAudio()
    
    # Start recording
    stream = audio.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, input=True,
                        frames_per_buffer=CHUNK)
    
    print("Recording started...")
    frames = []

    for _ in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)

    # Stop recording
    stream.stop_stream()
    stream.close()
    audio.terminate()

    # Save the recording
    with wave.open(OUTPUT_FILENAME, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(audio.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))

    print(f"Recording saved as {OUTPUT_FILENAME}")
    
    # Load Whisper model
    model = whisper.load_model("base")

    # Transcribe audio using Whisper
    result = model.transcribe(OUTPUT_FILENAME, language="en")
    
    text = result['text']

    print("Recognized Text:", text)
    # Return the processed equation
    return process_text_to_equation(text)

# Function to process the recognized text and convert it into a mathematical equation
def process_text_to_equation(text):
    text_lower = text.lower().split()  # Split the recognized text into words
    equation = ''
    skip_next_words = False

    i = 0
    while i < len(text_lower):
        word = text_lower[i]
        escaped_word = escape_special_characters(word)
        if df_c['Name'].str.contains(escaped_word, case=False).any():
            remaining_text = ' '.join(text_lower[i:])
            
            # Check if the remaining text matches any name in the DataFrame
            for j in range(len(remaining_text.split()), 0, -1):
                str_to_check = ' '.join(remaining_text.split()[:j])
                if str_to_check in df_c['Name'].str.lower().values:
                    if str_to_check == "to the power":
                        i += 3
                        if text_lower[i] == "2":
                            equation += chr(0x00B0 + int(text_lower[i]))
                        elif text_lower[i] == "3":
                            equation += chr(0x00B0 + int(text_lower[i]))
                        else:
                            equation += chr(0x2070 + int(text_lower[i]))
                        i += 1
                    elif str_to_check == "raised to":
                        i += 2
                        if text_lower[i] == "2":
                            equation += chr(0x00B0 + int(text_lower[i]))
                        elif text_lower[i] == "3":
                            equation += chr(0x00B0 + int(text_lower[i]))
                        else:
                            equation += chr(0x2070 + int(text_lower[i]))
                        i += 1
                    elif str_to_check == "square":
                        equation += chr(0x00B0 + int(2))
                        i += 1
                    elif str_to_check == "squared":
                        equation += chr(0x00B0 + int(2))
                        i += 1
                    elif str_to_check == "cube":
                        equation += chr(0x00B0 + int(3))
                        i += 1
                    elif str_to_check == "permutation":
                        var = print_n_choose_k(equation[-2], text_lower[i + 1])
                        equation = equation.replace(equation[-2], var, 1)
                        i += 2
                    elif str_to_check == "combination":
                        var = print_combi(equation[-2], text_lower[i + 1])
                        equation = equation.replace(equation[-2], var, 1)
                        i += 2
                    elif str_to_check == "integral":
                        var = print_integral(equation[-2], text_lower[i + 1])
                        equation = equation.replace(equation[-2], var, 1)
                        i += 2
                    else:
                        equation += df_c.loc[df_c['Name'].str.lower() == str_to_check, 'Symbol'].values[0] + ' '
                        i += len(str_to_check.split())
                    skip_next_words = True
                    break
        if not skip_next_words:
            equation += word + ' '
            i += 1
        else:
            skip_next_words = False

    equation = equation.strip()
    print("Equation:", equation)
    return equation  # Return the equation

@app.route('/')
def index(equation=None):
    return render_template('index.html', equation=equation)
from flask import jsonify

@app.route('/record')
def record():
    equation = from_microphone()  # Record audio using the microphone and get the equation
    return jsonify(equation=equation)  # Return the equation as a JSON response


if __name__ == '__main__':
    app.run(debug=True)

#  st.markdown("""
#                     1. Square brackets[]: Say "open squared brackets" to open and "closed squared brackets" to close.
#                     2. Parenthesis(): Say "open Parenthesis" to open and "closed Parenthesis" to close.
#                     3. Permutation ⁿPₖ : Express as "n permutation k" 
#                     4. Combination ⁿCₖ : Express as "n combination k" 
#                     5. a. Exponents : Use "raised to" or "to the power" to express exponents
#                        b. For square and cube, express as number square or number cube. 
#                     6. Integration : express as "lower limit integral upper limit" to print ₄∫⁵.
#                     7. Modulo : say " modulo your expression modulo " for opening and closing.
#                     """)