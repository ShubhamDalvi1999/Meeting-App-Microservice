FROM node:18-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    jq \
    && rm -rf /var/lib/apt/lists/*

# Copy package files
COPY package*.json ./

# Install all dependencies from package.json
RUN npm install && \
    npm cache clean --force

# Create directories
RUN mkdir -p /app/logs /app/src

# Copy source code separately to avoid permission issues
COPY src/ /app/src/
COPY *.js /app/

# Create healthcheck script that tests Redis connection
RUN echo '#!/bin/sh\n\
\n\
# Test HTTP endpoint\n\
RESPONSE=$(curl -s http://localhost:3001/health)\n\
if [ $? -ne 0 ]; then\n\
  echo "Healthcheck failed: Could not connect to service"\n\
  exit 1\n\
fi\n\
\n\
# Extract status from response\n\
STATUS=$(echo $RESPONSE | jq -r .status 2>/dev/null)\n\
\n\
# Handle "degraded" status as healthy to allow container time to fully connect\n\
if [ "$STATUS" = "degraded" ]; then\n\
  echo "Service is degraded but operational..."\n\
  exit 0\n\
fi\n\
\n\
# Require "healthy" status for fully operational service\n\
if [ "$STATUS" != "healthy" ]; then\n\
  echo "Healthcheck failed: Service returned status $STATUS"\n\
  exit 1\n\
fi\n\
\n\
exit 0\n\
' > /healthcheck.sh && \
chmod +x /healthcheck.sh

# Set environment
ENV NODE_ENV=production
ENV PORT=3001

# Expose port
EXPOSE 3001

# Health check with more lenient parameters
HEALTHCHECK --interval=30s --timeout=30s --start-period=30s --retries=3 \
    CMD /healthcheck.sh

# Start the application with error handling
CMD ["node", "src/server.js"] 