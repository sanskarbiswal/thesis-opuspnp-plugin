import cv2
import numpy as np
from math import atan2, cos, sin, pi, sqrt
from flask import Flask, Response, request
import threading


class SMDComponentDetector:
    def __init__(self, debug=False):
        self.cap = None
        self.device_idx = None
        self.running = False
        self.lock = threading.Lock()
        self.app = Flask(__name__)
        self.debug_state = debug
        self.should_stop = threading.Event()

    def list_vc_devices(self, max_devices=3):
        available_devices = []
        for dev_idx in range(max_devices):
            cap = cv2.VideoCapture(dev_idx, cv2.CAP_DSHOW)
            if cap.isOpened():
                available_devices.append(dev_idx)
                cap.release()
        return available_devices

    def connect(self, device_idx=0):
        # Release any existing capture
        if self.cap is not None:
            self.cap.release()

        # Open the new capture
        self.cap = cv2.VideoCapture(device_idx, cv2.CAP_DSHOW)
        if not self.cap.isOpened():
            print(f"Failed to open device {device_idx}")
            return False
        self.device_idx = device_idx
        return True

    def disconnect(self):
        if self.cap is not None:
            self.cap.release()
            self.cap = None
            self.device_idx = None
            return True
        return False

    def reconnect(self):
        if self.device_idx is not None:
            return self.connect(self.device_idx)
        else:
            print("No device to reconnect to. Use connect() to specify a device.")
            return False

    def start(self):
        self.running = True
        # self.flask_cv_thread.start()
        # threading.Thread(target=self.capture_and_diaply_frame).start()

    def stop(self):
        self.running = False
        self.should_stop.set()
        self.disconnect()

    def process_frame(self, desired_angle=0):
        frame = self.cv_frame
        # Crop Image
        height, width = frame.shape[:2]
        crop_size = 400
        center_x, center_y = width // 2, height // 2
        # Define Cropping Area
        x1 = max(center_x - crop_size // 2, 0)
        x2 = min(center_x + crop_size // 2, width)
        y1 = max(center_y - crop_size // 2, 0)
        y2 = min(center_y + crop_size // 2, height)
        cropped_img = frame[y1:y2, x1:x2]
        # Convert to Grayscale
        gray = cv2.cvtColor(cropped_img, cv2.COLOR_BGR2GRAY)

        th_low = 70
        th_high = 80
        # Edge Detection with Canny Edge Detection
        edges = cv2.Canny(gray, th_low, th_high)
        # Find contours from the edges
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Sort contours by area and keep only the top 5
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]

        # Merge the top 5 contours into one
        merged_contour = np.vstack(contours)

        # Create a bounding box around the merged contour
        rect = cv2.minAreaRect(merged_contour)
        box = cv2.boxPoints(rect)
        box = np.intp(box)

        bounding_box_img = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

        # Calculate the angle of orientation
        angle = rect[2]
        if angle < -45:
            angle += 90
        
        # Restrict angle to 2 decimal places
        angle = round(angle, 2)
        # Calculate the delta angle to the desired angle
        delta_angle = desired_angle - angle
        # Get the center of the bounding box for drawing reference lines
        center = (int(rect[0][0]), int(rect[0][1]))
        img_center = (bounding_box_img.shape[1] // 2, bounding_box_img.shape[0] // 2)
        # Calculate the offset between the bounding box center and the image center
        offset = (center[0] - img_center[0], center[1] - img_center[1])

        if self.debug_state:
            # Draw the bounding box on the cropped image
            cv2.drawContours(cropped_img, [box], 0, (0, 255, 0), 2)
            # Embed the angle and delta angle in the image
            cv2.putText(bounding_box_img, f'Current Angle: {angle:.2f} degrees', (10, 30), cv2.FONT_HERSHEY_PLAIN , 1, (0, 255, 255), 1)
            cv2.putText(bounding_box_img, f'Desired Angle: {desired_angle:.2f} degrees', (10, 70), cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 255), 1)
            cv2.putText(bounding_box_img, f'Delta Angle: {delta_angle:.2f} degrees', (10, 110), cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 255), 1)
            cv2.putText(bounding_box_img, f'Offset: {offset}', (10, 150), cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 255), 1)
            # Draw the x and y axis reference lines
            cv2.line(bounding_box_img, (center[0], 0), (center[0], frame.shape[0]), (255, 0, 0), 1)
            cv2.line(bounding_box_img, (0, center[1]), (frame.shape[1], center[1]), (255, 0, 0), 1)

            # Draw the offset lines
            cv2.line(bounding_box_img, img_center, center, (0, 255, 255), 2)
            cv2.circle(bounding_box_img, img_center, 5, (255, 0, 0), -1)  # Mark image center
            cv2.circle(bounding_box_img, center, 5, (0, 255, 0), -1)  # Mark bounding box center

            # TODO: Save the image to a file
        
        # Return the angle and delta angle and offset
        return angle, delta_angle, offset, bounding_box_img


    def generate_frame(self):
        while self.running and self.cap != None:
            ret, frame = self.cap.read()
            if not ret:
                print("Error: Failed to capture frame")
                continue

            self.cv_frame = frame

            ret, buffer = cv2.imencode(".jpg", frame)
            if not ret:
                print("Error: Failed to encode frame")
                continue
            
            fdata = buffer.tobytes()
            yield (b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + fdata + b"\r\n")

    def start_flask_stream(self):
        self.app.add_url_rule("/video_feed", "video_feed", self.video_feed)
        self.app.run(host="127.0.0.1", port=10010, use_reloader=False)

    def video_feed(self):
        return Response(
            self.generate_frame(), mimetype="multipart/x-mixed-replace; boundary=frame"
        )

if __name__ == "__main__":
    detector = SMDComponentDetector()
    devices = detector.list_vc_devices()
    print(f"Found {len(devices)} video capture devices.")
    # try:
    #     detector.connect(devices[1])
    #     try:
    #         th1 = threading.Thread(target=detector.start_flask_stream)
    #         th1.start()
    #         detector.start()
    #         while detector.running:
    #             pass
    #         print("Exiting...")
    #         th1.join()
    #     except Exception as e:
    #         print(e)
    # except IndexError:
    #     print("No video capture devices found.")
