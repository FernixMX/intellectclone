FROM node:22-alpine AS base
RUN corepack enable

# ---------------------------------------------------------------------------
# Etapa 1: instalar dependencias
# ---------------------------------------------------------------------------
FROM base AS deps
WORKDIR /app
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile --ignore-scripts && node node_modules/esbuild/install.js && node node_modules/sharp/install/check.js || true

# ---------------------------------------------------------------------------
# Etapa 2: build
# ---------------------------------------------------------------------------
FROM base AS builder
WORKDIR /app
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN pnpm build

# ---------------------------------------------------------------------------
# Etapa 3: runner (imagen final mínima)
# ---------------------------------------------------------------------------
FROM base AS runner
WORKDIR /app
ENV NODE_ENV=production

RUN addgroup --system --gid 1001 nodejs
RUN adduser  --system --uid 1001 nextjs

COPY --from=builder /app/public              ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next ./.next
COPY --from=deps    /app/node_modules        ./node_modules
COPY --from=builder /app/package.json        ./package.json

USER nextjs
EXPOSE 3000

CMD ["node", "node_modules/next/dist/bin/next", "start"]
