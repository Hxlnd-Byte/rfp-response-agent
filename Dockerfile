# The agent needs only Python. The AI model runs in a separate "ollama" container.
FROM python:3.12-slim
WORKDIR /app
COPY . .
ENV RFP_HOST=0.0.0.0
EXPOSE 8765
CMD ["python", "app.py"]
