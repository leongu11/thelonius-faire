######remember sudo pigpiod to start daemon
from gpiozero import AngularServo
from gpiozero.pins.pigpio import PiGPIOFactory
from time import sleep
import cv2
from picamera2 import Picamera2
from threading import Thread
import random
factory = PiGPIOFactory()
singalPIN = 3
servo2 = AngularServo(singalPIN, min_angle=0, max_angle=180, min_pulse_width=0.0005, max_pulse_width=0.0025,pin_factory = factory)
singalPIN2 = 4
servo = AngularServo(singalPIN2, min_angle=0, max_angle=180, min_pulse_width=0.0005, max_pulse_width=0.0025,pin_factory = factory)
signalPIN3 = 2
servo3 = AngularServo(signalPIN3, min_angle=0, max_angle=180, min_pulse_width=0.0005, max_pulse_width=0.0025,pin_factory = factory)
sp2 = 17
sp1 = 27
sp3 = 22
servo4 = AngularServo(sp1, min_angle=0, max_angle=180, min_pulse_width=0.0005, max_pulse_width=0.0025,pin_factory = factory)
servo5 = AngularServo(sp2, min_angle=0, max_angle=180, min_pulse_width=0.0005, max_pulse_width=0.0025,pin_factory = factory)
servo6 = AngularServo(sp3, min_angle=0, max_angle=180, min_pulse_width=0.0005, max_pulse_width=0.0025,pin_factory = factory)

## CAMERA ANGLE 0-1

##HORI INIT 
HMIN,HMAX = 110,150
DEF = 130
rightoff = 10
#init defaults
def initservos():
    servo2.angle = DEF
    servo3.angle=100
    servo.angle = 80
    servo4.angle = DEF+rightoff
    servo6.angle = 60
    servo5.angle = 70

CASCADE_PATH = '/usr/share/opencv4/haarcascades/haarcascade_frontalface_alt2.xml'
face_cascade = cv2.CascadeClassifier(CASCADE_PATH)

if face_cascade.empty():
    print("ERROR: cascade failed to load")
    exit(1)


##setup printer
from escpos.printer import File
import time as time_module  # you already import sleep from time, so aliasing avoids clashing

THELONIOUS_LINES = [
    "Thelonious has spoken! A maker stands before him!",
    "Thelonious has decided... start making!",
    "SCAN COMPLETE... maker prodigy recognized.",
    "Thelonious is impressed. This maker is well versed in his craft!",
    "Thelonious knows he has found the one! You are the chosen maker!",
    "Thelonious has spoken. You are a future maker.",
    "Thelonious knows he has found the one! You are a special maker!",
]

BIOMETRIC_LINES = [
    "SUBJECT SCANNED.\nCREATIVITY: ELEVATED.\nSLEEP: CRITICALLY LOW.",
    "FACE ACQUIRED.\nDESTINY: LOADING.\nPLEASE WAIT.",
    "SCAN COMPLETE.\nVERDICT: PROBABLY A MAKER.",
]

def get_message():
    thelonious_line = random.choice(THELONIOUS_LINES)
    scan_line = random.choice(BIOMETRIC_LINES)
    return f"{scan_line}\n\n{thelonious_line}"

PRINT_AFTER_SECONDS = 5
MAX_GAP_SECONDS = 1.0     # a face can be "missing" for up to 1 second without resetting

