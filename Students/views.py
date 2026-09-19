import pickle
from django.utils import timezone
from django.shortcuts import render
from django.conf import settings
from django.contrib import messages
import os
from .models import Attendance, UserProfile  # Adjust based on your app's models
import os
import cv2
import numpy as np
import shutil  # For cleanup
from django.shortcuts import render
from django.contrib import messages
from django.conf import settings
from django.db import transaction  # Important for atomicity

from insightface.app import FaceAnalysis
from .models import UserProfile

# ==========================================
# LOAD ARCFACE MODEL (ONCE)
# ==========================================
face_app = FaceAnalysis(name="buffalo_l")
face_app.prepare(ctx_id=0, det_size=(640, 640))

EMBEDDING_DIR = os.path.join(settings.BASE_DIR, "embeddings")
os.makedirs(EMBEDDING_DIR, exist_ok=True)


# ==========================================
# STUDENT REGISTRATION (SAFE VERSION)
# ==========================================
def student_register(request):
    if request.method == "POST":
        # Temporary storage for cleanup
        created_user = None
        image_dir = None

        try:
            name = request.POST.get("name")
            loginid = request.POST.get("loginid")
            mobile = request.POST.get("mobile")
            password = request.POST.get("password")
            images = request.FILES.getlist("images")

            # -------------------------------
            # BASIC VALIDATION
            # -------------------------------
            if not all([name, loginid, mobile, password]):
                messages.error(request, "All fields are required.")
                return render(request, "index.html")

            if len(images) < 10:
                messages.error(request, "Please upload at least 10 face images.")
                return render(request, "index.html")

            # Prepare paths (but don't create yet)
            image_dir = os.path.join(settings.MEDIA_ROOT, loginid)
            embedding_path = os.path.join(EMBEDDING_DIR, f"{loginid}.npy")

            # Check if user already exists
            if UserProfile.objects.filter(loginid=loginid).exists():
                messages.error(request, "A user with this Login ID already exists.")
                return render(request, "index.html")

            embeddings = []

            # -------------------------------
            # PROCESS IMAGES (create folder only now)
            # -------------------------------
            os.makedirs(image_dir, exist_ok=True)

            for idx, image_file in enumerate(images, 1):
                img_path = os.path.join(image_dir, f"img_{idx}.jpg")

                # Save uploaded image
                with open(img_path, "wb") as f:
                    for chunk in image_file.chunks():
                        f.write(chunk)

                # Load and process with OpenCV
                img = cv2.imread(img_path)
                if img is None:
                    continue  # Skip bad image

                faces = face_app.get(img)
                if len(faces) == 0:
                    continue  # No face detected

                # Select largest face
                face = max(
                    faces,
                    key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1])
                )
                embeddings.append(face.embedding)

            # -------------------------------
            # FINAL VALIDATION: Face detection
            # -------------------------------
            if len(embeddings) == 0:
                messages.error(request, "No face was detected in any of the uploaded images.")
                raise Exception("No valid face embeddings")  # Trigger cleanup

            mean_embedding = np.mean(embeddings, axis=0)

            # -------------------------------
            # DATABASE TRANSACTION (Atomic)
            # -------------------------------
            with transaction.atomic():
                # Create user inside transaction
                created_user = UserProfile.objects.create(
                    name=name,
                    loginid=loginid,
                    mobile=mobile,
                    password=password  # ⚠️ Remember to hash in production!
                )

                # Save embedding only if user creation succeeds
                np.save(embedding_path, mean_embedding)

            # If we reach here → Everything succeeded
            messages.success(
                request,
                "Registration successful! Face data registered for real-time attendance."
            )
            return render(request, "index.html")

        except Exception as e:
            # -------------------------------
            # CLEANUP ON ANY ERROR
            # -------------------------------
            error_msg = str(e) or "An unexpected error occurred during registration."
            if not error_msg.strip():  # In case e is empty
                error_msg = "Registration failed due to invalid data or processing error."

            messages.error(request, f"Registration failed: {error_msg}")

            # Delete database entry if it was created
            if created_user:
                try:
                    created_user.delete()
                except:
                    pass  # Best effort

            # Delete uploaded images folder
            if image_dir and os.path.exists(image_dir):
                try:
                    shutil.rmtree(image_dir)
                except:
                    pass

            # Delete embedding file if it was somehow saved
            embedding_path = os.path.join(EMBEDDING_DIR, f"{loginid}.npy") if loginid else None
            if embedding_path and os.path.exists(embedding_path):
                try:
                    os.remove(embedding_path)
                except:
                    pass

            return render(request, "index.html")

    # GET request
    return render(request, "index.html")


from datetime import time, datetime

# EXACTLY FROM YOUR IMAGE
TIME_SLOTS = [
    ("P1", time(9, 40),  time(10, 40)),
    ("P2", time(10, 40), time(11, 30)),
    ("P3", time(11, 40), time(12, 30)),
    ("P4", time(12, 30), time(13, 20)),
    ("P5", time(14, 0),  time(14, 50)),
    ("P6", time(14, 50), time(15, 40)),
    ("P7", time(15, 40), time(16, 40)),
]

def get_current_period():
    now = datetime.now().time()
    for period, start, end in TIME_SLOTS:
        if start <= now <= end:
            return period
    return None



import os
import json
import base64
import logging
import csv
import numpy as np
import cv2

from datetime import date, datetime, time
from django.http import JsonResponse, StreamingHttpResponse
from django.conf import settings

from insightface.app import FaceAnalysis
from .models import Attendance

logger = logging.getLogger(__name__)

# =====================================================
# CONFIG
# =====================================================
EMBEDDING_DIR = os.path.join(settings.BASE_DIR, "embeddings")
THRESHOLD = 0.45
live_cap = None

