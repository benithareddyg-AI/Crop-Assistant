import serial
import time
import threading
import speech_recognition as sr
import pyttsx3

from flask import Flask, jsonify, render_template


# =====================================================
# SETTINGS
# =====================================================

PORT = "COM3"
BAUD_RATE = 9600


# =====================================================
# FLASK
# =====================================================

app = Flask(__name__)


# =====================================================
# SERIAL
# =====================================================

try:

    arduino = serial.Serial(
        PORT,
        BAUD_RATE,
        timeout=1
    )

    time.sleep(2)

    print("Arduino connected on", PORT)

except Exception as e:

    print()
    print("ERROR: Could not connect to Arduino")
    print("Port:", PORT)
    print(e)
    print()

    arduino = None


# =====================================================
# LOCKS
# =====================================================

serial_lock = threading.Lock()
data_lock = threading.Lock()


# =====================================================
# SENSOR DATA
# =====================================================

sensor_data = {

    "rainValue": 0,
    "rainDetected": False,

    "soundValue": 0,

    "red": 0,
    "green": 0,
    "blue": 0,

    "cropColor": "UNKNOWN",

    "pumpOn": False,
    "buzzerOn": False,

    "connected": False,

    "lastUpdate": ""
}


# =====================================================
# SEND COMMAND TO ARDUINO
# =====================================================

def send_command(command):

    global arduino

    if arduino is None:
        print("Arduino not connected")
        return False

    try:

        with serial_lock:

            arduino.write(
                (command + "\n").encode()
            )

            arduino.flush()

        print("Sent to Arduino:", command)

        return True

    except Exception as e:

        print("Serial command error:", e)

        return False


# =====================================================
# SERIAL READER
# =====================================================

def serial_reader():

    global sensor_data

    while True:

        if arduino is None:

            time.sleep(2)
            continue

        try:

            line = arduino.readline().decode(
                errors="ignore"
            ).strip()

            if not line:
                continue


            print("Arduino:", line)


            # ------------------------------------------------
            # SENSOR DATA
            # ------------------------------------------------

            if line.startswith("DATA,"):

                parts = line.split(",")


                if len(parts) >= 10:

                    try:

                        rain_value = int(parts[1])
                        rain_detected = parts[2] == "1"

                        sound_value = int(parts[3])

                        red = int(parts[4])
                        green = int(parts[5])
                        blue = int(parts[6])

                        crop_color = parts[7]

                        pump_on = parts[8] == "1"
                        buzzer_on = parts[9] == "1"


                        with data_lock:

                            sensor_data["rainValue"] = rain_value

                            sensor_data[
                                "rainDetected"
                            ] = rain_detected

                            sensor_data[
                                "soundValue"
                            ] = sound_value

                            sensor_data["red"] = red
                            sensor_data["green"] = green
                            sensor_data["blue"] = blue

                            sensor_data[
                                "cropColor"
                            ] = crop_color

                            sensor_data[
                                "pumpOn"
                            ] = pump_on

                            sensor_data[
                                "buzzerOn"
                            ] = buzzer_on

                            sensor_data[
                                "connected"
                            ] = True

                            sensor_data[
                                "lastUpdate"
                            ] = time.strftime(
                                "%H:%M:%S"
                            )


                    except Exception as e:

                        print(
                            "Data parsing error:",
                            e
                        )


        except Exception as e:

            print(
                "Serial reader error:",
                e
            )

            time.sleep(1)


# =====================================================
# VOICE ENGINE
# =====================================================

def speak(text):

    print("Assistant:", text)

    try:

        engine = pyttsx3.init()

        engine.say(text)

        engine.runAndWait()

        engine.stop()

    except Exception as e:

        print(
            "Voice output error:",
            e
        )


# =====================================================
# VOICE ASSISTANT
# =====================================================

