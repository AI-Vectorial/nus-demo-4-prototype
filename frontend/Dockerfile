FROM node:22-alpine AS deps
WORKDIR /srv
COPY package.json package-lock.json* ./
RUN npm ci --omit=dev || npm install --omit=dev

FROM node:22-alpine AS builder
WORKDIR /srv
COPY package.json package-lock.json* ./
RUN npm ci || npm install
COPY . .
RUN npm run build

FROM node:22-alpine AS runner
WORKDIR /srv
ENV NODE_ENV=production
COPY --from=builder /srv/.next/standalone ./
COPY --from=builder /srv/.next/static ./.next/static
COPY --from=builder /srv/public ./public
CMD ["node", "server.js"]
