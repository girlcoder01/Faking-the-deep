# Uses Python 3.11 (stable, well-supported) rather than whatever's on your
# laptop -- this avoids the version-fragility issues we hit locally.
FROM python:3.11-slim

# System-level dependencies: ffmpeg for audio extraction (moviepy needs it),
# libglib for OpenCV.
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8080
EXPOSE 8080

CMD streamlit run app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true
