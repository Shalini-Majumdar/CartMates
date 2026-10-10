# Frontend

React 19 + [Vite](https://vite.dev/), talking to the FastAPI backend in `../backend`.

## Getting started

```bash
npm install
npm run dev
```

The dev server runs on <http://localhost:3000>.

## Scripts

| Script | What it does |
| --- | --- |
| `npm run dev` (or `npm start`) | Start the dev server with hot module replacement |
| `npm run build` | Production build into `build/` |
| `npm run preview` | Serve the production build locally |

There is no `test` script: the project has no test files. Add
[Vitest](https://vitest.dev/) when you want one.

## Configuration

The backend origin comes from `VITE_API_URL`, read once in
[`src/api.js`](src/api.js) and defaulted to `http://localhost:8000`.
Copy `.env.example` to `.env.local` to override it:

```bash
cp .env.example .env.local
```

Only variables prefixed with `VITE_` are exposed to the browser bundle.

## Layout

| Path | Purpose |
| --- | --- |
| `index.html` | Vite entry document (project root, not `public/`) |
| `src/main.jsx` | React entry point |
| `src/App.jsx` | Routes; authenticated routes are wrapped in `RequireAuth` |
| `public/` | Static files copied to the build root as-is |
