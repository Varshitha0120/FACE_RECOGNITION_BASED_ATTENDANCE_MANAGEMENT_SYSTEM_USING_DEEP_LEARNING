from django.shortcuts import render

# Create your views here.
from django.contrib import messages

from Students.models import Attendance

def facultyLoginCheck(request):
    if request.method=='POST':
        loginid=request.POST['loginid']
        password=request.POST['password']

        if loginid=="admin" and password=='admin':
            request.session['admin']=True

            return render(request,'faculty/facultyHome.html')
        else:
            messages.error(request,'Invalid details,please try again later')
            return render(request,'facultyLogin.html')
    else:
        return render(request,'facultyLogin.html')
    


from django.shortcuts import render

def facultyHome(request):
    if not request.session.get('admin'):
        return render(request, 'facultyLogin.html')
    return render(request, 'faculty/facultyHome.html')

def log(request):
    request.session.flush()
    return render(request, 'facultyLogin.html')




# import os
# import cv2
# import numpy as np
# from mtcnn import MTCNN
# import face_recognition
# from sklearn.preprocessing import LabelEncoder
# from sklearn.model_selection import train_test_split
# from sklearn.metrics import confusion_matrix
# from tensorflow.keras.models import Sequential
# from tensorflow.keras.layers import Dense
# import pickle
# from django.shortcuts import render
# from django.contrib.auth.decorators import login_required
# from django.conf import settings

# # Initialize MTCNN detector
# detector = MTCNN()

# # Path to dataset (update in settings.py or hardcode for testing)
# DATASET_PATH = "media"

# # Load and preprocess dataset
# import os
# import cv2
# import numpy as np
# import face_recognition
# from pathlib import Path

# def load_dataset(dataset_path):
   
#     embeddings = []
#     labels = []
    
#     # Convert dataset_path to Path object for robust handling
#     dataset_path = Path(dataset_path)
    
#     # Iterate through person directories
#     for person_name in dataset_path.iterdir():
#         if not person_name.is_dir():
#             continue
        
#         # Iterate through images in person directory
#         for image_path in person_name.glob("*.jpg"):  # Adjust for other formats if needed
#             try:
#                 # Load image using OpenCV
#                 image = cv2.imread(str(image_path))
#                 if image is None:
#                     print(f"Failed to load image: {image_path}")
#                     continue
                
#                 # Convert BGR to RGB
#                 image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                
#                 # Detect face locations using face_recognition
#                 face_locations = face_recognition.face_locations(image_rgb, model="hog")  # Use 'cnn' for GPU
#                 if not face_locations:
#                     print(f"No faces detected in: {image_path}")
#                     continue
                
#                 # Compute face embeddings for all detected faces
#                 face_embeddings = face_recognition.face_encodings(image_rgb, face_locations)
#                 if not face_embeddings:
#                     print(f"No embeddings computed for: {image_path}")
#                     continue
                
#                 # Append the first embedding (modify for multiple faces if needed)
#                 embeddings.append(face_embeddings[0])
#                 labels.append(person_name.name)
                
#             except Exception as e:
#                 print(f"Error processing {image_path}: {e}")
#                 continue
    
#     # Convert to NumPy arrays
#     embeddings = np.array(embeddings)
#     labels = np.array(labels)
    
#     # Validate output
#     if embeddings.size == 0:
#         print("Warning: No valid embeddings were computed.")
    
#     return embeddings, labels

# # Build SoftMax classifier
# def build_classifier(input_dim, num_classes):
#     model = Sequential([
#         Dense(64, activation='relu', input_dim=input_dim),
#         Dense(num_classes, activation='softmax')
#     ])
#     model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])
#     return model

# # Calculate performance metrics
# def calculate_metrics(y_true, y_pred):
#     cm = confusion_matrix(y_true, y_pred)
#     if cm.shape == (2, 2):
#         tn, fp, fn, tp = cm.ravel()
#     else:
#         tn = cm.sum() - (cm.sum(axis=0) + cm.sum(axis=1) - np.diag(cm)).sum()
#         fp = cm.sum(axis=0) - np.diag(cm)
#         fn = cm.sum(axis=1) - np.diag(cm)
#         tp = np.diag(cm)
#         tn, fp, fn, tp = np.sum(tn), np.sum(fp), np.sum(fn), np.sum(tp)
    
