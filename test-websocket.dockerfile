FROM node:18-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/node-service/package.json .
RUN npm install && \
    npm install prom-client && \
    npm cache clean --force

ENV NODE_ENV=production
ENV PORT=3001

CMD ["node", "-e", "console.log('Node version:', process.version); try { require('prom-client'); console.log('prom-client is installed'); } catch(e) { console.log('Error loading prom-client:', e.message); }"] 