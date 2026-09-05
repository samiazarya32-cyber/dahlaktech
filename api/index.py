from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

MAX_IMAGE_BYTES = 12 * 1024 * 1024
MAX_AUDIO_BYTES = 20 * 1024 * 1024
ALLOWED_IMAGE = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_AUDIO = {"audio/wav", "audio/x-wav", "audio/mpeg", "audio/webm", "audio/ogg", "video/webm"}

app = FastAPI(title="Smart Poultry Pro API", version="5.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=False, allow_methods=["GET", "POST"], allow_headers=["*"])

def now():
    return datetime.now(timezone.utc).isoformat()

@dataclass
class AIResult:
    status: str
    condition: str | None
    confidence: float | None
    recommendation: str
    model_name: str
    model_version: str

class PoultryAI:
    model_name = "not-configured"
    model_version = "0"
    @property
    def ready(self):
        return False
    def health(self):
        return {"status": "READY" if self.ready else "MODEL_NOT_CONFIGURED", "model": self.model_name, "version": self.model_version}
    def infer_image(self, _: bytes):
        return AIResult("MODEL_NOT_CONFIGURED", None, None, "A validated poultry vision model has not been installed. The app will not fabricate a diagnosis.", self.model_name, self.model_version)
    def infer_audio(self, _: bytes):
        return AIResult("MODEL_NOT_CONFIGURED", None, None, "A validated poultry acoustic model has not been installed. The app will not fabricate a diagnosis.", self.model_name, self.model_version)

ai = PoultryAI()

@app.get("/api")
def root():
    return {"system":"Smart Poultry Pro","status":"ONLINE","version":"5.0.0","time":now()}

@app.get("/api/health")
def health():
    return {"api":"ok","ai":ai.health(),"storage":"client-side IndexedDB","time":now()}

async def checked(file: UploadFile, allowed: set[str], limit: int):
    if file.content_type not in allowed:
        raise HTTPException(415, "Unsupported media type")
    data = await file.read()
    if not data:
        raise HTTPException(400, "Empty upload")
    if len(data) > limit:
        raise HTTPException(413, "Upload exceeds size limit")
    return data

@app.post("/api/diagnose-vision")
async def diagnose_vision(file: UploadFile = File(...)):
    data = await checked(file, ALLOWED_IMAGE, MAX_IMAGE_BYTES)
    result = ai.infer_image(data)
    return {**asdict(result), "sha256": hashlib.sha256(data).hexdigest(), "timestamp": now()}

@app.post("/api/diagnose-audio")
async def diagnose_audio(file: UploadFile = File(...)):
    data = await checked(file, ALLOWED_AUDIO, MAX_AUDIO_BYTES)
    result = ai.infer_audio(data)
    return {**asdict(result), "sha256": hashlib.sha256(data).hexdigest(), "timestamp": now()}
