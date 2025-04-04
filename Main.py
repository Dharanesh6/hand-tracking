import time
import math
import numpy as np
import HandTrackingModule as htm
import pyautogui
import subprocess
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import cv2  # Ensure cv2 is imported

# Camera Setup
cap = cv2.VideoCapture(0)
cap.set(3, 640)
cap.set(4, 480)
pTime = 0

# Hand Tracking
detector = htm.handDetector(maxHands=1, detectionCon=0.85, trackCon=0.8)

# Audio Setup
devices = AudioUtilities.GetSpeakers()
volume = cast(devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None), POINTER(IAudioEndpointVolume))
minVol, maxVol = volume.GetVolumeRange()[0], volume.GetVolumeRange()[1]

# Gesture Settings
tipIds = [4, 8, 12, 16, 20]
mode = ''
pyautogui.FAILSAFE = False
volBar, volPer = 400, 0
screenshot_counter = 1  # Unique screenshot filenames

while True:
    success, img = cap.read()
    if not success or img is None:
        print("Error: Could not read frame from camera.")
        continue

    img = detector.findHands(img)
    lmList = detector.findPosition(img, draw=False)
    fingers = []

    if lmList:
        # Thumb
        fingers.append(1 if lmList[tipIds[0]][1] > lmList[tipIds[0] - 1][1] else 0)
        # Other Fingers
        fingers.extend([1 if lmList[tipIds[i]][2] < lmList[tipIds[i] - 2][2] else 0 for i in range(1, 5)])

        # Gesture Controls
        if fingers == [0, 1, 0, 0, 1]:  # Minimize Windows
            pyautogui.hotkey('win', 'down')
            mode = 'Minimize Windows'
        elif fingers == [1, 0, 0, 0, 1]:  # Maximize Windows
            pyautogui.hotkey('win', 'up')
            mode = 'Maximize Windows'
        elif fingers == [0, 0, 1, 1, 1]:  # Screenshot
            screenshot_filename = f"screenshot_{screenshot_counter}.png"
            pyautogui.screenshot(screenshot_filename)
            screenshot_counter += 1
            mode = f'Screenshot Saved: {screenshot_filename}'
        elif fingers == [0, 1, 0, 0, 0]:  # Scroll Up
            pyautogui.scroll(400)
            mode = 'Scroll Up'
        elif fingers == [0, 1, 1, 0, 0]:  # Scroll Down
            pyautogui.scroll(-400)
            mode = 'Scroll Down'
        elif fingers == [1, 1, 1, 1, 1]:  # Cursor Control
            mode = 'Cursor Control'
        elif fingers == [1, 1, 0, 0, 0]:  # Volume Control
            mode = 'Volume Control'
        elif fingers == [0, 1, 1, 1, 1]:  # Left Click
            pyautogui.click()
            mode = 'Left Click'
        elif fingers == [1, 0, 1, 1, 1]:  # Right Click
            pyautogui.rightClick()
            mode = 'Right Click'

    # Volume Control
    if mode == 'Volume Control' and len(lmList) > 8:
        x1, y1 = lmList[4][1], lmList[4][2]
        x2, y2 = lmList[8][1], lmList[8][2]
        length = math.hypot(x2 - x1, y2 - y1)
        vol = np.interp(length, [30, 250], [minVol, maxVol])
        volume.SetMasterVolumeLevel(vol, None)
        volPer = np.interp(vol, [minVol, maxVol], [0, 100])
        volBar = np.interp(vol, [minVol, maxVol], [400, 150])

    # Cursor Control
    if mode == 'Cursor Control' and len(lmList) > 8:
        x1, y1 = lmList[8][1], lmList[8][2]
        w, h = pyautogui.size()
        X = int(np.interp(x1, [50, 590], [0, w - 1]))
        Y = int(np.interp(y1, [50, 300], [0, h - 1]))
        pyautogui.moveTo(X, Y, duration=0.01)

    # Volume Bar Animation
    cv2.rectangle(img, (30, 150), (55, 400), (200, 200, 200), 3)
    cv2.rectangle(img, (30, int(volBar)), (55, 400), (0, 255, 0), cv2.FILLED)
    cv2.putText(img, f'{int(volPer)}%', (20, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    # FPS Counter
    cTime = time.time()
    fps = 1 / ((cTime - pTime) + 0.01)
    pTime = cTime
    cv2.putText(img, f'FPS: {int(fps)}', (480, 50), cv2.FONT_ITALIC, 1, (255, 0, 0), 2)
    cv2.putText(img, mode, (250, 450), cv2.FONT_HERSHEY_COMPLEX_SMALL, 3, (0, 255, 255), 3)
    cv2.imshow('Hand LiveFeed', img)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release resources properly
cap.release()
cv2.destroyAllWindows()
