# src/html_generator.py
def build_dashboard(now_str, db, stocks_data, sector_data):
    """负责生成你要求的那个暗黑科技风 HTML"""
    html_template = f"""
    <!DOCTYPE html>... (这里粘贴之前发给你的暗黑风 HTML 代码) ...
    """
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_template)
