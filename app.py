from flask import Flask, render_template, request, send_from_directory
import os
from metalearn_video_generator import run_metalearn_pipeline

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "static/output"
OUTPUT_VIDEO = "final_video.mp4"

# Ensure folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate():
    if "pdf" not in request.files:
        return "No PDF uploaded", 400

    pdf = request.files["pdf"]
    if pdf.filename == "":
        return "No selected file", 400

    # Save uploaded PDF
    pdf_path = os.path.join(UPLOAD_FOLDER, pdf.filename)
    pdf.save(pdf_path)

    # Run pipeline with the uploaded file
    output_video_path = os.path.join(OUTPUT_FOLDER, OUTPUT_VIDEO)
    run_metalearn_pipeline(pdf_path, output_video_path)

    # Render the same index.html and show video
    return render_template("index.html", video_path=output_video_path)

@app.route("/video/<filename>")
def serve_video(filename):
    return send_from_directory(OUTPUT_FOLDER, filename)

if __name__ == "__main__":
    app.run(debug=True)
