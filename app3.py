from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from deep_translator import GoogleTranslator
from fpdf import FPDF
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
from gtts import gTTS
import cv2
import numpy as np
import pytesseract
import pandas as pd
from rapidfuzz import process, fuzz
import os
import uuid

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

df = pd.read_csv("uploads/Medicine_Details.csv").fillna("")
known_meds = df['product_name'].astype(str).tolist()

def extract_text(image_bytes):
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                   cv2.THRESH_BINARY, 15, 10)
    return pytesseract.image_to_string(thresh)

def find_medicines(text):
    words = [w.strip(".,:;()").lower() for w in text.split()]
    found = set()
    for word in words:
        match, score, _ = process.extractOne(word, known_meds, scorer=fuzz.partial_ratio)
        if score >= 80:
            found.add(match)
    return list(found)

def fetch_details(meds):
    result = []
    for med in meds:
        row = df[df["product_name"] == med]
        if not row.empty:
            row = row.iloc[0]
            result.append({
                "name": med,
                "usage": row.get("medicine_desc", ""),
                "dosage": row.get("product_dosage", ""),
                "side_effects": row.get("side_effects", ""),
                "warnings": row.get("warnings", ""),
            })
    return result

def detect_interactions(meds):
    return ["Avoid combining Paracetamol and Ibuprofen without prescription."] if "Paracetamol" in meds and "Ibuprofen" in meds else []

def validate_dosage(text):
    import re
    dosage_mentions = re.findall(r"\b\d{2,4}\s*mg\b", text.lower())
    flagged = [d for d in dosage_mentions if int(d.split()[0]) > 1000]
    return {"flagged": flagged, "valid": len(flagged) == 0}

def create_pdf_report(text, meds, interaction_notes, validation, filename):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, f"Extracted Text:\n{text}\n\n")
    pdf.multi_cell(0, 10, f"Detected Medicines:\n{', '.join(meds)}\n\n")
    pdf.multi_cell(0, 10, "Interaction Warnings:\n" + "\n".join(interaction_notes) + "\n\n")
    pdf.multi_cell(0, 10, "Dosage Validation:\n" +
                   ("Valid" if validation["valid"] else f"Issues: {', '.join(validation['flagged'])}") + "\n\n")
    pdf.output(filename)

def summarize_text(text, max_chars=4000):
    if len(text) <= max_chars:
        return text
    parser = PlaintextParser.from_string(text, Tokenizer("english"))
    summarizer = LsaSummarizer()
    summary = summarizer(parser.document, 30)  # 30 sentences (adjust as needed)
    summarized_text = " ".join(str(sentence) for sentence in summary)
    return summarized_text[:max_chars]

@app.post("/analyze-prescription")
async def analyze_prescription(file: UploadFile = File(...)):
    try:
        image_bytes = await file.read()
        text = extract_text(image_bytes)
        meds = find_medicines(text)
        details = fetch_details(meds)
        interactions = detect_interactions(meds)
        validation = validate_dosage(text)
        pdf_name = f"prescription_{uuid.uuid4().hex}.pdf"
        pdf_path = os.path.join("pdfs", pdf_name)
        os.makedirs("pdfs", exist_ok=True)
        create_pdf_report(text, meds, interactions, validation, pdf_path)

        return JSONResponse({
            "extracted_text": text,
            "medicines": details,
            "interactions": interactions,
            "dosage_check": validation,
            "pdf_path": f"/get-report/{pdf_name}"
        })

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.post("/translate-prescription")
async def translate_prescription(details_text: str = Form(...), target_lang: str = Form(...)):
    try:
        summarized = summarize_text(details_text, max_chars=4000)
        translated = GoogleTranslator(source='auto', target=target_lang).translate(summarized)
        return JSONResponse(content={"translated_text": translated})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.get("/get-report/{filename}")
async def get_report(filename: str):
    path = f"pdfs/{filename}"
    return FileResponse(path, media_type="application/pdf")

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
