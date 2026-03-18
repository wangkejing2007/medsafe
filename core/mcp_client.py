import asyncio
import json
import os
from typing import List, Dict, Any, Optional
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class MedSafeMCPClient:
    """
    藥安心 MCP Client 模組（持久連線優化版）
    負責與 Taiwan-Health-MCP 伺服器通訊，保持連線以支援背景初始化
    """
    def __init__(self, server_script_path: str):
        # 設定環境變數，包含 PYTHONPATH 以確保 MCP 伺服器能 import 自己的模組
        server_dir = os.path.dirname(server_script_path)
        env = os.environ.copy()
        # 加入 src 目錄到路徑中
        if "PYTHONPATH" in env:
            env["PYTHONPATH"] = f"{server_dir};{env['PYTHONPATH']}"
        else:
            env["PYTHONPATH"] = server_dir

        self.server_params = StdioServerParameters(
            command="python",
            args=[server_script_path],
            env=env
        )
        self.session: Optional[ClientSession] = None
        self._exit_stack = None

    async def connect(self):
        """建立持久的 MCP 伺服器連線"""
        if self.session:
            return
        
        try:
            from contextlib import AsyncExitStack
            self._exit_stack = AsyncExitStack()
            
            # 建立 stdio client 並進入 context
            read, write = await self._exit_stack.enter_async_context(stdio_client(self.server_params))
            # 建立 session 並進入 context
            self.session = await self._exit_stack.enter_async_context(ClientSession(read, write))
            
            # 初始化 session
            await self.session.initialize()
            print("Successfully connected to Taiwan-Health-MCP server.")
        except Exception as e:
            print(f"Failed to connect to MCP Server: {e}")
            self.session = None

    async def disconnect(self):
        """關閉連線"""
        if self._exit_stack:
            await self._exit_stack.aclose()
            self.session = None
            self._exit_stack = None

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """執行 MCP 工具 (使用現有 Session)"""
        if not self.session:
            await self.connect()
        
        if not self.session:
            raise Exception("MCP Session is not available")
            
        return await self.session.call_tool(tool_name, arguments)

    async def search_tfda_drug(self, drug_name: str):
        """查詢台灣 FDA 藥品詳情"""
        return await self.call_tool("search_drug_info", {"keyword": drug_name})

    async def check_health_food_conflict(self, medications: List[str], health_foods: List[str]):
        """檢查藥物與健康食品衝突"""
        results = []
        # 將藥物清單轉為逗號分隔字串，傳遞給 MCP 伺服器進行分析
        meds_str = ",".join(medications)
        for hf in health_foods:
            try:
                res = await self.call_tool("search_health_food", {
                    "keyword": hf,
                    "medications": meds_str
                })
                results.append(res)
            except Exception as e:
                print(f"Error calling search_health_food for {hf}: {e}")
        return results


# 使用專案內部的相對路徑連接至 MCP 伺服器
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
mcp_server_path = os.path.join(project_root, "mcp_server", "src", "server.py")
client = MedSafeMCPClient(mcp_server_path)