#     accuracy = (tp + tn) / (tp + tn + fp + fn)
#     sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0
#     specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
#     precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    
#     return {
#         'accuracy': round(accuracy * 100, 2),
#         'sensitivity': round(sensitivity * 100, 2),
#         'specificity': round(specificity * 100, 2),
#         'precision': round(precision * 100, 2)
#     }


# def training(request):
#     if not request.session.get('admin'):
#         return render(request, 'facultyLogin.html')

#     # Load dataset
#     embeddings, labels = load_dataset(DATASET_PATH)
#     print("Dataset loading successful")

#     if len(embeddings) == 0:
#         return render(request, 'faculty/training.html', {
#             'error': 'No valid data loaded. Check dataset path and images.'
#         })

#     # Encode labels
#     encoder = LabelEncoder()
#     encoded_labels = encoder.fit_transform(labels)

#     # Train-test split
#     X_train, X_test, y_train, y_test = train_test_split(
#         embeddings, encoded_labels, test_size=0.3, random_state=42
#     )

#     # Build and train the model
#     num_classes = len(np.unique(encoded_labels))
#     model = build_classifier(input_dim=128, num_classes=num_classes)
#     model.fit(X_train, y_train, epochs=10, batch_size=32, verbose=1)

#     # Evaluate model
#     y_pred = model.predict(X_test).argmax(axis=1)
#     metrics = calculate_metrics(y_test, y_pred)

#     # Save model and label encoder
#     model_path = os.path.join(settings.BASE_DIR, 'models', 'softmax_model.h5')
#     encoder_path = os.path.join(settings.BASE_DIR, 'models', 'label_encoder.pkl')
#     os.makedirs(os.path.dirname(model_path), exist_ok=True)
#     model.save(model_path)
#     with open(encoder_path, 'wb') as f:
#         pickle.dump(encoder, f)

#     # Render training result
#     return render(request, 'faculty/training.html', {
#         'metrics': metrics,
#         'success': 'Model trained successfully.'    
#     })

    # Run real-time recognition
from collections import defaultdict
from django.shortcuts import render
from django.utils.timezone import localtime
from Students.models import Attendance
from collections import defaultdict

from collections import defaultdict
from django.shortcuts import render
from django.utils.timezone import localtime

def studentAttendance(request):
    if not request.session.get('admin'):
        return render(request, 'facultyLogin.html')

    records = Attendance.objects.order_by('date', 'period', 'student_id')


    for rec in records:
        rec.local_time = localtime(rec.timestamp)
        print(rec.date, rec.period, rec.student_id, rec.classification, rec.local_time)

    return render(request, 'faculty/attendance.html', {
        'records': records,
        'title': 'Day-wise Hourly Attendance'
    })


def dayWiseReports(request):
    if not request.session.get('admin'):
        return render(request, 'facultyLogin.html')

    context = {}

    if request.method == "POST":
        selected_date = request.POST.get("date")

        exists = Attendance.objects.filter(date=selected_date).exists()

        if exists:
            context["file_exists"] = True
            context["selected_date"] = selected_date
        else:
            context["file_exists"] = False
            context["error"] = "No attendance found for selected date"

    return render(request, 'faculty/daywisereport.html', context)

import csv
from django.http import Http404, HttpResponse
from django.utils.timezone import localtime
from Students.models import Attendance

def download_daywise_csv(request, date):
    if not request.session.get('admin'):
        return render(request, 'facultyLogin.html')

    records = Attendance.objects.filter(date=date).order_by(
        'student_id', 'period'
    )

    if not records.exists():
        raise Http404("No attendance found for selected date")

    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = (
        f'attachment; filename="attendance_{date}.csv"'
    )

    writer = csv.writer(response)
    writer.writerow(["Student ID", "Date", "Period", "Status", "Time (IST)"])

    for rec in records:
        local_ts = localtime(rec.timestamp)
        writer.writerow([
            rec.student_id,
            rec.date,
            rec.period,
            rec.classification,
            local_ts.strftime("%I:%M %p")
        ])

    return response

