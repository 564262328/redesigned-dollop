def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(os.path.dirname(current_dir))
    output_path = os.path.join(root_dir, "index.html")

    print(f"🚀 QUANT Terminal V15.8 啟動...")
    dc = MarketDataCenter()
    
    # 1. 獲取數據並記錄當前所有源的健康狀態
    df, source = dc.get_all_market_data()
    
    # 獲取熔斷器狀態 (自定義邏輯)
    health_status = {}
    now = _time.time()
    for s_name, cooldown_time in dc._circuit_breaker.items():
        if cooldown_time == 0:
            health_status[s_name] = "🟢 正常"
        elif now < cooldown_time:
            health_status[s_name] = f"🔴 熔斷 (剩餘 {int(cooldown_time - now)}s)"
        else:
            health_status[s_name] = "🟡 恢復中"

    if df.empty:
        print("❌ 錯誤：所有數據源已熔斷，無法獲取行情")
        return

    # ... (其餘 AI 分析邏輯保持不變) ...

    # 傳遞 health_status 給 generate_report
    generate_report(ai_results, new_count, total_count, source, dc.get_industry_heatmap(), indices, output_path, health_status)
    print(f"✅ 看板更新成功！數據源: {source}")






















