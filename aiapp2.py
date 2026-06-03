#user python 3.11
import sys
import pandas as pd
import numpy as np
import tensorflow as tf
from sklearn.preprocessing import LabelEncoder, StandardScaler
import warnings
import os
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)
import cv2
import mediapipe as mp
import math
from PIL import Image, ImageDraw, ImageFont # For drawing Arabic text
import traceback
from bidi.algorithm import get_display
import arabic_reshaper
import asyncio
import os
import winsound  
import pythoncom
from queue import Queue 
import winrt.windows.media.speechsynthesis as tts
import winrt.windows.storage.streams as streams
import joblib

# --- PySide6 Imports ---
from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtGui import QFont, QImage, QPixmap
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QLabel, QPushButton, QComboBox,
    QVBoxLayout, QHBoxLayout, QFrame, QTextEdit
)

# --- SETUP ---
warnings.simplefilter(action='ignore', category=FutureWarning)
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2' 

# ---CONSTANTS ---
# (Tuned values for performance)
STABILITY_THRESHOLD = 0.02
STABILITY_FRAMES = 10
EMA_ALPHA = 0.2
CONFIDENCE_THRESHOLD = 0.80 # (Adjust if needed)
HAND_GONE_FRAMES = 20
INTERNAL_WIDTH = 640
INTERNAL_HEIGHT = 480
FONT_PATH = "C:/Windows/Fonts/arial.ttf" # Font for the text box
FONT_SIZE = 28 # (Made font smaller for the text box)

