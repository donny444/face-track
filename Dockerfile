# syntax=docker/dockerfile:1.7
#
# FaceTrack Next.js (web) image.
#
# Multi-stage build on node:20-alpine:
#   * deps    - resolves node_modules from package-lock.json via `npm ci`.
#   * builder - runs `next build` to produce .next/.
#   * runtime - copies the built app + production node_modules and runs
#               `next start` on port 3000 as a non-root user.
#
# IMPORTANT: NEXT_PUBLIC_* environment variables are inlined into the
# client bundle at BUILD TIME. NEXT_PUBLIC_SERVER_URL must therefore be
# supplied as a docker build --build-arg (also wired in docker-compose.yml).
# Changing it after the image is built has no effect on the client.
#
# The Next.js source imports SERVER_URL from src/data/global_variables.ts,
# which is gitignored. If it does not exist in the build context, we stub
# it here so it reads NEXT_PUBLIC_SERVER_URL at build time.

ARG NEXT_PUBLIC_SERVER_URL=http://localhost/api

# ---------- deps stage ----------
FROM node:20-alpine AS deps
WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund

# ---------- builder stage ----------
FROM node:20-alpine AS builder
WORKDIR /app

ARG NEXT_PUBLIC_SERVER_URL
ENV NEXT_PUBLIC_SERVER_URL=${NEXT_PUBLIC_SERVER_URL} \
    NEXT_TELEMETRY_DISABLED=1

COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Stub the gitignored client-side global if the host did not supply one,
# so SERVER_URL resolves to the build-time NEXT_PUBLIC_SERVER_URL value.
RUN mkdir -p src/data && \
    if [ ! -f src/data/global_variables.ts ]; then \
      printf "export const SERVER_URL = process.env.NEXT_PUBLIC_SERVER_URL || %s;\n" \
        "'${NEXT_PUBLIC_SERVER_URL}'" > src/data/global_variables.ts ; \
    fi

RUN npm run build

# ---------- runtime stage ----------
FROM node:20-alpine AS runtime
WORKDIR /app

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    HOSTNAME=0.0.0.0

RUN addgroup --system --gid 1001 nodejs \
 && adduser  --system --uid 1001 --ingroup nodejs nextjs

COPY --from=builder --chown=nextjs:nodejs /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next ./.next
COPY --from=builder --chown=nextjs:nodejs /app/node_modules ./node_modules
COPY --from=builder --chown=nextjs:nodejs /app/package.json ./package.json
COPY --from=builder --chown=nextjs:nodejs /app/next.config.mjs ./next.config.mjs

USER nextjs

EXPOSE 3000

CMD ["npm", "run", "start", "--", "-p", "3000", "-H", "0.0.0.0"]
