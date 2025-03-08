// Initialize environment variables from .env file
try {
  require('dotenv').config();
} catch (error) {
  console.log('Error loading dotenv, using process.env variables:', error.message);
}

const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const cors = require('cors');
const Redis = require('ioredis');
const morgan = require('morgan');
const winston = require('winston');
const helmet = require('helmet');
const compression = require('compression');
const jwt = require('jsonwebtoken');
const WebRTCSignaling = require('./services/webrtc');
const ChatService = require('./services/chat');
const WhiteboardService = require('./services/whiteboard');
const config = require('./config');

// Setup logger
const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  transports: [
    new winston.transports.Console(),
    new winston.transports.File({ filename: 'logs/error.log', level: 'error' }),
    new winston.transports.File({ filename: 'logs/combined.log' })
  ]
});

// Initialize Express app
const app = express();
const server = http.createServer(app);

// Set port
const PORT = process.env.PORT || 3001;

// Middleware
app.use(cors());
app.use(helmet());
app.use(compression());
app.use(express.json());
app.use(morgan('dev'));

// Redis client
let redisClient;
let redisReconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 10;

function connectRedis() {
  try {
    const redisUrl = process.env.REDIS_URL || 'redis://:dev-redis-123@redis:6379/0';
    logger.info(`Connecting to Redis at ${redisUrl.replace(/:[^:]*@/, ':****@')}`);
    
    redisClient = new Redis(redisUrl, {
      retryStrategy: (times) => {
        redisReconnectAttempts = times;
        if (times > MAX_RECONNECT_ATTEMPTS) {
          logger.error(`Redis connection failed after ${times} attempts. Giving up.`);
          return null; // stop retrying
        }
        const delay = Math.min(times * 1000, 5000);
        logger.info(`Redis reconnecting... attempt ${times}. Retrying in ${delay}ms`);
        return delay;
      }
    });

    redisClient.on('connect', () => {
      logger.info('Redis connection established');
      redisReconnectAttempts = 0;
    });

    redisClient.on('error', (err) => {
      logger.error(`Redis error: ${err.message}`);
    });

    return redisClient;
  } catch (error) {
    logger.error(`Redis connection error: ${error.message}`);
    return null;
  }
}

// Initialize Redis connection
connectRedis();

// Socket.io setup
const io = socketIo(server, {
  cors: {
    origin: '*',
    methods: ['GET', 'POST']
  }
});

// Initialize services
const webrtcService = new WebRTCSignaling(io);
const chatService = new ChatService(io);
const whiteboardService = new WhiteboardService(io);

// Health check endpoint
app.get('/health', (req, res) => {
  const healthInfo = {
    status: 'healthy',
    service: 'websocket',
    timestamp: new Date().toISOString(),
    environment: process.env.NODE_ENV || 'development',
    system_info: {
      node_version: process.version,
      platform: process.platform,
      arch: process.arch,
      hostname: require('os').hostname()
    },
    dependencies: {}
  };

  // Check Redis connectivity
  if (redisClient) {
    redisClient.ping()
      .then(() => {
        healthInfo.dependencies.redis = {
          status: 'connected',
          reconnect_attempts: redisReconnectAttempts
        };
        res.status(200).json(healthInfo);
      })
      .catch((err) => {
        healthInfo.status = 'degraded';
        healthInfo.dependencies.redis = {
          status: 'disconnected',
          error: err.message,
          reconnect_attempts: redisReconnectAttempts
        };
        res.status(200).json(healthInfo);
      });
  } else {
    healthInfo.status = 'degraded';
    healthInfo.dependencies.redis = {
      status: 'not_initialized'
    };
    res.status(200).json(healthInfo);
  }
});

// Socket.io event handlers
io.on('connection', (socket) => {
  logger.info(`User connected: ${socket.id}`);

  socket.on('join-meeting', (meetingId) => {
    socket.join(meetingId);
    logger.info(`User ${socket.id} joined meeting ${meetingId}`);
  });

  socket.on('leave-meeting', (meetingId) => {
    socket.leave(meetingId);
    logger.info(`User ${socket.id} left meeting ${meetingId}`);
  });

  socket.on('message', (data) => {
    io.to(data.meetingId).emit('message', data);
    logger.info(`Message sent in meeting ${data.meetingId} by ${socket.id}`);
  });

  socket.on('disconnect', () => {
    logger.info(`User disconnected: ${socket.id}`);
  });
});

// Start server
server.listen(PORT, () => {
  logger.info(`WebSocket service running on port ${PORT}`);
});

// Handle graceful shutdown
process.on('SIGTERM', () => {
  logger.info('SIGTERM signal received: closing HTTP server');
  server.close(() => {
    logger.info('HTTP server closed');
    if (redisClient) {
      redisClient.quit();
    }
    process.exit(0);
  });
}); 