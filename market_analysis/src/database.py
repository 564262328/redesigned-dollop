# src/database.py
import json
import os
from src.config import DB_FILE

def load_db():
    """從 JSON 文件加載數據庫，如果不存在則返回默認結構"""
    default_db = {
        "last_update": "NEVER",
        "total_count": 0,
        "stock_list": [],
        "history_logs": []
    }
    
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                # 確保返回的字典包含所有必要的鍵
                for key in default_db:
                    if key not in data:
                        data[key] = default_db[key]
                return data
        except (json.JSONDecodeError, Exception) as e:
            print(f"⚠️ 數據庫讀取失敗: {e}，正在重置...")
            return default_db
    return default_db

def save_db(data):
    """將數據保存到 JSON 文件，壓縮格式以節省空間"""
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            # separators=(',', ':') 可以去除空格，壓縮文件大小
            json.dump(data, f, ensure_ascii=False, separators=(',', ':'))
        print(f"💾 數據庫已更新: {DB_FILE}")
        return True
    except Exception as e:
        print(f"❌ 數據庫保存失敗: {e}")
        return False
