# 1. 基礎映像檔 (使用與 .devcontainer 相同的 Python 3.12 環境)
FROM mcr.microsoft.com/devcontainers/python:3.12

# 2. 設定在容器內的工作目錄
WORKDIR /app

# 3. 複製並安裝依賴 (這一步會被快取，加速後續建置)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. 複製所有應用程式碼 (會被 .dockerignore 過濾)
COPY . .

# 5. 預設執行命令
#    -u 參數是為了讓 print() 的日誌能即時顯示在 docker logs 中
CMD ["python", "-u", "app.py"]