face_start_time = None
last_seen_time = None
already_printed = False
LOGO_PATH = "/home/leonguyen/logo_bw.png"          # the face logo
def _print_job():
    try:
        p = File("/dev/usb/lp0")
        p._raw(b'\x1b\x37\x03\x80\x0f')
        # --- fortune message up top ---
        p.text(get_message() + "\n\n")
        
        # --- logo, name, and QR codes at the bottom ---
        from PIL import Image
        logo = Image.open(LOGO_PATH)
        logo = logo.resize((logo.width // 2, logo.height // 2), Image.LANCZOS)
        logo = logo.convert("L").point(lambda x: 0 if x < 160 else 255, mode="1")
        p.set(align="center")
        p.image(logo, impl="bitImageColumn")
        
        p.text("\n")
        p.set(bold=True)
        p.text(f"Built by Leo Nguyen\n Follow Thelonius instagram:\n'thelonius.official.real'\nTake a look at my github:\n @leongu11")
        p.set(bold=False)

        p.cut()
        p.close()
        print("Printed!")
    except Exception as e:
        print(f"Print failed: {e}")

def print_scan():
    Thread(target=_print_job, daemon=True).start()
##picam2 = Picamera2()
##picam2.configure(picam2.create_video_configuration(
##    main={"size": (640, 480), "format": "XRGB8888"}
##))
##picam2.start()
cap = cv2.VideoCapture(0)
 
smoothed_x, smoothed_y = 0.5, 0.5
ALPHA = 0.3
last_target = None
lost_frames = 0
LOST_TIMEOUT = 100
 
def blink(blinkTime):
    servo3.angle = 55
    servo5.angle = 120
    sleep(blinkTime)
    servo3.angle = 100
    servo5.angle = 70
    sleep(blinkTime)
 
def lookhori(stallTime,dirAngle):
    servo2.angle = dirAngle
    servo4.angle = dirAngle
    sleep(stallTime)
def lookup(upTime):
    servo.angle = 70
    servo6.angle = 80
    sleep(upTime)
    initservos()
    sleep(upTime)
def bootup():
    blink(0.15)
    blink(0.15)
    lookhori(1,150)
    lookhori(1,110)
    lookhori(1,150)
    lookhori(1,110)
    initservos()
    
##blink inits
def blinkThread():
    while True:
        blinkTime = random.randint(1,4)
        servo3.angle = 55
        servo5.angle = 120
        sleep(0.15)
        servo3.angle = 80
        servo5.angle = 90
        sleep(blinkTime)
 
##bootupsequence
initservos()
bootup()
 
blinkthread = Thread(target = blinkThread,daemon = True)
blinkthread.start()
try:
    while True:
        ret,frame = cap.read()
##        frame = picam2.capture_array()[:, :, :3]
        display = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(display, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)
        faces = face_cascade.detectMultiScale(
            gray, scaleFactor=1.05, minNeighbors=4, minSize=(80, 80)
        )
 
        # --- simple 5-second print trigger (tolerant of brief misses) ---
        now = time_module.time()

        if len(faces) > 0:
            if face_start_time is None:
                face_start_time = now
            last_seen_time = now
        else:
            if last_seen_time is not None and now - last_seen_time > MAX_GAP_SECONDS:
                # face has genuinely been gone for a while -> reset
                face_start_time = None
                already_printed = False
                last_seen_time = None

        if face_start_time is not None:
            elapsed = now - face_start_time
            if elapsed >= PRINT_AFTER_SECONDS and not already_printed:
                print_scan()
                already_printed = True
        # --- end print trigger ---
 
        if len(faces) > 0:
            if last_target is None:
                x, y, w, h = max(faces, key=lambda f: f[2]*f[3])
            else:
                x, y, w, h = min(
                    faces,
                    key=lambda f: (f[0]+f[2]/2 - last_target[0])**2
                                + (f[1]+f[3]/2 - last_target[1])**2
                )
 
            cx, cy = x + w/2, y + h/2
            last_target = (cx, cy)
 
            lost_frames = 0
            target_x_norm = cx / display.shape[1]
            target_y_norm = cy / display.shape[0]
            smoothed_x = ALPHA * target_x_norm + (1 - ALPHA) * smoothed_x
            smoothed_y = ALPHA * target_y_norm + (1 - ALPHA) * smoothed_y
            horiScale= cx/640
            ## min + range*angle
            horiMove = 150 - horiScale*(HMAX-HMIN)
            servo2.angle = horiMove
            servo4.angle = horiMove+rightoff
            cv2.rectangle(display, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.circle(display, (int(cx), int(cy)), 6, (0, 255, 255), -1)
        else:
            lost_frames += 1
            if lost_frames > LOST_TIMEOUT:
                last_target = None
 
        cv2.putText(display,
                    f"gaze: ({smoothed_x:.2f}, {smoothed_y:.2f})",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
 
        cv2.imshow("Face", display)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
finally:
    picam2.stop()
    cv2.destroyAllWindows()
 
