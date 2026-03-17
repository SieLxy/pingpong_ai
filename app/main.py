from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import threading
import logging
import os
import json
import shutil
from app.services.training import Trainer
from app.services.inference import InferenceService
from app.services.dataset import LabelHelper
from app.services.video_processing import extract_features_from_video

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
STATIC_DIR = BASE_DIR / "static"
MODEL_DIR = BASE_DIR / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)
USER_DATA_DIR = BASE_DIR / "data"
USER_DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR = USER_DATA_DIR / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR = ROOT_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE_ENV = os.getenv("LOG_FILE_PATH")
if LOG_FILE_ENV:
    LOG_FILE = Path(LOG_FILE_ENV)
else:
    LOG_FILE = LOG_DIR / "app.log"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

handlers = []
try:
    handlers.append(logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8"))
except Exception:
    fallback = LOG_DIR / "fallback.log"
    handlers.append(logging.FileHandler(fallback, mode="a", encoding="utf-8"))
handlers.append(logging.StreamHandler())

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=handlers,
)
logger = logging.getLogger("pingpong")
logger.info("server starting, log file=%s", LOG_FILE)

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
ADMIN_COOKIE = "admin_auth"
ALLOWED_ORIGINS = ["http://127.0.0.1:8000", "http://localhost:8000"]

app = FastAPI(title="PingPong AI", version="1.4")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

label_helper = LabelHelper(data_dir=ROOT_DIR / "data", model_dir=MODEL_DIR)
trainer = Trainer(data_dir=ROOT_DIR / "data", model_dir=MODEL_DIR, label_helper=label_helper)
infer = InferenceService(model_dir=MODEL_DIR, label_helper=label_helper)

training_state = {"status": "idle", "message": ""}
state_lock = threading.Lock()

def set_state(status: str, message: str):
    with state_lock:
        training_state["status"] = status
        training_state["message"] = message
    logger.info("state=%s msg=%s", status, message)

def ensure_admin(request: Request):
    if request.cookies.get(ADMIN_COOKIE) != "1":
        raise HTTPException(status_code=401, detail="需要管理员登录")

@app.get("/", response_class=HTMLResponse)
async def home():
    return FileResponse(STATIC_DIR / "index.html")

@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    if request.cookies.get(ADMIN_COOKIE) == "1":
        return FileResponse(STATIC_DIR / "admin.html")
    return FileResponse(STATIC_DIR / "admin_login.html", headers={"Cache-Control": "no-store"})

@app.post("/admin/login")
async def admin_login(password: str = Form(...)):
    if password != ADMIN_PASSWORD:
        logger.warning("admin login failed")
        raise HTTPException(status_code=401, detail="管理员密码错误")
    resp = JSONResponse({"message": "登录成功"})
    resp.set_cookie(
        key=ADMIN_COOKIE,
        value="1",
        httponly=False,
        samesite="lax",
        max_age=3600,
        path="/",
    )
    logger.info("admin login success")
    return resp

@app.get("/labels")
async def labels():
    return {"labels": label_helper.id_to_name_list()}

@app.post("/train")
async def train(request: Request):
    ensure_admin(request)
    set_state("running", "训练中...")
    try:
        info = trainer.train()
        infer.reload()
        set_state("done", f"训练完成，样本 {info['samples']}，类别 {info['classes']}")
        return {"message": "训练完成", "info": info}
    except Exception as exc:
        set_state("error", str(exc))
        logger.exception("train failed")
        raise HTTPException(status_code=400, detail=str(exc))

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    tmp_path = USER_DATA_DIR / file.filename
    with open(tmp_path, "wb") as f:
        f.write(await file.read())
    logger.info("predict upload=%s", file.filename)
    try:
        features, stats = extract_features_from_video(str(tmp_path))
        result = infer.predict(features, stats)
        return result
    finally:
        tmp_path.unlink(missing_ok=True)

@app.post("/annotate")
async def annotate(
    request: Request,
    label_id: int = Form(...),
    file: UploadFile = File(...),
):
    ensure_admin(request)
    tmp_path = USER_DATA_DIR / file.filename
    with open(tmp_path, "wb") as f:
        f.write(await file.read())
    # 保存长期副本
    dest = UPLOADS_DIR / file.filename
    shutil.copy2(tmp_path, dest)
    logger.info("annotate upload=%s label=%s saved=%s", file.filename, label_id, dest)
    set_state("running", "提取特征...")
    try:
        features, stats = extract_features_from_video(str(tmp_path))
        record = trainer.save_user_annotation(features, label_id, file.filename)
        set_state("running", "训练中...")
        info = trainer.train()
        infer.reload()
        set_state("done", f"训练完成，样本 {info['samples']}，类别 {info['classes']}")
        return {"message": "已保存并完成训练", "record": record, "saved_video": str(dest)}
    except Exception as exc:
        set_state("error", str(exc))
        logger.exception("annotate/train failed")
        raise HTTPException(status_code=400, detail=str(exc))
    finally:
        tmp_path.unlink(missing_ok=True)

@app.get("/train_status")
async def train_status(request: Request):
    ensure_admin(request)
    with state_lock:
        return dict(training_state)

@app.get("/health")
async def health():
    return {"status": "ok"}
