# Dockerfile for Duane "the Rock" Reade Pharmacy AI Agent

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app.py .
COPY src/ ./src/
COPY templates/ ./templates/
COPY add_medications.py .

# Copy database initialization script
COPY src/database/init_db.py ./src/database/

# Expose port 5000
EXPOSE 5000

# Set environment variables
ENV FLASK_APP=app.py
ENV PYTHONUNBUFFERED=1

# Create directory for database
RUN mkdir -p /app/data

# Initialize database on container start and run the app
CMD python3 src/database/init_db.py && \
    python3 add_medications.py && \
    python3 app.py --host=0.0.0.0
