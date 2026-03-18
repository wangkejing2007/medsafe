# MedSafe Main Application - Build Trigger 2026-03-19
import os
import sys

# 將當前目錄（專案根目錄）加入路徑，以便 import medsafe
# 注意：如果是從根目錄執行 python main.py，需要確保 medsafe 作為包被識別
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

from contextlib import asynccontextmanager
from config import settings
from api.routes import router as api_router
from core.mcp_client import client as mcp_client

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 啟動時：建立 MCP 連線，觸發資料庫背景初始化
    print("Initializing MCP connection...")
    await mcp_client.connect()
    yield
    # 關閉時：切斷連線
    print("Disconnecting MCP...")
    await mcp_client.disconnect()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=settings.APP_DESCRIPTION,
    lifespan=lifespan
)

# CORS 打通
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 掛載 API 路由
app.include_router(api_router, prefix="/api")

@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "MedSafe API is running"}

# 掛載 Web 靜態檔案 (放在路由最後)
root_dir = os.path.dirname(os.path.abspath(__file__))
web_dir = os.path.join(root_dir, "web")
if os.path.exists(web_dir):
    app.mount("/", StaticFiles(directory=web_dir, html=True), name="web")
else:
    print(f"Warning: Web directory not found at {web_dir}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)
