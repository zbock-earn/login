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
├── requirements-ml.txt
├── requirements-deepfilter.txt
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
│   │   ├── local_jobs.py
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
  ├─ Default local background job   -> in-process worker thread
  ├─ Listen to progress            -> WebSocket /ws/jobs/{job_id}
  └─ Stream generated audio        -> FastAPI /api/audio/{audio_id}/stream

FastAPI API Process
  ├─ Validates user input
  ├─ Stores voice references and metadata
  ├─ Enqueues local demo jobs or Celery jobs in Redis
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

### 1. Create an isolated Python environment

Use a virtual environment. Do not install into a global Python that already has Gradio, DeepFilterNet, or other AI tools installed, because pip may downgrade unrelated packages.

**Windows CMD:**

```bat
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
copy .env.example .env
```

**Linux/macOS:**

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
```

The base requirements do not force a NumPy downgrade and do not install Torch, so a global environment with Kokoro or other TTS tools is less likely to be disrupted. The included demo engine can create placeholder WAV output without downloading a 200 MB+ Torch wheel. Install `requirements-ml.txt` only for real StyleTTS2 integration, and use `requirements-deepfilter.txt` in a dedicated environment when enabling DeepFilterNet 0.5.x because that add-on expects NumPy 1.x.

### 2. Start Redis

The app now works without Redis by default using `BACKGROUND_BACKEND=local`, so pressing **Generate studio voice** immediately creates a demo WAV file with the placeholder TTS engine. Use Redis when you want production-style Celery workers. On Windows, the easiest Redis option is Docker Desktop:

```bat
docker run --name voice-redis -p 6379:6379 -d redis:7
```

For production-style async workers, set `BACKGROUND_BACKEND=celery` in `.env`, keep `REDIS_URL=redis://localhost:6379/0`, and start the Celery worker below. If Redis is unavailable while `BACKGROUND_BACKEND=celery`, the API falls back to the local in-process runner so the UI still generates audio.

### 3. Start the FastAPI web server

Run this from the repository root:

```bat
python -m uvicorn app.main:app --reload
```

Then open `http://127.0.0.1:8000`.

You can also run the script directly. Both of these work after this fix:

```bat
python app\main.py
cd app && python main.py
```

### 4. Optional: start the Celery worker

Skip this section for the default local demo mode. For production-style Celery mode, set `BACKGROUND_BACKEND=celery` in `.env`, open a second terminal, activate the same virtual environment, and run the worker from the repository root.

**Windows CMD:**

```bat
.venv\Scripts\activate
celery -A app.tasks.celery_app.celery_app worker --loglevel=info --pool=solo --concurrency=1
```

**Linux/macOS:**

```bash
source .venv/bin/activate
celery -A app.tasks.celery_app.celery_app worker --loglevel=info --concurrency=1
```

The Windows command uses `--pool=solo` because Celery's default prefork pool is not reliable on native Windows.

### Troubleshooting

- If the page loads but Generate does nothing, check `/api/jobs/{job_id}` in the browser developer network tab. The default `BACKGROUND_BACKEND=local` should not require Redis.
- If you see Redis retry logs, either start Redis or change `.env` back to `BACKGROUND_BACKEND=local`, then restart Uvicorn.
- Use a fresh virtual environment. Installing every AI tool into one global Python can still create conflicts, such as Kokoro requiring NumPy 2.x while DeepFilterNet 0.5.x expects NumPy 1.x. The base demo no longer installs Torch or DeepFilterNet-specific pins; install `requirements-ml.txt` and `requirements-deepfilter.txt` only when you are ready to wire those engines.

## Production Notes

- Put Nginx or Caddy in front of FastAPI for TLS, static caching, and large upload limits.
- Use a process manager such as systemd, Supervisor, Docker Compose, or Kubernetes.
- Store audio artifacts in S3-compatible object storage once traffic grows.
- Add authentication, subscription quotas, and per-user storage isolation before public launch.
- Use Redis persistence only for job metadata; generated audio should live in durable storage.
