# Use Python 3.11 base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code
COPY . .

# Expose the port your app runs on (adjust if different)
EXPOSE 5000

# Start your app (update this if different)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000"]