def voice_assistant():

    recognizer = sr.Recognizer()

    print()
    print("====================================")
    print("VOICE ASSISTANT")
    print("====================================")
    print("Say:")
    print("Turn on motor")
    print("Turn off motor")
    print("Motor status")
    print("What is the rain status")
    print("What colour is the crop")
    print("What is the sound level")
    print("Status")
    print("Exit")
    print("====================================")
    print()


    try:

        microphone = sr.Microphone()

    except Exception as e:

        print(
            "Microphone error:",
            e
        )

        return


    with microphone as source:

        print(
            "Adjusting microphone..."
        )

        recognizer.adjust_for_ambient_noise(
            source,
            duration=1
        )


    speak(
        "Voice assistant is ready."
    )


    while True:

        try:

            print()
            print("Listening...")

            with microphone as source:

                audio = recognizer.listen(
                    source,
                    timeout=5,
                    phrase_time_limit=6
                )


            print("Recognizing...")


            command = recognizer.recognize_google(
                audio
            )

            command = command.lower().strip()


            print(
                "You said:",
                command
            )


            # =================================================
            # MOTOR ON
            # =================================================

            if (
                "turn on motor" in command
                or "start motor" in command
                or "motor on" in command
                or "turn on the motor" in command
                or "start the motor" in command
            ):

                if send_command("PUMP_ON"):

                    speak(
                        "Motor turned on."
                    )

                else:

                    speak(
                        "I could not connect to the Arduino."
                    )


            # =================================================
            # MOTOR OFF
            # =================================================

            elif (
                "turn off motor" in command
                or "stop motor" in command
                or "motor off" in command
                or "turn off the motor" in command
                or "stop the motor" in command
            ):

                if send_command("PUMP_OFF"):

                    speak(
                        "Motor turned off."
                    )

                else:

                    speak(
                        "I could not connect to the Arduino."
                    )


            # =================================================
            # MOTOR STATUS
            # =================================================

            elif (
                "motor status" in command
                or "status of motor" in command
            ):

                with data_lock:

                    motor = sensor_data[
                        "pumpOn"
                    ]

                if motor:

                    speak(
                        "The motor is currently on."
                    )

                else:

                    speak(
                        "The motor is currently off."
                    )


            # =================================================
            # RAIN
            # =================================================

            elif (
                "rain" in command
                or "raining" in command
            ):

                with data_lock:

                    rain = sensor_data[
                        "rainDetected"
                    ]

                    value = sensor_data[
                        "rainValue"
                    ]

                if rain:

                    speak(
                        "Rain is detected. "
                        f"The rain sensor value is {value}."
                    )

                else:

                    speak(
                        "No rain is detected. "
                        f"The rain sensor value is {value}."
                    )


            # =================================================
            # COLOUR
            # =================================================

            elif (
                "colour" in command
                or "color" in command
                or "crop colour" in command
                or "crop color" in command
            ):

                with data_lock:

                    color = sensor_data[
                        "cropColor"
                    ]

                speak(
                    "The detected crop colour is "
                    + color
                )


            # =================================================
            # SOUND
            # =================================================

            elif (
                "sound" in command
                or "microphone" in command
            ):

                with data_lock:

                    sound = sensor_data[
                        "soundValue"
                    ]

                speak(
                    f"The sound sensor value is {sound}."
                )


            # =================================================
            # GENERAL STATUS
            # =================================================

            elif (
                command == "status"
                or "system status" in command
                or "give me status" in command
            ):

                with data_lock:

                    rain = sensor_data[
                        "rainDetected"
                    ]

                    color = sensor_data[
                        "cropColor"
                    ]

                    sound = sensor_data[
                        "soundValue"
                    ]

                    motor = sensor_data[
                        "pumpOn"
                    ]


                if motor:
                    motor_text = "on"
                else:
                    motor_text = "off"


                if rain:
                    rain_text = "detected"
                else:
                    rain_text = "not detected"


                speak(
                    f"Rain is {rain_text}. "
                    f"Crop colour is {color}. "
                    f"Sound level is {sound}. "
                    f"Motor is {motor_text}."
                )


            # =================================================
            # EXIT
            # =================================================

            elif (
                command == "exit"
                or "close assistant" in command
                or "quit" in command
            ):

                speak(
                    "Voice assistant stopped."
                )

                break


            # =================================================
            # UNKNOWN COMMAND
            # =================================================

            else:

                speak(
                    "I did not understand that command."
                )


        except sr.WaitTimeoutError:

            print(
                "No voice detected."
            )


        except sr.UnknownValueError:

            print(
                "Could not understand the voice."
            )


        except sr.RequestError as e:

            print(
                "Speech recognition error:",
                e
            )


        except Exception as e:

            print(
                "Voice assistant error:",
                e
            )


# =====================================================
# WEBSITE API
# =====================================================

@app.route("/api/data")
def get_data():

    with data_lock:

        return jsonify(
            sensor_data.copy()
        )


# =====================================================
# WEBSITE MOTOR ON
# =====================================================

@app.route("/api/motor/on")
def motor_on():

    success = send_command(
        "PUMP_ON"
    )

    return jsonify({
        "success": success,
        "motor": "ON"
    })


# =====================================================
# WEBSITE MOTOR OFF
# =====================================================

@app.route("/api/motor/off")
def motor_off():

    success = send_command(
        "PUMP_OFF"
    )

    return jsonify({
        "success": success,
        "motor": "OFF"
    })


# =====================================================
# WEBSITE
# =====================================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# =====================================================
# START PROGRAM
# =====================================================

if __name__ == "__main__":


    # -----------------------------------------------
    # Start Arduino reader
    # -----------------------------------------------

    reader_thread = threading.Thread(
        target=serial_reader,
        daemon=True
    )

    reader_thread.start()


    # -----------------------------------------------
    # Start voice assistant
    # -----------------------------------------------

    voice_thread = threading.Thread(
        target=voice_assistant,
        daemon=True
    )

    voice_thread.start()


    # -----------------------------------------------
    # Start website
    # -----------------------------------------------

    print()
    print("====================================")
    print("AI CROP FLOW ASSISTANT")
    print("====================================")
    print("Website:")
    print("http://127.0.0.1:5000")
    print("====================================")
    print()


    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False,
        use_reloader=False
    )
