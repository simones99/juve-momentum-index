# Used only for local docker-compose parity ("full stack in Docker").
# The actual production deploy uses Vercel, which builds directly from the repo.

FROM node:24-slim AS deps
WORKDIR /app
COPY package.json ./
RUN npm install

FROM node:24-slim AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM node:24-slim AS runner
WORKDIR /app
ENV NODE_ENV=production
RUN useradd --create-home --uid 1000 nextjs
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nextjs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nextjs /app/.next/static ./.next/static
USER nextjs
EXPOSE 3000
CMD ["node", "server.js"]