# =====================================================
# TIMETABLE (FROM YOUR IMAGE)
# =====================================================
TIME_SLOTS = [
    ("P1", time(9, 40),  time(10, 40)),
    ("P2", time(10, 40), time(11, 30)),
    ("P3", time(11, 40), time(12, 30)),
    ("P4", time(12, 30), time(13, 20)),
    ("P5", time(14, 0),  time(14, 50)),
    ("P6", time(14, 50), time(15, 40)),
    ("P7", time(15, 40), time(16, 40)),
]

def get_current_period():
    now = datetime.now().time()
    for period, start, end in TIME_SLOTS:
        if start <= now <= end:
            return period
    return None

# =====================================================
# LOAD ARCFACE MODEL
# =====================================================
face_app = FaceAnalysis(name="buffalo_l")
face_app.prepare(ctx_id=0, det_size=(640, 640))

# =====================================================
# LOAD REGISTERED EMBEDDINGS
# =====================================================
def load_known_faces():
    known = {}
    if not os.path.exists(EMBEDDING_DIR):
        return known

    for file in os.listdir(EMBEDDING_DIR):
        if file.endswith(".npy"):
            student_id = file.replace(".npy", "")
            known[student_id] = np.load(
                os.path.join(EMBEDDING_DIR, file)
            )
    return known

KNOWN_FACES = load_known_faces()

# =====================================================
# COSINE DISTANCE
# =====================================================
def cosine_distance(a, b):
    return 1 - np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

# =====================================================
# CAMERA INIT
# =====================================================
def init_live_capture():
    global live_cap
    if live_cap is None or not live_cap.isOpened():
        live_cap = cv2.VideoCapture(0)
        if not live_cap.isOpened():
            logger.error("❌ Camera not accessible")
            live_cap = None

# =====================================================
# CSV EXPORT (HOURLY)
# =====================================================
def write_attendance_csv(attendance):
    csv_dir = os.path.join(settings.MEDIA_ROOT, "attendance_csv")
    os.makedirs(csv_dir, exist_ok=True)

    date_str = attendance.date.strftime("%Y-%m-%d")
    csv_path = os.path.join(csv_dir, f"attendance_{date_str}.csv")

    file_exists = os.path.exists(csv_path)

    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Student ID", "Date", "Period", "Status", "Time"])

        writer.writerow([
            attendance.student_id,
            attendance.date,
            attendance.period,
            attendance.classification,
            attendance.timestamp.strftime("%H:%M:%S")
        ])

# =====================================================
# 🎥 REALTIME STREAM (HOURLY ATTENDANCE)
# =====================================================
def realtime(request):

    def generate_frames():
        init_live_capture()
        today = date.today()

        while True:
            success, frame = live_cap.read()
            if not success:
                break

            period = get_current_period()
            faces = face_app.get(frame)

            for face in faces:
                emb = face.embedding
                bbox = face.bbox.astype(int)

                name = "Unknown"
                min_dist = 1.0

                for sid, ref_emb in KNOWN_FACES.items():
                    dist = cosine_distance(emb, ref_emb)
                    if dist < min_dist:
                        min_dist = dist
                        name = sid

                if min_dist < THRESHOLD and period:
                    attendance, created = Attendance.objects.get_or_create(
                        student_id=name,
                        date=today,
                        period=period,
                        defaults={"classification": "Present"}
                    )
                    if created:
                        write_attendance_csv(attendance)

                color = (0,255,0) if min_dist < THRESHOLD else (0,0,255)

                cv2.rectangle(frame, bbox[:2], bbox[2:], color, 2)
                cv2.putText(
                    frame,
                    f"{name} | {period}",
                    (bbox[0], bbox[1]-10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    color,
                    2
                )

            _, buffer = cv2.imencode(".jpg", frame)
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" +
                buffer.tobytes() +
                b"\r\n"
            )

        if live_cap:
            live_cap.release()

    return StreamingHttpResponse(
        generate_frames(),
        content_type="multipart/x-mixed-replace; boundary=frame"
    )

# =====================================================
# 📸 AUTO ATTENDANCE (BASE64 | HOURLY)
# =====================================================
def auto_attendance(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)

    try:
        data = json.loads(request.body)
        image_data = data.get("image")

        if not image_data:
            return JsonResponse({"error": "No image"}, status=400)

        _, encoded = image_data.split(",", 1)
        frame = cv2.imdecode(
            np.frombuffer(base64.b64decode(encoded), np.uint8),
            cv2.IMREAD_COLOR
        )

        period = get_current_period()
        today = date.today()
        print(today, period)

        faces = face_app.get(frame)
        results = []

        for face in faces:
            emb = face.embedding
            min_dist = 1.0
            student_id = None

            for sid, ref_emb in KNOWN_FACES.items():
                dist = cosine_distance(emb, ref_emb)
                if dist < min_dist:
                    min_dist = dist
                    student_id = sid

            if student_id and min_dist < THRESHOLD and period:
                attendance, created = Attendance.objects.get_or_create(
                    student_id=student_id,
                    date=today,
                    period=period,
                    defaults={"classification": "Present"}
                )
                if created:
                    write_attendance_csv(attendance)

                results.append({
                    "student_id": str(student_id),
                    "period": str(period),
                    "confidence": float(round(1 - float(min_dist), 2)),
                    "status": "Marked" if created else "Already Marked"
                })

        return JsonResponse({
            "period": str(period),
            "faces_detected": len(results),
            "results": results
        })

    except Exception:
        logger.exception("❌ Auto attendance failed")
        return JsonResponse({"error": "Processing error"}, status=500)
