import pandas as pd
import numpy as np
import tensorflow as tf
from sklearn.preprocessing import LabelEncoder, StandardScaler
import warnings
import os

# --- PART 0: SETUP ---
# Ignore warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
# Hide TensorFlow informational messages
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2' 

print("--- Starting Prediction Process ---")

try:
    # --- 1. Load the Saved Model ---
    model_path = 'my_model.keras'
    if not os.path.exists(model_path):
        print(f"Error: Saved model not found at: '{model_path}'.")
        print("Please run the training script first.")
        exit()
        
    print(f"Loading saved model from: '{model_path}'...")
    model = tf.keras.models.load_model(model_path)
    # model.summary() # Uncomment to see the model summary

    # --- 2. Rebuild Processors (Scaler & Encoder) ---
    # We need the original training data to create the same Scaler and Encoder
    print("Loading 'train_data.csv' to rebuild processors...")
    train_df = pd.read_csv("data/train_data.csv")
    
    # Standardize labels as a precaution (e.g., 'ا' -> 'أ')
    train_df['label'] = train_df['label'].replace('ا', 'أ')

    # Extract training data to fit the processors
    X_train_raw = train_df.drop('label', axis=1).values
    y_train_labels = train_df['label'].values

    # 2a. Rebuild Scaler
    scaler = StandardScaler()
    scaler.fit(X_train_raw) # Fit Scaler on training data
    
    # 2b. Rebuild LabelEncoder
    label_encoder = LabelEncoder()
    label_encoder.fit(y_train_labels) # Fit Encoder on training labels
    
    print("... Processors rebuilt. Model is ready!")

    # --- 3. Load and Process New Test Data ---
    print("\nLoading new 'test_data.csv' (for prediction)...")
    test_df = pd.read_csv("data/test_data.csv")
    
    X_test_raw = None
    
    # Check if 'label' column exists
    if 'label' in test_df.columns:
        print("... (Warning: 'label' column found. It will be ignored, using features only.)")
        X_test_raw = test_df.drop('label', axis=1).values
    else:
        print("... (File has no 'label' column. All columns will be used as input features.)")
        X_test_raw = test_df.values
        
    print(f"Found {len(X_test_raw)} samples to predict.")

    # 3a. Apply the Scaler (transform) to the test data
    X_test_scaled = scaler.transform(X_test_raw)

    # --- 4. Make Predictions ---
    print("... Making predictions ...")
    predictions = model.predict(X_test_scaled, verbose=0)
    
    # Get the highest confidence prediction
    predicted_indices = np.argmax(predictions, axis=1)
    predicted_labels = label_encoder.inverse_transform(predicted_indices)
    confidences = np.max(predictions, axis=1) * 100

    # --- 5. Display Results ---
    print("\n✅ --- Final Prediction Results --- ✅")
    
    results_df = pd.DataFrame({
        'Sample #': range(1, len(predicted_labels) + 1),
        'Predicted Label': predicted_labels,
        'Confidence (%)': confidences.round(2)
    })
    
    print(results_df.to_string(index=False))

except FileNotFoundError as e:
    print(f"Error: File not found. {e}")
except ValueError as e:
    print(f"Data Error: {e}")
    print("This might be due to a mismatch in the number of columns (features) between train and test files.")
except Exception as e:
    print(f"An unexpected error occurred: {e}")