# Frontend Lapangin

Vue 3 + Vite + Pinia + Vue Router, dibuat dengan `npm create vue@latest` (Router dan Pinia).

```bash
npm install
npm run dev      # http://localhost:5173, request /api diteruskan ke FastAPI
npm run build    # hasil build di dist/
```

Kalau backend tidak jalan di port 8000, salin `.env.example` menjadi `.env.local` lalu ubah
`VITE_API_TARGET`. Panduan lengkap ada di README di folder utama.
