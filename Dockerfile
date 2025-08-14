FROM python:3.10-slim-bookworm

# Set Chrome for Testing version and architecture
ENV CHROME_VERSION=125.0.6422.141
ENV ARCH=linux64

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    unzip \
    fonts-liberation \
    libnss3 \
    libxss1 \
    libappindicator3-1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    libglib2.0-0 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libdbus-glib-1-2 \
    ca-certificates \
    libu2f-udev \
    libvulkan1 \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Install Chrome
RUN wget -O /tmp/chrome-${ARCH}.zip "https://storage.googleapis.com/chrome-for-testing-public/${CHROME_VERSION}/${ARCH}/chrome-${ARCH}.zip" && \
    unzip /tmp/chrome-${ARCH}.zip -d /opt && \
    mv /opt/chrome-${ARCH} /opt/chrome && \
    ln -s /opt/chrome/chrome /usr/bin/google-chrome && \
    rm /tmp/chrome-${ARCH}.zip

# Install ChromeDriver
RUN wget -O /tmp/chromedriver-${ARCH}.zip "https://storage.googleapis.com/chrome-for-testing-public/${CHROME_VERSION}/${ARCH}/chromedriver-${ARCH}.zip" && \
    unzip /tmp/chromedriver-${ARCH}.zip -d /opt && \
    mv /opt/chromedriver-${ARCH}/chromedriver /usr/local/bin/chromedriver && \
    chmod +x /usr/local/bin/chromedriver && \
    rm -rf /tmp/chromedriver-${ARCH}.zip /opt/chromedriver-${ARCH}

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . /app
WORKDIR /app

# Set default download directory
ENV DOWNLOAD_DIR=/app/downloads

# Create download directory
RUN mkdir -p /app/downloads

# Run the main Python script
CMD ["python", "main.py"]