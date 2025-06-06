# 🧾 PDF Converter Web App

A Python Flask-based web application that converts documents to PDF using **LibreOffice** and **wkhtmltopdf**. Built for simplicity, scalability, and containerized using Docker.

---

## 🚀 Features

- ✅ Convert `.docx`, `.xlsx`, `.txt`, `.html`, and other supported formats to PDF
- 🧩 Dual-engine conversion:
  - **LibreOffice** for Office documents
  - **wkhtmltopdf** for HTML/text content
- 🔐 Session-based web interface (optional login)
- 📦 Dockerized for easy deployment
- 📝 Logging and error handling for production use

---

## 🛠️ Tech Stack

- **Backend**: Python, Flask
- **Conversion Tools**: LibreOffice, wkhtmltopdf
- **Containerization**: Docker

---

## 📦 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/pdf-converter-app.git
cd pdf-converter-app
```

### 2. Build the Docker Image

```bash
docker build -t pdf-converter .
```

### 3. Run the Docker Container

```bash
docker run -p 5000:5000 pdf-converter
```

Visit `http://localhost:5000` in your browser.

---

## 📁 Project Structure

```
pdf-converter-app/
├── run.py
├── requirements.txt
├── Dockerfile
├── templates/
│   └── index.html
├── static/
│   └── (css/js/images if any)
└── utils/
    └── conversion.py  # Handles LibreOffice and wkhtmltopdf logic
```

---

## 🔍 Example Usage

- Upload a `.docx`, `.txt`, or `.html` file via the UI
- Click **Convert**
- App returns a downloadable PDF version

---

## 🐳 Docker Overview

**Dockerfile** installs LibreOffice and wkhtmltopdf, exposes port 5000, and runs Flask.

```dockerfile
FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    libreoffice \
    wkhtmltopdf \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "run.py"]
```

---

## ☁️ Deployment

This app can be deployed to:

- [Render](https://render.com) – Docker support, no credit card required

---

## 🧠 Credits

Created by [Michael (JMDev)](https://github.com/your-username)  
LibreOffice and wkhtmltopdf are open-source tools used under respective licenses.

---

## 📜 License

This project is licensed under the [MIT License](LICENSE).