# ------------------------------------------------------------------
# --- VIDEO WORKER ---
# --- (Refactored: Does NO drawing, only processing) ---
# ------------------------------------------------------------------
class VideoWorker(QThread):
    # Signals to emit data to the GUI
    frameReady = Signal(np.ndarray)  # Emits the raw OpenCV frame (BGR)
    sentenceReady = Signal(str)      # Emits the FULL sentence string
    newWordReady = Signal(str)       # Emits the LAST word (for TTS)
    logMessage = Signal(str)         # Emits status/error messages

    def __init__(self, camera_index=0):
        super().__init__()
        self.running = True
        self.camera_index = camera_index
        # --- State Machine Variables ---
        self.current_sentence = ""
        self.last_predicted_letter = ""
        self.space_added = False
        
        try:
            self.logMessage.emit("Loading model and processors...")#loding text
            # --- search for the model
            model_path = resource_path('my_model.keras')
 
            self.logMessage.emit(f"Loading model from: {model_path}")
            self.model = tf.keras.models.load_model(model_path)
            #now we load the tools to limite file size
            scaler_path = resource_path('scaler.joblib')
            encoder_path = resource_path('label_encoder.joblib')

            self.logMessage.emit(f"Loading scaler: {scaler_path}")
            self.scaler = joblib.load(scaler_path)
            self.logMessage.emit(f"Loading encoder: {encoder_path}")
            self.label_encoder = joblib.load(encoder_path)
            
            
            mp_hands = mp.solutions.hands
            self.mp_drawing = mp.solutions.drawing_utils #drawing skeletons for your hands
            #here is some ruls or sittings for medipipe
            self.hands = mp_hands.Hands(
                static_image_mode=False, #we told medipipe to take hands from live video not from an imeg
                max_num_hands=1, #max hand is only one hand do not take more in the same time 
                min_detection_confidence=0.7, #do not take the hand only if you shure at lest 70% its a hand
                min_tracking_confidence=0.5 #when hand moves and shure pesent drop to loer than 50% do not trake the hand
            )
            self.logMessage.emit("... Model is ready!")
        except Exception as e:
            self.logMessage.emit(f"FATAL ERROR during init: {e}")
            traceback.print_exc() #print a full error report 
            self.running = False

    def run(self):
        # This is the main loop that runs in the background thread
        cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW) #open the cam(0,1,2,3,)
        if not cap.isOpened():
            self.logMessage.emit(f"Error: Could not open camera index {self.camera_index}.")
            return

        self.logMessage.emit(f"Camera feed started on index {self.camera_index}.")
        #some vars for tracking the hand  
        current_state = "MOVING" #when hand is movind do not run the model 
        stable_counter = 0 # when the hand stay stabel(not moving) for x frames then run the model
        last_wrist_pos = None # last position for the wrist importint to know if the hand is moved or not
        hand_gone_counter = 0 # how many frames without hand ? to add space and spech the centenc
        smoothed_distance = 0 # count smothe distance important to avoid jitter 

        while cap.isOpened() and self.running:
            try:
                success, frame = cap.read() #try to read one frame (mae shure camera is working and evry think is fine)
                if not success: 
                    self.msleep(10) # Wait a bit if no frame very important for avoid overlad the CPU 
                    #stop this thread for 10 ms
                    continue
                
                frame = cv2.resize(frame, (INTERNAL_WIDTH, INTERNAL_HEIGHT))
                #resize the frame , make it smaller reslution good for performince

                image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)#OpenCV is weardo , she is read collers as BGR Unlike others read RGB this cod is to fix that
                results = self.hands.process(image_rgb)# take the frame(whith corect collers) and send it to medipipe

                if results.multi_hand_landmarks: #if there are hand 
                    hand_landmarks = results.multi_hand_landmarks[0] #extract data from the hand 0 (the only hand)
                    # Draw landmarks(skeleton) directly on the frame
                    self.mp_drawing.draw_landmarks(frame, hand_landmarks, mp.solutions.hands.HAND_CONNECTIONS)
                    # track the wrist and extract x y from it
                    wrist_landmark = hand_landmarks.landmark[mp.solutions.hands.HandLandmark.WRIST]
                    wrist_pos = (wrist_landmark.x, wrist_landmark.y)

                    if last_wrist_pos is None: last_wrist_pos = wrist_pos #take the farst wrist post 
                    
                    distance = math.sqrt((wrist_pos[0] - last_wrist_pos[0])**2 + (wrist_pos[1] - last_wrist_pos[1])**2) #Calculate Raw Motion Distance
                    smoothed_distance = (EMA_ALPHA * distance) + ((1 - EMA_ALPHA) * (smoothed_distance or 0)) #smothing avoid jitter

                    if smoothed_distance < STABILITY_THRESHOLD: #if smothd mothin is stabel 
                        stable_counter += 1 #start stabeltiy counting 
                    else:
                        stable_counter = 0
                        current_state = "MOVING"
                        last_wrist_pos = wrist_pos
                        smoothed_distance = 0

                    if current_state == "MOVING" and stable_counter > STABILITY_FRAMES: #did the hand was moving but now its stabel ?
                        landmarks_list = [coord for lm in hand_landmarks.landmark for coord in (lm.x, lm.y, lm.z)] #extract position for 21 point x y z 
                        X_test_scaled = self.scaler.transform(np.array([landmarks_list])) #standerized the data -2.5 - 2.5
                        predictions = self.model.predict(X_test_scaled, verbose=0) #send the standerized data to the model and get a reply from it
                        
                        # confidenc persint
                        confidence = np.max(predictions)
                        self.logMessage.emit(f"Prediction Conf: {confidence*100:.2f}%")
                        
                        if confidence > CONFIDENCE_THRESHOLD: # if confidenc persint is greater than 70%(can be changed)
                            predicted_index = np.argmax(predictions) #find the maxemum persent from array [0.1,0.85,0.2]
                            predicted_letter = self.label_encoder.inverse_transform([predicted_index])[0] #aske the transformer wich letter it eqal 2 ?
                            
                            if predicted_letter != self.last_predicted_letter: #De-duplication avoid repiting loops 
                                self.current_sentence += predicted_letter #add the new latter to ouer sentence
                                self.last_predicted_letter = predicted_letter
                                self.sentenceReady.emit(self.current_sentence) # Emit the new sentence (send it to gui)

                        current_state = "STABLE"

                    hand_gone_counter = 0
                    self.space_added = False
                else:
                    # --- "HAND IS GONE" LOGIC ---
                    last_wrist_pos = None
                    stable_counter = 0
                    current_state = "MOVING"
                    if self.last_predicted_letter != "": self.last_predicted_letter = ""#its ok for repeting 
                    
                    hand_gone_counter += 1
                    if hand_gone_counter > HAND_GONE_FRAMES and not self.space_added: #if hands is gone for along enugh and did we actilly add a space last taime? (avoid repiting loop)
                        last_word = self.current_sentence.strip().split(" ")[-1] #extract the last word (to sepeach it)
                        if last_word: self.newWordReady.emit(last_word) #send it to speach thrid 
                        
                        self.current_sentence += " " # add space
                        self.space_added = True #avoid repiting loop
                        self.sentenceReady.emit(self.current_sentence) # Emit sentence with new space (send it to gui)
                
                # --- Emit the frame on EVERY loop ---
                # This fixes the "freezing" when no hand is detected
                self.frameReady.emit(frame)
            
            except Exception as e:
                self.logMessage.emit(f"Error in loop: {e}")
                traceback.print_exc() #error report
        
        cap.release() #turn off the cam
        self.logMessage.emit("Camera feed closed.")

    # Function to stop the thread safely
    def stop(self):
        self.running = False
        self.wait()

    # --- Slots for GUI buttons to call ---
    @Slot()
    def clear_sentence(self):
        self.current_sentence = ""
        self.last_predicted_letter = ""
        self.space_added = True
        self.sentenceReady.emit(self.current_sentence) # Emit the empty sentence

    @Slot()
    def backspace(self):
        if self.current_sentence:
            self.current_sentence = self.current_sentence[:-1]
            self.last_predicted_letter = "" 

            self.hand_gone_counter = 0 
            self.space_added = True 
            self.sentenceReady.emit(self.current_sentence) 
