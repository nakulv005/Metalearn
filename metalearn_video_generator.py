import os
import sys
import time
import pytesseract
from pdf2image import convert_from_path
import pyttsx3
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import ImageSequenceClip, AudioFileClip, ImageClip, concatenate_videoclips
import textwrap
import requests
from duckduckgo_search import DDGS
from duckduckgo_search.exceptions import RatelimitException
from moviepy.video.fx.fadein import fadein
from moviepy.video.fx.fadeout import fadeout

# === Clean Old Outputs ===
def clean_previous_outputs():
    print("🧹 Cleaning old files...")
    if os.path.exists("voice.mp3"):
        os.remove("voice.mp3")
    if os.path.exists("final_video.mp4"):
        os.remove("final_video.mp4")
    if os.path.exists("debug_text.txt"):
        os.remove("debug_text.txt")
    if os.path.exists("slides"):
        for f in os.listdir("slides"):
            os.remove(os.path.join("slides", f))
    else:
        os.makedirs("slides")
    print("✅ Old outputs cleaned.\n")


# === Step 1: OCR extract text ===
def extract_text_from_scanned_pdf(pdf_path):
    print("🔍 Converting PDF to images for OCR...")
    pages = convert_from_path(pdf_path, dpi=300)
    text_list = []
    for i, page in enumerate(pages):
        text = pytesseract.image_to_string(page)
        text_list.append(text)
        print(f"✅ OCR Extracted Page {i+1}")
        print("----- Text Start -----")
        print(text[:200])
        print("----- Text End -----")
    return text_list


# === Step 2: Voice generation (offline) ===
def generate_voice(text, output_audio="voice.mp3"):
    engine = pyttsx3.init()
    engine.setProperty("rate", 150)
    engine.save_to_file(text, output_audio)
    engine.runAndWait()
    print("✅ Voiceover generated (offline):", output_audio)


# === Step 3: Create animated slides with images ===
def create_animated_slides(pages, output_folder="slides"):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    try:
        font_title = ImageFont.truetype("arialbd.ttf", 48)
        font_body = ImageFont.truetype("arial.ttf", 28)
    except:
        font_title = ImageFont.load_default()
        font_body = ImageFont.load_default()

    slide_index = 1

    for i, text in enumerate(pages[:10]):
        lines = text.strip().split('\n')
        title = lines[0].strip() if lines else f"Slide {i+1}"
        summary = " ".join(lines[1:4]).strip()

        with DDGS() as ddgs:
            try:
                results = ddgs.images(title, max_results=4)
            except RatelimitException as e:
                print(f"⚠️ DuckDuckGo rate limited us: {e}")
                results = []

            for j, result in enumerate(results):
                try:
                    img_data = requests.get(result["image"], timeout=10).content
                    img = Image.open(requests.get(result["image"], stream=True).raw).convert("RGB")
                    img = img.resize((600, 350))
                except Exception as e:
                    print(f"❌ Failed to download image {j+1} for '{title}': {e}")
                    continue

                # Create slide
                slide = Image.new('RGB', (1280, 720), color=(240, 248, 255))
                draw = ImageDraw.Draw(slide)

                draw.text((50, 30), title[:60], fill=(0, 51, 102), font=font_title)

                wrapped = textwrap.wrap(summary[:300], width=70)
                y_text = 110
                for line in wrapped:
                    draw.text((50, y_text), line, fill=(0, 0, 0), font=font_body)
                    y_text += font_body.getbbox(line)[3] + 5

                slide.paste(img, (340, 340))

                path = os.path.join(output_folder, f"slide_{slide_index}.png")
                slide.save(path)
                print(f"✅ Slide saved: {path}")
                slide_index += 1

                time.sleep(2)  # ✅ Delay to avoid DuckDuckGo rate limiting


# === Step 4: Combine slides + voice ===
def create_video_from_slides(slide_folder="slides", audio_path="voice.mp3", output="final_video.mp4"):
    slide_images = sorted(
        [f"{slide_folder}/{img}" for img in os.listdir(slide_folder) if img.endswith(".png")]
    )
    audio = AudioFileClip(audio_path)
    duration = audio.duration / len(slide_images)

    clips = []
    for img_path in slide_images:
        clip = ImageClip(img_path, duration=duration)
        clip = fadein(clip, 2).fx(fadeout, 2)
        clips.append(clip)

    video = concatenate_videoclips(clips, method="compose")
    final = video.set_audio(audio).set_duration(audio.duration)
    final.write_videofile(output, codec='libx264', audio_codec='aac', fps=24)
    print("✅ Final video created with transitions:", output)


# === Final Main Function ===
def run_metalearn_pipeline(pdf_path="sample.pdf", output_video="static/output/final_video.mp4"):
    clean_previous_outputs()
    pages = extract_text_from_scanned_pdf(pdf_path)
    combined_text = "\n\n".join(pages)

    with open("debug_text.txt", "w", encoding="utf-8") as f:
        f.write(combined_text)

    generate_voice(combined_text)
    create_animated_slides(pages)
    create_video_from_slides(output=output_video)
    print("✅ MetaLearn video generation complete!")
