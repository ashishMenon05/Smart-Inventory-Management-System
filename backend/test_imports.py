import sys
import os

print("Testing imports...")

try:
    import numpy
    print(f"numpy ok: {numpy.__version__}")
except Exception as e:
    print(f"numpy error: {e}")

try:
    import cv2
    print(f"cv2 ok: {cv2.__version__}")
except Exception as e:
    print(f"cv2 error: {e}")

try:
    import PIL
    print(f"PIL ok: {PIL.__version__}")
except Exception as e:
    print(f"PIL error: {e}")

try:
    import pyttsx3
    print(f"pyttsx3 initialization...")
    engine = pyttsx3.init()
    print(f"pyttsx3 ok")
except Exception as e:
    print(f"pyttsx3 error: {e}")

try:
    from ultralytics import YOLO
    print(f"ultralytics ok")
except Exception as e:
    print(f"ultralytics error: {e}")

try:
    import tkinter
    print(f"tkinter ok: {tkinter.TkVersion}")
    root = tkinter.Tk()
    root.withdraw()
    print("tkinter root ok")
    root.destroy()
except Exception as e:
    print(f"tkinter error: {e}")

print("Tests finished.")
