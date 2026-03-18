def main():
    # ... 前面的路徑與數據獲取邏輯 ...
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(os.path.dirname(current_dir))
    output_path = os.path.join(root_dir, "index.html")

    print(f"🚀 QUANT Terminal V15.8 啟動...")
    dc = MarketDataCenter()
    
    # 1. 獲取數據與當前熔斷狀態
    df, source = dc.get_all_market_data()
    
    # 構造熔斷器健康狀態字典 (供 HTML 渲染)
    health_status = {}
    now = _time.time()
    for s_name, cooldown_time in dc._circuit_breaker.items():
        if cooldown_time == 0:
            health_status[s_name] = "🟢 正常"
        elif now < cooldown_time:
            health_status[s_name] = f"🔴 熔斷 ({int(cooldown_time - now)}s)"
        else:
            health_status[s_name] = "🟡 恢復中"

    if df.empty:
        print("❌ 嚴重錯誤：無法獲取行情數據，程序終止。")
        return

    # 2. 獲取大盤與行業輔助數據
    indices = dc.get_market_indices()
    industry_data = dc.get_industry_heatmap()
    new_count, total_count = dc.sync_and_get_new(df)
    
    # 3. 挑選標的並進行 AI 分析 (核心 30 檔或熱門股)
    hot_df = df.sort_values(by='change', ascending=False).head(15) 
    ai_results = []
    
    for _, row in hot_df.iterrows():
        code = str(row['code'])
        chip = dc.get_chip_data(code)
        combined_info = {**row.to_dict(), **chip}
        
        # 呼叫 AI 分析
        analysis = get_ai_analysis(row['name'], str(combined_info), str(indices))
        if not analysis:
            analysis = {"insights": "數據源波動，建議關注支撐位。", "buy_point": "觀望", "stop_loss": "前低"}
        
        analysis.update(combined_info)
        ai_results.append(analysis)

    # 4. 【關鍵】按照 html_generator.py 的參數順序調用
    generate_report(
        ai_results,      # 1. AI 結果
        new_count,       # 2. 新股數
        total_count,     # 3. 總掃描數
        source,          # 4. 當前數據源
        industry_data,   # 5. 行業熱力圖
        indices,         # 6. 指數數據
        output_path,     # 7. 輸出路徑
        health_status    # 8. 熔斷狀態 (新增)
    )
    
    print(f"✅ 報告更新成功！路徑: {output_path}")























