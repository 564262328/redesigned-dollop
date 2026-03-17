def build_dashboard(now_str, db, df_a, new_count):
    # Simplified version of the Cyberpunk UI
    stocks_html = ""
    if not df_a.empty:
        top_12 = df_a.sort_values(by="涨跌幅", ascending=False).head(12)
        for _, r in top_12.iterrows():
            stocks_html += f"<div class='p-4 bg-slate-900 border border-white/5 rounded-xl'>\
                <div class='text-white font-bold'>{r['名称']}</div>\
                <div class='text-emerald-400 font-mono'>{r['最新价']} (+{r['涨跌幅']}%)</div></div>"

    html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8"><script src="https://cdn.tailwindcss.com"></script>
    <style>body {{ background: #020617; color: #f8fafc; font-style: italic; text-transform: uppercase; }}</style>
</head>
<body class="p-8">
    <div class="max-w-5xl mx-auto">
        <header class="flex justify-between border-b border-white/10 pb-6 mb-8">
            <h1 class="text-2xl font-black text-blue-400 tracking-tighter">QUANT TERMINAL v14.0</h1>
            <div class="text-xs text-slate-500 font-mono">{now_str}</div>
        </header>
        <div class="grid grid-cols-2 gap-8 mb-12">
            <div class="p-6 bg-blue-500/5 border border-blue-500/20 rounded-2xl text-center">
                <div class="text-3xl font-black">{db['total_count']}</div><div class="text-[10px] text-slate-500">TOTAL STOCKS</div>
            </div>
            <div class="p-6 bg-emerald-500/5 border border-emerald-500/20 rounded-2xl text-center">
                <div class="text-3xl font-black text-emerald-400">+{new_count}</div><div class="text-[10px] text-slate-500">NEW TODAY</div>
            </div>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">{stocks_html}</div>
    </div>
</body>
</html>"""
    with open("index.html", "w", encoding="utf-8") as f: f.write(html)

