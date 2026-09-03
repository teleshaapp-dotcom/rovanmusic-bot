
FROM python:3.10-slim

WORKDIR /app

# دامەزراندنی FFmpeg
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# کۆپی کردنی فایلەکان
COPY requirements.txt .
COPY main.py .

# دامەزراندنی پەرەپێدانەکان (بەبێ cache)
RUN pip install --no-cache-dir -r requirements.txt

# دەستپێکردن
CMD ["python", "main.py"]
