# Environment and Secrets

## 1. Root `.env.example`

```dotenv
APP_ENV=development
```

## 2. Frontend `.env.local`

```dotenv
# apps/frontend/.env.local
VITE_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

주의:

- `GEMINI_API_KEY`를 frontend env에 넣지 않는다.
- `SUPABASE_SERVICE_ROLE_KEY`를 frontend env에 넣지 않는다.

## 3. Backend `.env`

```dotenv
# apps/backend/.env
APP_ENV=development
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
GEMINI_API_KEY=replace-me
SUPABASE_URL=https://replace-me.supabase.co
SUPABASE_ANON_KEY=replace-me
SUPABASE_SERVICE_ROLE_KEY=replace-me
DATABASE_URL=postgresql://postgres:password@db.host:5432/postgres
```

## 4. Render Environment Variables

Render service에는 다음을 설정한다.

```dotenv
APP_ENV=production
CORS_ORIGINS=https://your-vercel-domain.vercel.app
GEMINI_API_KEY=...
SUPABASE_URL=...
SUPABASE_SERVICE_ROLE_KEY=...
DATABASE_URL=...
```

## 5. Vercel Environment Variables

Vercel project에는 다음만 설정한다.

```dotenv
VITE_API_BASE_URL=https://your-render-service.onrender.com
NEXT_PUBLIC_API_BASE_URL=https://your-render-service.onrender.com
```

## 6. Secret Handling Rule

- secret은 `.env.example`에 실제 값 없이 이름만 남긴다.
- `.env`, `.env.local`은 gitignore에 포함한다.
- CI에서 secret이 필요한 테스트는 mock 기반으로 대체한다.
- Gemini/Supabase 실제 호출 테스트는 manual smoke test로 분리한다.
