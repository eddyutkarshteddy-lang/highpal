from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import requests
from bs4 import BeautifulSoup
import PyPDF2
import io

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/upload_pdf/")
async def upload_pdf(file: UploadFile = File(...)):
    content = await file.read()
    pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() or ""
    return JSONResponse({"text": text})

@app.post("/fetch_url/")
async def fetch_url(url: str = Form(...)):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    text = soup.get_text()
    return JSONResponse({"text": text})

@app.post("/ask_question/")
async def ask_question(text: str = Form(...), question: str = Form(...)):
    # Placeholder for AI Q&A logic
    # You can integrate an LLM or external API here
    answer = f"Pretend answer to '{question}' based on provided text."
    return JSONResponse({"answer": answer})
