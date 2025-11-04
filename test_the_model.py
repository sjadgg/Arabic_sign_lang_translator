# VERY VERY VERYYYYYYYY IMPORTANT NOTE : USER PYHON 3.11 OR 3.10
import pandas as pd
import numpy as np
import tensorflow as tf
from sklearn.preprocessing import LabelEncoder, StandardScaler
import warnings
import os
import cv2
import mediapipe as mp
import math
from PIL import Image, ImageDraw, ImageFont # For drawing Arabic text
import traceback # For detailed error printing
from bidi.algorithm import get_display
import arabic_reshaper

#take cears of warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2' 

# --- CONSTANTS ---
# Stability filter settings
# (Increased threshold to 20 and frames to 12 to handle MediaPipe jitter)
STABILITY_THRESHOLD = 12 # (in pixels) How much movement to ignore?
STABILITY_FRAMES = 7  # How many stable frames before we "trust" the pose?

# Sentence logic settings
HAND_GONE_FRAMES = 20 # How many frames before we add a "space"

# Text box display settings
TEXT_BOX_HEIGHT = 100 # Height of the black box in pixels
FONT_PATH = "C:/Windows/Fonts/arial.ttf" # Path to a .ttf font file
FONT_SIZE = 40
TEXT_COLOR_PIL = (0, 255, 0) # Green (RGB for Pillow)


