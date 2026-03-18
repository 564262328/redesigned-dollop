name: API Diagnostic Test
on: 
  workflow_dispatch: # 允許手動點擊運行

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip' # 開啟緩存加速安裝

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install --prefer-binary akshare pandas requests

      - name: Run Diagnostic (EM/Sina/TX)
        run: python debug_api.py # 執行剛才更新的診斷腳本
