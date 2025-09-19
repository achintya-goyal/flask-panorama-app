from flask import Flask, render_template, request, send_from_directory, redirect, url_for
import os
import time
import cv2
import smtplib
from email.message import EmailMessage
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
RESULT_FOLDER = "results"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

def clear_folder(folder):
    """Delete all files in a folder."""
    for f in os.listdir(folder):
        path = os.path.join(folder, f)
        if os.path.isfile(path):
            os.remove(path)

def send_email_with_attachment(filepath):
    msg = EmailMessage()
    msg["Subject"] = "New 360° Panorama Uploaded"
    msg["From"] = "mailidved@gmail.com"   # <-- replace with your Gmail
    msg["To"] = "mailidved@gmail.com"     # <-- replace with your Gmail
    msg.set_content("A new panorama was uploaded from your website!")

    with open(filepath, "rb") as f:
        msg.add_attachment(
            f.read(),
            maintype="image",
            subtype="jpeg",
            filename=os.path.basename(filepath)
        )

    # Gmail SMTP
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login("mailidved@gmail.com", "itkq wtfl fatq dlfm")  # <-- App Password
        smtp.send_message(msg)

@app.route("/")
def index():
    clear_folder(UPLOAD_FOLDER)  # clear old photos when fresh start
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload():
    files = request.files.getlist("images")
    img_paths = []

    for f in files:
        filename = secure_filename(f.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        f.save(filepath)
        img_paths.append(filepath)

    if len(img_paths) < 2:
        return "Need at least 2 photos for stitching!"

    images = [cv2.imread(p) for p in img_paths]
    stitcher = cv2.Stitcher_create()
    status, stitched = stitcher.stitch(images)

    if status != cv2.Stitcher_OK:
        return f"Stitching failed (error code {status})"

    result_filename = f"panorama_{int(time.time())}.jpg"
    result_path = os.path.join(RESULT_FOLDER, result_filename)
    cv2.imwrite(result_path, stitched)

    return render_template("result.html", image=result_filename)

@app.route("/results/<filename>")
def result_file(filename):
    return send_from_directory(RESULT_FOLDER, filename)

@app.route("/final-upload/<filename>", methods=["POST"])
def final_upload(filename):
    filepath = os.path.join(RESULT_FOLDER, filename)
    if os.path.exists(filepath):
        send_email_with_attachment(filepath)
        return f"✅ Panorama {filename} has been emailed successfully!"
    return "❌ File not found!"

if __name__ == "__main__":
    app.run(debug=True)
