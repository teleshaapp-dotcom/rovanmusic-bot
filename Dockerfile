# بەکارهێنانی وەشانی فەرمی پایتۆن
FROM python:3.10-slim

# دیاریکردنی شوێنی کارکردن لە ناو سێرڤەرەکەدا
WORKDIR /app

# گواستنەوەی فایلەکان بۆ ناو سێرڤەرەکە
COPY . /app

# دامەزراندنی پێداویستییەکان
RUN pip install --no-cache-dir -r requirements.txt

# کارپێکردنی فایلی سەرەکی
CMD ["python", "main.py"]