try:
    # --- Load Model & Processors ---
    print("Loading model and processors...")
    model = tf.keras.models.load_model('my_model.keras')
    
    print("Loading 'train_data.csv' to rebuild processors...")
    # (Ensure this path 'data/train_data.csv' is correct for you)
    train_df = pd.read_csv("data/train_data.csv")
    train_df['label'] = train_df['label'].replace('ا', 'أ') # Standardize
    
    # Rebuild Scaler
    X_train_raw = train_df.drop('label', axis=1).values
    scaler = StandardScaler().fit(X_train_raw)
    
    # Rebuild LabelEncoder
    y_train_labels = train_df['label'].values
    label_encoder = LabelEncoder().fit(y_train_labels)
    

    # ---SETUP FONT (for Pillow) ---
    try:
        font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
    except IOError:
        print(f"Error: Font file not found at {FONT_PATH}.")
        print("Using default font (may not support Arabic).")
        font = ImageFont.load_default()

    # --- SETUP MEDIAPIPE AND CAMERA ---
    mp_hands = mp.solutions.hands
    mp_drawing = mp.solutions.drawing_utils
    hands = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1, # Only track one hand
        min_detection_confidence=0.7,
        min_tracking_confidence=0.5
    )

    # (Use 0, 1, or 2 based on your camera index)
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW) 
    if not cap.isOpened():
        print("Error: Could not open camera.")
        exit()

    # --- PART 5: STATE MACHINE VARIABLES ---
    current_state = "MOVING"        # Current state: "MOVING" or "STABLE"
    stable_counter = 0              # Frame counter for stability
    last_wrist_pos = None           # To store the last wrist position
    
    current_sentence = ""           # The full sentence being built
    last_predicted_letter = ""      # To prevent letter spam
    hand_gone_counter = 0           # Frame counter for when the hand disappears
    space_added = False             # Lock to prevent space spam

    print("Camera feed started. Press 'ESC' or Ctrl+C to quit.")

    # ---MAIN CAMERA LOOP ---
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            continue

        # Flip the frame (like a mirror)
        frame = cv2.flip(frame, 1)
        # Convert to RGB for MediaPipe
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # Process the frame
        results = hands.process(image_rgb)
        
        # Get frame dimensions
        h, w, _ = frame.shape
        # Create a new black canvas (image + text box)
        canvas = np.zeros((h + TEXT_BOX_HEIGHT, w, 3), dtype="uint8")
        # Paste the video frame onto the top part of the canvas
        canvas[0:h, 0:w] = frame # Use the original BGR frame for pasting

        hand_detected = False
        
        if results.multi_hand_landmarks:
            # --- HAND IS DETECTED ---
            hand_detected = True
            hand_landmarks = results.multi_hand_landmarks[0]
            
            # Draw the hand landmarks onto the canvas
            mp_drawing.draw_landmarks(
                canvas, # Draw on the canvas
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS
            )

            # ---WRIST MOTION FILTER LOGIC ---
            wrist_landmark = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST]
            wrist_pos = (wrist_landmark.x * w, wrist_landmark.y * h)
            
            if last_wrist_pos is None:
                last_wrist_pos = wrist_pos # Initialize on first frame
            
            # Calculate movement distance
            distance = math.sqrt(
                (wrist_pos[0] - last_wrist_pos[0])**2 + 
                (wrist_pos[1] - last_wrist_pos[1])**2
            )

            # Update state machine based on movement
            if distance < STABILITY_THRESHOLD:
                # Hand is stable
                stable_counter += 1
            else:
                # Hand is moving
                stable_counter = 0
                current_state = "MOVING"
                # We do NOT reset last_predicted_letter here (this prevents spam)
                last_wrist_pos = wrist_pos # Update the anchor position

            # --- PREDICTION LOGIC ---
            # Check if hand is stable AND was previously moving
            if current_state == "MOVING" and stable_counter > STABILITY_FRAMES:
                
                # --- Time to Predict! (Run model once) ---
                
                # Extract all 63 landmarks
                landmarks_list = []
                for landmark in hand_landmarks.landmark:
                    landmarks_list.extend([landmark.x, landmark.y, landmark.z])
                
                X_test_raw = np.array([landmarks_list])
                
                # Apply the Scaler
                X_test_scaled = scaler.transform(X_test_raw)

                # Make Prediction
                predictions = model.predict(X_test_scaled, verbose=0)
                
                predicted_index = np.argmax(predictions)
                confidence = np.max(predictions)
                predicted_letter = label_encoder.inverse_transform([predicted_index])[0]

                # (NEW SPAM FIX)
                # Only add the letter if confidence is high
                # AND it's different from the last letter added
                if confidence > 0.80 and predicted_letter != last_predicted_letter:
                    current_sentence += predicted_letter
                    last_predicted_letter = predicted_letter # Set the spam lock
                
                # Set state to "STABLE" (prevents spam on next frame)
                current_state = "STABLE"

            # Reset "hand gone" counters because the hand is visible
            hand_gone_counter = 0
            space_added = False
            
        else:
            # --- "HAND IS GONE" LOGIC (Your Idea) ---
            # No hand detected in this frame
            last_wrist_pos = None
            stable_counter = 0
            current_state = "MOVING"
            
            # (NEW SPAM FIX)
            # Reset the spam lock ONLY when the hand disappears
            last_predicted_letter = "" 
            
            # Increment the "hand gone" counter
            hand_gone_counter += 1
            
            # If hand is gone for long enough, add a space
            if hand_gone_counter > HAND_GONE_FRAMES and not space_added:
                current_sentence += " " # Add one space
                space_added = True # Lock to prevent space spam

        # --- 10. DISPLAY TEXT (Using Pillow for Arabic support) ---
        # Convert the OpenCV canvas (Numpy) to a PIL Image
        pil_image = Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(pil_image)

        # (NEW) Apply BIDI to fix Right-to-Left (RTL) text ordering
        reshaped_text = arabic_reshaper.reshape(current_sentence)
        bidi_text = get_display(reshaped_text)

        # Draw the sentence text on the image
        draw.text(
            (w - 50, h + (TEXT_BOX_HEIGHT // 2)), # Position (start from the right)
            bidi_text, # (MODIFIED) We now draw the corrected bidi_text
            font=font, 
            fill=TEXT_COLOR_PIL,
            anchor="rm" # Anchor: 'r'ight, 'm'iddle
        )
        
        # Convert back to OpenCV format (Numpy) for display
        final_frame = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

        # Display the final frame (Video + Text Box)
        cv2.imshow('Arabic Sign Language Recognition', final_frame)

        # --- (MODIFIED) KEYBOARD INPUT & EXIT ---
        # Wait 5ms for a key press and get its ASCII value
        key = cv2.waitKey(5) & 0xFF

        # Exit loop if 'ESC' key is pressed (ASCII 27)
        if key == 27:
            print("\nESC key pressed. Exiting...")
            break
            
        # (NEW) Check for 'Backspace' key (ASCII 8)
        if key == 8:
            # Use string slicing to remove the last character
            current_sentence = current_sentence[:-1]
            
            # (Spam Fix) Reset the letter spam lock
            last_predicted_letter = "" 
            
            # (Spam Fix) Reset the spacebar lock
            space_added = False 

    # --- CLEANUP ---
    print("\nCamera feed closed.")
    print(f"Final Sentence: {current_sentence}")

except KeyboardInterrupt:
    # (NEW) Handle Ctrl+C gracefully
    print("\nInterrupted by user (Ctrl+C). Exiting...")
except Exception as e:
    print(f"\nAn unexpected error occurred: {e}")
    traceback.print_exc() # Print detailed error
finally:
    # This 'finally' block ensures resources are freed NO MATTER WHAT
    print("Cleaning up resources...")
    if 'hands' in locals():
        hands.close()
    if 'cap' in locals() and cap.isOpened():
        cap.release()
    cv2.destroyAllWindows()