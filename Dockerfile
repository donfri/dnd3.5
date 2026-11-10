FROM python:3.12-slim
WORKDIR /app
COPY dnd35 ./dnd35
COPY play.py README.md ./
ENV PYTHONUNBUFFERED=1 \
    DND35_SAVE_DIR=/data \
    PORT=8080
EXPOSE 8080
CMD ["python", "-m", "dnd35.web", "--host", "0.0.0.0", "--port", "8080"]
