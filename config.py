"""
藥安心 MedSafe — 系統設定
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """應用程式全域設定"""

    # === 應用程式 ===
    APP_NAME: str = "藥安心 MedSafe"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "AI 多重用藥安全守護系統"
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"

    # === API 伺服器 ===
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = 8001

    # === 外部 API ===
    OPENFDA_BASE_URL: str = "https://api.fda.gov/drug"
    CHEMBL_BASE_URL: str = "https://www.ebi.ac.uk/chembl/api/data"
    OPENFDA_API_KEY: str = os.getenv("OPENFDA_API_KEY", "")

    # === LINE Bot ===
    LINE_CHANNEL_SECRET: str = os.getenv("LINE_CHANNEL_SECRET", "")
    LINE_CHANNEL_ACCESS_TOKEN: str = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")

    # === 風險分級閾值 ===
    RISK_GREEN_MAX: int = 30      # 🟢 綠燈上限
    RISK_YELLOW_MAX: int = 60     # 🟡 黃燈上限
    # 超過 RISK_YELLOW_MAX 即為 🔴 紅燈

    # === 免責聲明 ===
    DISCLAIMER: str = (
        "⚠️ 免責聲明：本系統提供之分析結果僅供參考，不構成醫療建議。"
        "使用者如有任何用藥疑慮，應諮詢專業醫師或藥師。"
    )


settings = Settings()