# ----------------------------------------------------
# --- TTS WORKER (The Speaker) ---
# --- (using the new winrt) ---
# ---------------------------------------------------
class TTSWorker(QThread):
    logMessage = Signal(str) #creat signal line with data type string 
    
    def __init__(self):
        super().__init__()#let the class father prepir him self first
        self.running = True #if evry think ok let the run loop loops 
        
        self.text_to_speak_queue = Queue() #creat queue for the speach (its can onle speach a sentence once a time)
        self.output_file = "temp_speech.wav" #temp audeo file name
        
        
        self.synthesizer = None #the arabick speach engie
        self.arabic_voice = None #arabic voice

    @Slot(str)
    def speak(self, text):
        if text:
            self.text_to_speak_queue.put(text)
            self.logMessage.emit(f"TTS: Added '{text}' to queue.")

    def stop(self):
        self.running = False
        self.text_to_speak_queue.put(None) 
        self.wait() #witing for the main thrid to shut down

    async def initialize_engine(self):
    
        try:
            self.logMessage.emit("TTS Thread: Initializing Windows Runtime TTS engine...")
            self.synthesizer = tts.SpeechSynthesizer() #creat the speach engin
            
            voices = tts.SpeechSynthesizer.all_voices # HAY YOU ! YES YOU !!! GIVE ME A LIST OF VOICES YOU HAVE 
            for voice in voices: # hmmmmmm lest see the list that i got from that fool , if its have any arabick voice
                if 'ar' in voice.language:
                    self.arabic_voice = voice
                    self.logMessage.emit(f"TTS Thread: Found Arabic voice: {voice.display_name}")
                    return True
            
            self.logMessage.emit("TTS Thread: FATAL - No Arabic voice found.")
            return False
            
        except Exception as e:
            self.logMessage.emit(f"TTS Thread: Error during init: {e}")
            return False

    async def speak_text_async(self, text):
        if not self.synthesizer or not self.arabic_voice: # if we have what we got (araibic voice)
            self.logMessage.emit("TTS Thread: Engine not ready. Skipping.")
            return

        try:
            self.logMessage.emit(f"TTS Thread: Generating speech for '{text}'...")
            self.synthesizer.voice = self.arabic_voice #now we using arabic voice
            
            # make sound file 
            stream = await self.synthesizer.synthesize_text_to_stream_async(text)
            
            # save file on the storeg
            reader = streams.DataReader(stream)
            await reader.load_async(stream.size)
            data_bytes = bytearray(stream.size)
            reader.read_bytes(data_bytes)
            reader.close()
            stream.close()
            
            with open(self.output_file, "wb") as f:
                f.write(data_bytes)
            
            self.logMessage.emit("TTS Thread: Playing audio file...")
            winsound.PlaySound(self.output_file, winsound.SND_FILENAME) #play the sound
            self.logMessage.emit("TTS Thread: Speech finished.")

        except Exception as e:
            self.logMessage.emit(f"TTS Thread: Error during speech: {e}")
            traceback.print_exc()
        finally:
            #deleting the sound file
            if os.path.exists(self.output_file):
                os.remove(self.output_file)

    def run(self):
        try:
            pythoncom.CoInitialize()#tell widows that we gona use his spech system
            
            # HAY YOU VOICE ENGIN !!! KEEP UP MAN ! 
            if not asyncio.run(self.initialize_engine()):
                self.running = False #if the engin scruo us just stop 
            
            while self.running:
                # wait in queueue
                text = self.text_to_speak_queue.get()
                
                if text is None: # if we are don , we are don
                    self.running = False
                    continue
                
                # SAY MY NAME (spech the text)
                asyncio.run(self.speak_text_async(text))
                
        except Exception as e:
            self.logMessage.emit(f"TTS Thread: FATAL RUN ERROR: {e}")
        finally:
            
            pythoncom.CoUninitialize()
            self.logMessage.emit("TTS Thread stopped.")
