# --- IMPORTS ---
import pandas as pd  # For reading CSV files (data tables)
import numpy as np   # For numerical operations and arrays
import tensorflow as tf # The main Deep Learning library (Keras is inside it)
from sklearn.preprocessing import LabelEncoder, StandardScaler # Tools for data preparation
from sklearn.model_selection import train_test_split # Tool to split data
from tensorflow.keras.utils import to_categorical # Tool to convert labels to one-hot encoding
from tensorflow.keras.callbacks import EarlyStopping # Tool to stop training intelligently
import warnings      # To hide unimportant warnings

# Ignore future warnings from sklearn to keep output clean
warnings.simplefilter(action='ignore', category=FutureWarning)

# --- LOAD AND CLEAN DATA ---
try:
    # Read the training and testing data from CSV files into DataFrames
    train_df = pd.read_csv("data/train_data.csv")
    test_df = pd.read_csv("data/test_data.csv")
    print(f"Loaded {len(train_df)} training rows and {len(test_df)} test rows.")
except FileNotFoundError as e:
    # Handle error if files are not found and stop the program
    print(f"Error: File not found. {e}")
    exit()

# Pre-cleaning: Standardize labels (e.g., 'ا' becomes 'أ')
train_df['label'] = train_df['label'].replace('ا', 'أ')
test_df['label'] = test_df['label'].replace('ا', 'أ')

# --- PREPARE LABELS (y) ---
# *** This is the correct way: Fit ONLY on training data ***
label_encoder = LabelEncoder() # Create an empty label encoder (dictionary)

# Get all unique labels from the TRAINING data
all_train_labels = train_df['label'].unique()
all_train_labels.sort() # Sort them alphabetically (good practice)

# Fit (teach) the encoder ONLY with the training labels
label_encoder.fit(all_train_labels)
# Get the total number of unique classes
num_classes = len(label_encoder.classes_)

print(f"\nTotal classes found in training data: {num_classes}")
print(f"Classes: {label_encoder.classes_}")

# --- Convert training labels ---
# 1. Transform text labels ('أ', 'ب'...) to integers (0, 1...)
y_train_full_encoded = label_encoder.transform(train_df['label'])
# 2. Convert integers to one-hot encoding (e.g., 1 -> [0, 1, 0, ...])
y_train_full_categorical = to_categorical(y_train_full_encoded, num_classes=num_classes)

# --- Convert test labels (for final evaluation) ---
y_test_labels = test_df['label'] # Keep the original text labels for comparison later

try:
    # Use the SAME encoder (fit on train) to transform test labels
    y_test_encoded = label_encoder.transform(y_test_labels)
    y_test_categorical = to_categorical(y_test_encoded, num_classes=num_classes)
except ValueError as e:
    # This error happens if a label in test_df was NOT in train_df
    print(f"\n!!! FATAL DATA ERROR !!!")
    print(f"A label in 'test_data.csv' was not present in 'train_data.csv'.")
    print(f"Details: {e}")
    exit()

# --- PREPARE FEATURES (X) ---
# Drop the 'label' column to get only the features (coordinates)
# .values converts the DataFrame to a Numpy array
X_train_full_raw = train_df.drop('label', axis=1).values
X_test_raw = test_df.drop('label', axis=1).values

# Create a scaler to normalize data (mean=0, std=1)
scaler = StandardScaler()

# Fit the scaler ONLY on training features (learn the mean/std)
# and then transform the training features.
X_train_full_scaled = scaler.fit_transform(X_train_full_raw)

# Transform the test features using the SAME mean/std learned from training
# (We only use .transform(), NOT .fit_transform() here - this is crucial)
X_test_scaled = scaler.transform(X_test_raw)

# --- SPLIT TRAINING DATA (for Validation) ---
# Split the full training set into 80% for training, 20% for validation
X_train, X_val, y_train, y_val = train_test_split(
    X_train_full_scaled, y_train_full_categorical, # The data to split
    test_size=0.2, # 20% goes to validation
    random_state=42, # Ensures the split is the same every time
    stratify=y_train_full_categorical # Ensures class balance (e.g., same % of 'س') in both splits
)
print(f"Data split: {X_train.shape[0]} training samples, {X_val.shape[0]} validation samples.")

