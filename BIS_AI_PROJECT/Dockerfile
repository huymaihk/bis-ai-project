FROM node:22-bookworm-slim AS frontend
WORKDIR /build
COPY frontend/package*.json ./
RUN npm ci --ignore-scripts
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir fastapi uvicorn requests pillow pymupdf beautifulsoup4 streamlit gspread google-auth python-dotenv
COPY bis_api.py persistent_memory.py product_quality.py media_quality.py quality_jobs.py sheets_manager.py ./
COPY deployment/config.py ./config.py
COPY --from=frontend /build/dist ./frontend/dist
RUN mkdir -p Google_Drive_Storage/8_AI_Memory && useradd -m bis && chown -R bis:bis /app
USER bis
EXPOSE 8765
CMD ["uvicorn", "bis_api:create_app", "--factory", "--host", "0.0.0.0", "--port", "8765"]
