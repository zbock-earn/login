# AI Voice Generation SaaS Blueprint

A production-ready scaffold for a high-performance AI Voice Generation SaaS platform powered by StyleTTS 2, asynchronous FastAPI/Celery workers, Redis queues, and DeepFilterNet post-processing.

## Goals

- **Natural cinematic narration** with StyleTTS 2 as the core TTS engine.
- **Zero-shot voice cloning** through uploaded reference audio.
- **Emotion controls** for `deep`, `whisper`, `dramatic`, and `neutral` delivery styles.
- **Real-time user experience** through WebSocket progress events and chunked audio streaming endpoints.
- **CPU-first deployment** using memory-mapped model assets, constrained thread pools, batching, and worker isolation.
- **Studio-grade polishing** with DeepFilterNet noise reduction as an automated post-processing stage.

## Repository Layout

```text
.
├── README.md
├── requirements.txt
├── .env.example
├── app
│   ├── __init__.py
│   ├── main.py
│   ├── core
│   │   ├── __init__.py
│   │   ├── config.py
│   │   └── logging.py
│   ├── models
│   │   ├── __init__.py
│   │   └── schemas.py
│   ├── services
│   │   ├── __init__.py
│   │   ├── audio_library.py
│   │   ├── postprocess.py
│   │   ├── streaming.py
│   │   └── tts_engine.py
│   ├── tasks
│   │   ├── __init__.py
│   │   ├── celery_app.py
│   │   └── generation.py
│   └── web
│       ├── __init__.py
│       ├── routes.py
│       └── templates
│           └── index.html
└── storage
    ├── generated
    │   └── .gitkeep
    └── voices
        └── .gitkeep
```

## Architecture

```text
Browser UI
  ├─ Upload reference voice        -> FastAPI /api/voices
  ├─ Submit generation request     -> FastAPI /api/generate
  ├─ Listen to progress            -> WebSocket /ws/jobs/{job_id}
  └─ Stream generated audio        -> FastAPI /api/audio/{audio_id}/stream

FastAPI API Process
  ├─ Validates user input
  ├─ Stores voice references and metadata
  ├─ Enqueues Celery jobs in Redis
  └─ Serves responsive HTML/Tailwind UI

Celery Worker Process
  ├─ Loads StyleTTS 2 once per worker process
  ├─ Runs CPU inference with tuned thread limits
  ├─ Applies emotion and stability controls
  ├─ Runs DeepFilterNet denoising/polishing
  └─ Saves audio artifacts for the library manager

Redis
  ├─ Celery broker/result backend
  └─ Lightweight progress/cache channel
```

## CPU-First Performance Blueprint

Target hardware can be CPU-only, including older 4-core processors, if the platform is configured for bounded concurrency instead of raw parallelism.

1. **One model load per worker process**
   - Keep StyleTTS 2 in a process-global singleton.
   - Do not reload weights per HTTP request.
   - Use `--concurrency=1` or `--concurrency=2` depending on RAM and CPU contention.

2. **Thread control**
   - Set `OMP_NUM_THREADS`, `MKL_NUM_THREADS`, and `TORCH_NUM_THREADS` to the physical core count or lower.
   - On 4-core CPUs, start with `4` for one worker or `2` for two workers.

3. **Memory mapping and lazy assets**
   - Keep model directories outside the app image, for example `D:\Models Library\StyleTTS2` on Windows or `/models/styletts2` on Linux.
   - Load large checkpoints with memory-mapped reads where supported by the model loader.
   - Store generated WAV/MP3 files on disk or object storage instead of keeping byte arrays in Redis.

4. **Chunked long-form generation**
   - Split text into sentence-aware chunks of 8-15 seconds.
   - Batch compatible chunks to amortize model overhead.
   - Crossfade chunk boundaries to hide discontinuities.
   - Stream completed chunks to the user while the rest of the job continues.

5. **1-minute audio under 3 minutes on CPU**
   - Use pre-warmed workers and cached speaker embeddings.
   - Keep reference embedding extraction separate from synthesis and cache it by voice ID.
   - Run DeepFilterNet after chunk stitching, not per tiny chunk, unless streaming polish is required.
   - Use WAV during processing and encode compressed formats asynchronously after first playback is available.

## Local Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

In another terminal:

```bash
celery -A app.tasks.celery_app.celery_app worker --loglevel=info --concurrency=1
```

## Production Notes

- Put Nginx or Caddy in front of FastAPI for TLS, static caching, and large upload limits.
- Use a process manager such as systemd, Supervisor, Docker Compose, or Kubernetes.
- Store audio artifacts in S3-compatible object storage once traffic grows.
- Add authentication, subscription quotas, and per-user storage isolation before public launch.
- Use Redis persistence only for job metadata; generated audio should live in durable storage.
