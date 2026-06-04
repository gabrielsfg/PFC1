"""Transcription configuration, read from the agent's .env."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parents[1] / ".env", override=True)

# Groq (default transcription engine)
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "whisper-large-v3-turbo")
# Stay safely under Groq's upload limit (a 24 MB chunk already returned HTTP 413,
# so the effective limit is lower than the documented 25 MB — keep a margin).
GROQ_MAX_FILE_MB = float(os.getenv("GROQ_MAX_FILE_MB", "20"))

# Local faster-whisper fallback (fast preset — quicker than the old medium/beam=5).
LOCAL_WHISPER_MODEL = os.getenv("LOCAL_WHISPER_MODEL", "small")
LOCAL_WHISPER_BEAM_SIZE = int(os.getenv("LOCAL_WHISPER_BEAM_SIZE", "1"))
