from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from deep_translator import GoogleTranslator
import cv2
import numpy as np
import pytesseract
import pandas as pd
from rapidfuzz import process, fuzz
import uuid
from gtts import gTTS
import os

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

df = pd.read_csv("uploads/Medicine_Details.csv").fillna("")
known_medicines = df['product_name'].astype(str).tolist()

def extract_text(image_bytes):
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)

    extracted = ""
    for cnt in contours[:5]:
        x, y, w, h = cv2.boundingRect(cnt)
        roi = img[y:y + h, x:x + w]
        text = pytesseract.image_to_string(roi)
        if len(text.strip()) > 3:
            extracted += text.strip() + "\n"
    return extracted.strip()

def extract_keywords(text):
    import re
    lines = text.split('\n')
    keywords = []
    for line in lines:
        matches = re.findall(r'\b\d+\s*(mg|ml|IU)\b', line, flags=re.IGNORECASE)
        keywords.extend(matches)
        for word in line.split():
            word_clean = word.strip('.,:;()').lower()
            if word_clean not in {"ip", "each", "mg", "ml", "tablet", "capsule", "keep", "out", "reach", "children"}:
                if len(word_clean) >= 4:
                    keywords.append(word_clean)
    return list(set(keywords))

def guess_medicine(text, keywords):
    sub_df = df.copy()
    rows = []
    for _, row in sub_df.iterrows():
        combined = f"{row['product_name']} {row['salt_composition']}".lower()
        if any(k in combined for k in keywords):
            rows.append(row)
    sub_df = pd.DataFrame(rows)
    if sub_df.empty:
        return None, 0
    products = sub_df['product_name'].astype(str).tolist()
    match, score, _ = process.extractOne(text, products, scorer=fuzz.partial_ratio)
    return (match, score) if score >= 60 else (None, score)

@app.post("/process-image")
async def process_image(file: UploadFile = File(...)):
    try:
        image_bytes = await file.read()
        ocr_text = extract_text(image_bytes)
        keywords = extract_keywords(ocr_text)
        match_name, score = guess_medicine(ocr_text, keywords)
        result = {
            "extracted_text": ocr_text,
            "matched_medicine_name": match_name or "Not Found",
            "price": "", "manufacturer": "", "type": "", "composition": "",
            "description": "", "side_effects": "", "drug_interactions": "",
            "match_score": round(score, 2),
            "big_words": keywords
        }

        if match_name:
            row = df[df['product_name'] == match_name].iloc[0]
            for field in ["product_price", "product_manufactured", "sub_category",
                          "salt_composition", "medicine_desc", "side_effects", "drug_interactions"]:
                key = field.replace("product_", "").replace("medicine_", "").replace("salt_", "").replace("desc", "description")
                result[key] = str(row.get(field, "N/A"))

        for key in result:
            if result[key] is None or str(result[key]).lower() == "nan":
                result[key] = ""

        return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.post("/translate-details")
async def translate_details(details_text: str = Form(...), target_lang: str = Form(...)):
    try:
        translated = GoogleTranslator(source='auto', target=target_lang).translate(details_text)
        return JSONResponse(content={"translated_text": translated})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.post("/generate-audio")
async def generate_audio(details_text: str = Form(...), lang: str = Form(...)):
    try:
        filename = f"speech_{uuid.uuid4().hex}.mp3"
        filepath = f"audio/{filename}"
        os.makedirs("audio", exist_ok=True)
        gTTS(text=details_text, lang=lang).save(filepath)
        return JSONResponse(content={"audio_path": f"/get-audio/{filename}"})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.get("/get-audio/{filename}")
async def get_audio(filename: str):
    path = f"audio/{filename}"
    return FileResponse(path, media_type="audio/mpeg")
