# Human Motion to Sound Converter

## Project Overview
This project is a graduation project developed by seven students from the Technical Institute, Department of Computer Networks and Software. The goal of the project is to convert human movements captured from video into corresponding sounds using a mobile application. The application detects the motion of a person and generates real-time audio feedback based on the detected gestures.

This project combines concepts from computer vision, machine learning, and audio processing to create an interactive experience that translates physical movement into sound.

---

## Team Members
1. sjad
2. sayf
3. hussen
4. amany
5. amna
6. naima
7. kazem

---

## Features
- Real-time motion detection using video input
- Gesture recognition and mapping to specific sounds
- Interactive audio output in response to movement
- Easy-to-use mobile application interface

---

## Technologies Used
- Python for machine learning and signal processing
- TensorFlow / Keras for gesture recognition models
- OpenCV for video capture and motion analysis
- Flutter for cross-platform mobile app development
- Other libraries: NumPy, Pandas, MediaPipe, OpenCV, Pillow

---

## Getting Started

### Prerequisites
- Python 3.10 or 3.11 (newer versions such as 3.12 cause dependency conflicts with OpenCV and MediaPipe)
- pip (consider upgrading with `python -m pip install --upgrade pip`)

### Create a virtual environment
```powershell
py -3.11 -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements-lock.txt
```
Use `py -3.10` if you prefer Python 3.10. Always activate the environment before installing packages or running scripts.

### Run the scripts
- Train the network using the CSV files in the `data` folder:
  ```powershell
  python AI.py
  ```
- Launch real-time gesture detection using the saved model and your webcam:
  ```powershell
  python test_the_model.py
  ```

### Clean up
- Deactivate the environment with `deactivate` when you finish.
- Generated folders such as `venv/`, `__pycache__/`, and `*.pyc` files are now ignored by Git via the `.gitignore` file.

---

## Project Structure
- `AI.py` - trains the neural network from CSV datasets.
- `test_the_model.py` - loads the trained model and performs real-time inference.
- `data/` - training and testing CSV files.
- `my_model.keras` - pre-trained model weights for quick inference.
- `requirements-lock.txt` - pinned dependencies tested with Python 3.11.
- `.gitignore` - ensures virtual environments and generated files are not committed.
