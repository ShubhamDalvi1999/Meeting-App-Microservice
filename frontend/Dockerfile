# Build stage
FROM node:18-slim AS builder

WORKDIR /app

# Set environment variables for build
ENV NEXT_PUBLIC_API_URL=http://localhost:5000
ENV NEXT_PUBLIC_AUTH_URL=http://localhost:5001
ENV NEXT_PUBLIC_WS_URL=ws://localhost:3001
ENV NEXT_PUBLIC_APP_NAME="Meeting App"
ENV NEXT_PUBLIC_APP_VERSION=1.0.0
ENV NEXT_PUBLIC_ENABLE_ANALYTICS=false
ENV NEXT_PUBLIC_ENABLE_DEBUG_TOOLS=false
ENV NEXT_PUBLIC_API_TIMEOUT_MS=30000
ENV NEXT_PUBLIC_WS_RECONNECT_INTERVAL_MS=5000
ENV NEXT_PUBLIC_MAX_UPLOAD_SIZE_MB=5

# Copy package files
COPY package*.json ./

# Install dependencies and ensure React types are installed
RUN npm install
RUN npm install --save-dev @types/react @types/react-dom

# Create necessary directories
RUN mkdir -p /app/public /app/src

# Copy app source by category to avoid Windows permission issues
COPY public/ /app/public/
COPY src/ /app/src/
COPY *.js /app/
COPY *.json /app/
COPY *.css /app/

# Build the application
RUN npm run build

# Production stage
FROM node:18-slim AS runner

WORKDIR /app

# Set environment variables
ENV NODE_ENV=production
ENV PORT=3000
ENV NEXT_PUBLIC_API_URL=http://localhost:5000
ENV NEXT_PUBLIC_AUTH_URL=http://localhost:5001
ENV NEXT_PUBLIC_WS_URL=ws://localhost:3001
ENV HOST=0.0.0.0

# Create public directory if it doesn't exist
RUN mkdir -p public

# Copy necessary files from builder
COPY --from=builder /app/next.config.js ./
COPY --from=builder /app/public/ ./public/
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json
# Copy the standalone output for the server
COPY --from=builder /app/.next/standalone ./

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000/api/health || exit 1

# Start the application with explicit host binding
CMD ["node", "server.js"] 