# ------------------------------------------------------------------
# --- MAIN WINDOW (The GUI) ---
# --- (This code is based on your modified skeleton) ---
# ------------------------------------------------------------------
class MainWindow(QMainWindow):
    # Signal to send text from GUI to TTS worker
    speakRequest = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Deaf Talk")
        self.resize(1000, 700) # Start a bit larger
        
        # We need this to hold the Arabic text for PIL drawing
        self.current_sentence = "..."
        try:
            self.font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
        except IOError:
            print(f"Font not found at {FONT_PATH}, using default.")
            self.font = ImageFont.load_default()

        # --- Define The Widgets ---
        
        # Top-Left: Video Feed
        self.video_label = QLabel("Connecting to camera...")
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setFrameShape(QFrame.Shape.StyledPanel)
        self.video_label.setScaledContents(True) # Make video fill the label

        # Bottom-Left: Settings Area 
        self.settings_frame = QFrame()
        self.settings_frame.setFrameShape(QFrame.Shape.StyledPanel)
        
        # Create the actual controls
        self.camera_combo = QComboBox()
        self.populate_cameras() # Fill the camera list
        self.speak_button = QPushButton("Speak Full Sentence")
        self.clear_button = QPushButton("Clear All")
        
        # Add controls to the settings_frame
        settings_layout = QVBoxLayout()
        settings_layout.addWidget(QLabel("Settings:"))
        settings_layout.addWidget(self.camera_combo)
        settings_layout.addStretch()
        settings_layout.addWidget(self.speak_button)
        settings_layout.addWidget(self.clear_button)
        self.settings_frame.setLayout(settings_layout)

        # Right: Message Area (Sequential Text)
        self.message_area = QTextEdit("Translated messages will appear here")
        self.message_area.setReadOnly(True) # do nothing but read
        self.message_area.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
        self.message_area.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        # Bottom: Footer (Status Bar)
        self.footer_label = QLabel("very important mote : if ypu dont have any arabic speach engine or voice pleas download it ")
        self.footer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.footer_label.setFrameShape(QFrame.Shape.StyledPanel)
        self.footer_label.setFixedHeight(40) # Give footer a fixed height

        # --- Build The Layout ---
        
        # Left-side layout (Video + Settings)
        layout_left = QVBoxLayout()
        layout_left.addWidget(self.video_label, 5) # 5 parts video
        layout_left.addWidget(self.settings_frame, 2) # 2 parts settings

        # Middle layout (Left + Right)
        layout_middle = QHBoxLayout()
        layout_middle.addLayout(layout_left, 5) # 5 parts left side
        layout_middle.addWidget(self.message_area, 3) # 3 parts right side (messages)

        # Main layout (Middle + Footer)
        layout_main = QVBoxLayout()
        layout_main.addLayout(layout_middle, 12) # 12 parts main area
        layout_main.addWidget(self.footer_label, 1) # 1 part footer
        
        # --- Set Stylesheet ---
        self.setStyleSheet("""
            QWidget {
                background-color: #2E2E2E; /* Dark background */
                color: #E0E0E0;
            }
            QLabel {
                font-size: 16px;
                color: #CCC;
                border: none;
            }
            QFrame {
                 border: 2px solid #000000;
                 background-color: #333;
                 padding: 1px;
                 margin: 1px;
            }
            QPushButton {
                background-color: #555555;
                color: #FFFFFF;
                font-size: 10pt;
                padding: 1px 1px;
                border-radius: 5px;
                border: 1px solid #777777;
            }
            QPushButton:hover {
                background-color: #777777;
            }
            QPushButton:pressed {
                background-color: #777777;
            }
            QComboBox {
                font-size: 10pt;
                padding: 1px;
            }
            /* Specific styles for each section */
            #VideoLabel {
                background-color: #000;
                border: 2px solid #FFFFFF; 
            }
            #MessageLabel {
                background-color: #252525;
                border: 2px solid #000000; 
                color: #00FF00; /* Message text color */
                text-align: right;
                font-size: 24pt;
                font-weight: bold;
            }
            #SettingsFrame {
                background-color: #2E2E2E;
                border:none; 
            }
            #SettingsFrame QLabel {
                border: none;
                background-color: transparent;
            }
            #FooterLabel {
                background-color: #2E2E2E;
                border: 2px solid #000000; 
                font-size: 12pt;
            }
        """)

        # --- Set the Central Widget ---
        central_widget = QWidget()
        central_widget.setLayout(layout_main)
        self.setCentralWidget(central_widget)
        
        # --- Set Object Names for the Stylesheet ---
        self.video_label.setObjectName("VideoLabel")
        self.message_area.setObjectName("MessageLabel")
        self.settings_frame.setObjectName("SettingsFrame")
        self.footer_label.setObjectName("FooterLabel")
        
        # --- Setup Workers and Connections ---
        self.setup_workers()
    
    # --- Worker and Connection Setup ---
    def setup_workers(self):
        # Create the Video Worker
        self.worker = VideoWorker()
        
        # Connect its signals to the GUI slots
        self.worker.frameReady.connect(self.update_video_frame)
        self.worker.sentenceReady.connect(self.update_sentence)
        self.worker.logMessage.connect(self.log_message)
        
        # Create the TTS Worker
        self.tts_worker = TTSWorker()
        self.tts_worker.logMessage.connect(self.log_message)
        
        # Connect signals between workers and GUI
        self.worker.newWordReady.connect(self.tts_worker.speak) # Auto-speak word
        self.speakRequest.connect(self.tts_worker.speak) # Speak-all button
        
        # Connect GUI buttons to the worker's slots
        self.clear_button.clicked.connect(self.worker.clear_sentence)
        
        self.speak_button.clicked.connect(self.speak_all_text)
        self.camera_combo.currentIndexChanged.connect(self.change_camera)

        # Start the threads
        self.tts_worker.start()
        self.worker.start()

    # --- GUI Slot Functions ---
    
    @Slot(np.ndarray)
    def update_video_frame(self, frame_bgr):
        """Receives the raw BGR frame from the worker and displays it."""
        # w for wighd h for hight ch for coller cahnnel
        h, w, ch = frame_bgr.shape
        bytes_per_line = ch * w
        
        # Convert BGR (from OpenCV) to RGB (for QImage)
        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        # Tell QImage it is receiving RGB data
        qt_image = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        
        self.video_label.setPixmap(QPixmap.fromImage(qt_image))
    @Slot(str)
    def update_sentence(self, text):
        """Receives the raw text from the worker and updates the message_area."""
        self.current_sentence = text # Store local copy
        
        # connect the alphabets
        reshaped_text = arabic_reshaper.reshape(text)
        
        
        # gave the text to the boss
        self.message_area.setText(reshaped_text)

    @Slot()
    def speak_all_text(self):
        """Called when the 'Speak Full Sentence' button is clicked."""
        if self.current_sentence.strip():
            # Send the *logical* (un-shaped) text to the TTS worker
            self.speakRequest.emit(self.current_sentence.strip())

    @Slot(int)
    def change_camera(self, index):
        """Called when the ComboBox is changed."""
        self.log_message(f"GUI: Camera change to index {index} requested.")
        # This is an advanced feature that requires safely restarting the thread
        # We will implement this next.
        # self.worker.stop()
        # self.worker = VideoWorker(camera_index=index)
        # ... (reconnect all signals) ...
        # self.worker.start()

    def populate_cameras(self):
        """Finds all available cameras and adds them to the ComboBox."""
        self.camera_combo.clear()
        indices = [i for i in range(5) if cv2.VideoCapture(i, cv2.CAP_DSHOW).isOpened()]
        if not indices:
            self.camera_combo.addItem("No cameras found")
            self.camera_combo.setEnabled(False)
        else:
            for i in indices: 
                self.camera_combo.addItem(f"Camera {i}")

    @Slot(str)
    def log_message(self, message):
        """Prints log messages to the console."""
        print(f"[LOG] {message}")

    def closeEvent(self, event):
        """Ensures all threads are stopped safely when closing the window."""
        self.log_message("Closing application...")
        self.tts_worker.stop()
        self.worker.stop()
        event.accept()


    def keyPressEvent(self, event):
        
        # if button is bacspace
        if event.key() == Qt.Key.Key_Backspace:
            self.log_message("Key: Backspace pressed.")
            

            self.worker.backspace()
            
        else:
            
            super().keyPressEvent(event)
# --- Main execution block ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())