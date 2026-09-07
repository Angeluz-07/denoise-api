FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y ffmpeg git && \
    apt-get clean

# Install PyTorch CPU version
RUN pip install --no-cache-dir -v "torch==2.8.0" "torchaudio==2.8.0" --index-url https://download.pytorch.org/whl/cpu

# Install cargo && c++ compilers for deepfilternet
RUN apt-get install -y cargo build-essential

# Install deepfilter net
RUN pip install --no-cache-dir deepfilternet

# Install requirements
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose gradio port
EXPOSE 7860 

CMD ["sh", "-c", "gradio process_record_ui.py"]
