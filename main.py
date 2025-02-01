import cv2
import numpy as np
import time
import pygame
from tkinter import Tk, Button, Label

# Initialize Pygame for sound effects
pygame.mixer.init()
cloak_sound = pygame.mixer.Sound('whoosh.wav')
cloak_sound.play()
# Global variables
cloak_enabled = True
current_color = 'blue'
lower_color = np.array([90, 50, 50])  # Default blue color range
upper_color = np.array([130, 255, 255])
background = None
recording = False
out = None

# Cloak color ranges
cloak_colors = {
    'blue': (np.array([90, 50, 50]), np.array([130, 255, 255])),
    'green': (np.array([35, 50, 50]), np.array([85, 255, 255])),
    'red': (np.array([0, 50, 50]), np.array([10, 255, 255]))
}

# Function to create background
def create_background(cap, num_frames=30):
    print("Capturing background. Please move out of frame.")
    backgrounds = []
    for i in range(num_frames):
        ret, frame = cap.read()
        if ret:
            backgrounds.append(frame)
        else:
            print(f"Warning: Could not read frame {i+1}/{num_frames}")
        time.sleep(0.1)
    if backgrounds:
        # Use median to remove moving objects from the background
        return np.median(backgrounds, axis=0).astype(np.uint8)
    else:
        raise ValueError("Could not capture any frames for background")

# Function to create mask
def create_mask(frame, lower_color, upper_color):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, lower_color, upper_color)
    # Remove noise using morphological operations
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8), iterations=2)
    mask = cv2.morphologyEx(mask, cv2.MORPH_DILATE, np.ones((5, 5), np.uint8), iterations=1)
    return mask

# Function to apply cloak effect
def apply_cloak_effect(frame, mask, background):
    mask_inv = cv2.bitwise_not(mask)
    # Extract the foreground (non-cloak area)
    fg = cv2.bitwise_and(frame, frame, mask=mask_inv)
    # Extract the background (cloak area)
    bg = cv2.bitwise_and(background, background, mask=mask)
    # Combine foreground and background
    return cv2.add(fg, bg)

# Function to handle mouse clicks for color picking
def select_color(event, x, y, flags, param):
    global lower_color, upper_color
    if event == cv2.EVENT_LBUTTONDOWN:
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        selected_color = hsv[y, x]
        # Set a range around the selected color
        lower_color = np.array([selected_color[0] - 10, 50, 50])
        upper_color = np.array([selected_color[0] + 10, 255, 255])
        print(f"Selected color range: {lower_color} to {upper_color}")

# GUI for controls
def create_gui():
    def toggle_cloak():
        global cloak_enabled
        cloak_enabled = not cloak_enabled
        toggle_button.config(text="Cloak: ON" if cloak_enabled else "Cloak: OFF")

    def set_color(color):
        global current_color, lower_color, upper_color
        current_color = color
        lower_color, upper_color = cloak_colors[color]
        color_label.config(text=f"Color: {current_color}")

    def start_recording():
        global recording, out
        recording = True
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        out = cv2.VideoWriter('output.avi', fourcc, 20.0, (640, 480))
        record_button.config(text="Recording...")

    def stop_recording():
        global recording, out
        recording = False
        if out:
            out.release()
        record_button.config(text="Start Recording")

    root = Tk()
    root.title("Invisible Cloak Controls")

    toggle_button = Button(root, text="Cloak: ON", command=toggle_cloak)
    toggle_button.pack()

    color_label = Label(root, text=f"Color: {current_color}")
    color_label.pack()

    Button(root, text="Blue", command=lambda: set_color('blue')).pack()
    Button(root, text="Green", command=lambda: set_color('green')).pack()
    Button(root, text="Red", command=lambda: set_color('red')).pack()

    record_button = Button(root, text="Start Recording", command=start_recording)
    record_button.pack()

    Button(root, text="Stop Recording", command=stop_recording).pack()

    return root

# Main function
def main():
    global frame, background

    print("OpenCV version:", cv2.__version__)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open camera.")
        return

    # Countdown before capturing background
    def countdown(seconds):
        for i in range(seconds, 0, -1):
            print(f"Capturing background in {i} seconds...")
            time.sleep(1)

    countdown(5)
    background = create_background(cap)

    # Create GUI
    gui = create_gui()

    cv2.namedWindow('Invisible Cloak')
    cv2.setMouseCallback('Invisible Cloak', select_color)

    print("Starting main loop. Press 'q' to quit.")
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Could not read frame.")
            time.sleep(1)
            continue

        # Update GUI
        gui.update()

        if cloak_enabled:
            mask = create_mask(frame, lower_color, upper_color)
            result = apply_cloak_effect(frame, mask, background)
        else:
            result = frame

        if recording and out:
            out.write(result)

        cv2.imshow('Invisible Cloak', result)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release resources
    cap.release()
    if out:
        out.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()