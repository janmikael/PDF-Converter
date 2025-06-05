FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libreoffice \
    wkhtmltopdf \
    libmagic1 \
    file \
    fonts-liberation \
    fonts-dejavu \
    fonts-freefont-ttf \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV LIBREOFFICE_PATH=/usr/bin/soffice \
    WKHTMLTOPDF_PATH=/usr/bin/wkhtmltopdf \
    SAL_USE_VCLPLUGIN=headless

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app
WORKDIR /app

EXPOSE 5000
CMD ["python", "run.py"]
