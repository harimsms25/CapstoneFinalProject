import cv2
import time
import serial
from picamera2 import Picamera2
from libcamera import controls
from pyzbar.pyzbar import decode, ZBarSymbol
import signal
import sys
import requests
import re

CENTER_LOW = 200  
CENTER_HIGH = 250  
LINE_THRESHOLD = 80
prevData = None
arduino = serial.Serial("/dev/ttyUSB0", 9600, timeout=1)
time.sleep(2)

def send(cmd):
    arduino.write((cmd + "\n").encode())
    
def stopAtExit(signum, frame):
    send('S')
    send('0')
    sys.exit(0)
    
def parseData(raw_text):
    room_match = re.search(r"ROOM:(\d+)", raw_text)
    room = room_match.group(1) if room_match else "Unknown"
    
    item_pattern = r"Qty:\s*(\d+)\s*\|\s*Name:\s*([^|]+)\s*\|\s*Teacher:\s*([^|]+)"
    items_found = re.findall(item_pattern, raw_text)
    
    materials_list = []
    for qty, name, teacher in items_found:
        materials_list.append({
            "quantity": int(qty),
            "name": name.strip(),
            "teacher": teacher.strip()
        })
        
    return {"room": room, "materials": materials_list}

signal.signal(signal.SIGINT, stopAtExit)
signal.signal(signal.SIGTERM, stopAtExit)
signal.signal(signal.SIGUSR1, stopAtExit)

h, w = 720, 1280
picam = Picamera2()
config = picam.create_preview_configuration(
    main={"size": (w, h), "format": 'YUV420'}
)
picam.configure(config)
picam.set_controls({
        "ExposureTime": 8333,
        "AnalogueGain": 12.0,
})
picam.start()
lastCmd = "S"
send("V55,80")
send("K300")
time.sleep(1)
goingForward = 0

while True:

    if lastCmd != "F" or goingForward==5:
        time.sleep(0.15)
        lastCmd='S'
        send(lastCmd)
        time.sleep(0.1)
        goingForward = 0
    else:
        goingForward+=1

    frame = picam.capture_array()
    gray = frame[:h, :w]
    smallgray = cv2.resize(gray, (640, 360), interpolation=cv2.INTER_NEAREST)

    codes = decode(smallgray,symbols=[ZBarSymbol.QRCODE])
    if codes:
        data = codes[0].data.decode('utf-8')
        if data != prevData:
            lastCmd='S'
            send(lastCmd)
            print("QR CODE FOUND:", data)
            try:
                response = requests.get(data, timeout=5)
                if response.status_code == 200:
                    parsed_data = parseData(response.text)
                    print(f"DESTINATION: Room {parsed_data['room']}")
                    print("REQUIRED MATERIALS:")
                    for item in parsed_data["materials"]:
                        print(f"   - [{item['quantity']}x] {item['name']} for Teacher: {item['teacher']}")
                    for i in range (0,3):
                        send("1")
                        time.sleep(0.5)
                        send("0")
                        time.sleep(0.5)
            except requests.exceptions.RequestException as e:
                print(f"? Connection Failed: Could not reach the server. ({e})")
            print("delivering items")
            prevData = data

    roi = smallgray[int(0.66 * 360):360, int(640/7):640-int(640/7)] 
    _, threshold = cv2.threshold(roi,LINE_THRESHOLD,255,cv2.THRESH_BINARY_INV)

    moments = cv2.moments(threshold)
    
    currentCmd = "S" 

    if moments["m00"] > 500: 
        cx = int(moments["m10"] / moments["m00"])

        if cx < CENTER_LOW:
            currentCmd = "L"
        elif cx > CENTER_HIGH:
            currentCmd = "R"
        else:
            currentCmd = "F"

    if currentCmd != lastCmd:
        send(currentCmd)
        lastCmd = currentCmd

picam.stop()
cv2.destroyAllWindows()
