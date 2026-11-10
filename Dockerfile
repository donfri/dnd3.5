FROM python:3.12-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    DND35_SAVE_DIR=/data \
    PIPER_VOICE_DIR=/app/voices \
    PORT=8080

# Piper: free offline neural text-to-speech for the narrator (optional at runtime)
RUN pip install --no-cache-dir "piper-tts>=1.3"

COPY dnd35 ./dnd35
COPY play.py README.md ./

# download the narrator + character voices at build time, then smoke-test them
RUN (python -m dnd35.tts --download && python -m dnd35.tts --say "Build check." && rm -f narrator-test.wav) \
    || echo "WARNING: narrator voices unavailable; players will get browser voices instead"

EXPOSE 8080
CMD ["python", "-m", "dnd35.web", "--host", "0.0.0.0", "--port", "8080"]
