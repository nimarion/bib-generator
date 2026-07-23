# Use official, lightweight Python 3.12 slim image
FROM python:3.12-slim

# Set environment variables for optimized execution
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies (e.g., git or build-essential if needed, slim is basic)
# For standard Pillow/pandas, standard pip packages have pre-built wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file first to leverage Docker layer caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the core backend application files
COPY main.py bib.py server.py utils.py ./
COPY header/ ./header/
COPY footer/ ./footer/
COPY example/ ./example/

# Expose port 8080 to permit inbound network connections
EXPOSE 8080

# Default entry point to run the Kiosk Server dynamically on container boot
CMD ["python", "main.py", "--server", "--port", "8080", "--host", "0.0.0.0"]