# --- BUILD THE NEURAL NETWORK MODEL ---
model = tf.keras.Sequential([
    # Input layer: expects 1D arrays of shape (63,)
    tf.keras.layers.Input(shape=(X_train.shape[1],)), # X_train.shape[1] is 63
    
    # Add noise to inputs: helps prevent overfitting
    tf.keras.layers.GaussianNoise(0.02),
    
    # Hidden Layer 1: 128 neurons, 'gelu' activation
    # l2 regularization also helps prevent overfitting
    tf.keras.layers.Dense(128, activation='gelu', kernel_regularizer=tf.keras.regularizers.l2(0.001)),
    # Normalize the outputs of the previous layer: speeds up training
    tf.keras.layers.BatchNormalization(),
    # Dropout layer: randomly "turns off" 40% of neurons during training to prevent overfitting
    tf.keras.layers.Dropout(0.4),
    
    # Hidden Layer 2: 64 neurons
    tf.keras.layers.Dense(64, activation='gelu', kernel_regularizer=tf.keras.regularizers.l2(0.001)),
    tf.keras.layers.BatchNormalization(),
    tf.keras.layers.Dropout(0.3), # Less dropout for deeper layers
    
    # Output Layer:
    # Must have 'num_classes' neurons (one for each letter)
    # 'softmax' converts outputs to probabilities (summing to 1)
    tf.keras.layers.Dense(num_classes, activation='softmax') 
])

# Compile the model: configure it for training
model.compile(
    optimizer='adam', # 'adam' is an efficient and popular optimizer
    loss='categorical_crossentropy', # Use this loss for one-hot encoded labels
    metrics=['accuracy'] # Track 'accuracy' during training
)

# Print a summary of the model's architecture
model.summary()

# --- TRAIN THE MODEL ---
print("\n--- Starting Model Training ---")

# Setup EarlyStopping:
# Monitor 'val_loss' (loss on the validation set)
# Stop if it doesn't improve for 30 epochs (patience=30)
# Restore the weights from the single best epoch
early_stop = EarlyStopping(monitor='val_loss', patience=30, restore_best_weights=True)

# Start the training process
# We don't assign it to 'history' variable, as per your question.
# The model is trained, but we don't keep the log.
model.fit(
    X_train, y_train, # Training data (80%)
    validation_data=(X_val, y_val), # Validation data (20%)
    epochs=500, # Maximum number of training cycles
    batch_size=16, # Train on 16 samples at a time
    callbacks=[early_stop], # Use the EarlyStopping tool
    verbose=1 # Show a progress bar
)
print("--- Training Complete ---")

# --- EVALUATE THE MODEL ---
# First, evaluate on the validation set (the 20% split)
loss_val, acc_val = model.evaluate(X_val, y_val, verbose=0)
print(f"\n Validation Accuracy: {acc_val*100:.2f}%")

# Second, evaluate on the *real* test set ('test_data.csv')
# This is the true measure of the model's performance
print("\n... Evaluating on 'test_data.csv' (True Test Set) ...")
loss_test, acc_test = model.evaluate(X_test_scaled, y_test_categorical, verbose=0)
print(f" Final Test Accuracy: {acc_test*100:.2f}%")

# --- SHOW DETAILED PREDICTIONS ---
print("\n Detailed Predictions on 'test_data.csv':")

# Get the raw probability predictions from the model
predictions = model.predict(X_test_scaled, verbose=0)
# Find the index of the highest probability (the predicted class)
predicted_indices = np.argmax(predictions, axis=1)
# Convert the predicted indices (0, 1...) back to labels ('أ', 'ب'...)
predicted_labels = label_encoder.inverse_transform(predicted_indices)

# Create a clean DataFrame to display results
results_df = pd.DataFrame({
    'True Label': y_test_labels.values, # The real answers
    'Predicted Label': predicted_labels, # The model's guesses
    'Confidence (%)': np.max(predictions, axis=1) * 100 # The model's confidence
})
results_df['Correct?'] = results_df['True Label'] == results_df['Predicted Label']
results_df['Confidence (%)'] = results_df['Confidence (%)'].round(2)

print(results_df.to_string()) # .to_string() ensures all rows are printed

# --- SAVE THE MODEL ---
save = input("\n Do you want to save the model? (y/n): ").strip().lower()
    
# Check for positive answers
if save in ["y", "yes", "نعم", "ن", "نعم."]:
    model.save('my_model.keras')
    print(" Model saved as 'my_model.keras'!")
else:
    # If the answer is not 'y' or 'yes', assume 'no'
    print(" Model was not saved.")