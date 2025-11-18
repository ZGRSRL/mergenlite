FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy application code (root directory'den)
COPY app.py /app/app.py
COPY mergenlite_app.py /app/mergenlite_app.py
COPY mergen/mergenlite_unified.py /app/mergenlite_unified.py
COPY guided_analysis.py /app/guided_analysis.py
COPY theme.css /app/theme.css
COPY theme_loader.py /app/theme_loader.py
COPY mergenlite_ui_components.py /app/mergenlite_ui_components.py
COPY sam_integration.py /app/sam_integration.py
COPY gsa_opportunities_client.py /app/gsa_opportunities_client.py
COPY document_processor.py /app/document_processor.py
COPY rag_service.py /app/rag_service.py
COPY llm_analyzer.py /app/llm_analyzer.py
# Copy .env file if it exists (for API key loading)
# Note: Docker Compose env_file already loads env vars, but we also copy .env for direct file access
COPY mergen/.env /app/mergen/.env

# Streamlit configuration
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

EXPOSE 8501

# Run Streamlit (app.py veya mergenlite_app.py)
CMD ["streamlit", "run", "app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]

