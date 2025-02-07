FROM node:18-alpine

WORKDIR /app

# Install wget for health checks
RUN apk add --no-cache wget curl

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the application
COPY . .

# Set environment variables
ENV PORT=3001

# Add health check
HEALTHCHECK --interval=10s --timeout=5s --start-period=10s --retries=3 \
  CMD wget -qO- http://localhost:3001/health || exit 1

EXPOSE 3001

CMD ["npm", "start"] 