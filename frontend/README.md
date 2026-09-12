# Pixel Repair Shop frontend

This is a dependency-free vanilla HTML/CSS/JavaScript frontend for the current FastAPI backend.

## Run locally

Start the backend from the repository root:

```bash
uvicorn app.main:app --reload
```

Then serve this directory with any static file server, for example:

```bash
python -m http.server 5500 --directory frontend
```

Open <http://localhost:5500>.

The frontend defaults to `http://localhost:8000/api`. To point it at another backend, define `window.PIXEL_BOT_API_URL` before loading `app.js`.
