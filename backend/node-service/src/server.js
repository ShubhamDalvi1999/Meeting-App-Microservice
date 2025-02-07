const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const cors = require('cors');
const Redis = require('ioredis');
const config = require('./config');
const { logger, requestLogger, wsLogger } = require('./utils/logger');
const { metrics, metricsMiddleware } = require('./utils/metrics');
const WebRTCSignaling = require('./services/webrtc');
const ChatService = require('./services/chat');
const WhiteboardService = require('./services/whiteboard');

// Initialize Express app
const app = express();
const server = http.createServer(app);
const io = new Server(server, {
  cors: config.cors,
  pingTimeout: 60000,
  pingInterval: 25000
});

// Initialize Redis client
const redis = new Redis(config.redis.url);

// Middleware
app.use(cors(config.cors));
app.use(requestLogger);

// Health check endpoint
app.get('/health', (req, res) => {
  redis.ping()
    .then(() => {
      res.json({ 
        status: 'healthy',
        redis: 'connected',
        uptime: process.uptime()
      });
    })
    .catch((error) => {
      logger.error('Redis health check failed:', error);
      res.status(500).json({ 
        status: 'unhealthy',
        redis: 'disconnected',
        error: error.message
      });
    });
});

// Metrics endpoint
if (config.metrics.enabled) {
  app.get('/metrics', metricsMiddleware);
}

// Initialize services
const webrtcService = new WebRTCSignaling(io);
const chatService = new ChatService(io);
const whiteboardService = new WhiteboardService(io);

// WebSocket connection handling
io.use(wsLogger);
io.use((socket, next) => {
  const token = socket.handshake.auth.token;
  if (!token) {
    return next(new Error('Authentication error'));
  }
  // Verify token and set user data
  try {
    const decoded = jwt.verify(token, config.jwt.secret);
    socket.userId = decoded.userId;
    socket.user = decoded;
    next();
  } catch (err) {
    next(new Error('Invalid token'));
  }
});

io.on('connection', (socket) => {
  logger.info(`Client connected: ${socket.id}`);
  metrics.activeConnections.inc();

  // WebRTC events
  socket.on('join_room', (roomId) => webrtcService.handleJoin(socket, roomId));
  socket.on('leave_room', (roomId) => webrtcService.handleLeave(socket, roomId));
  socket.on('rtc_offer', (data) => webrtcService.handleOffer(socket, data));
  socket.on('rtc_answer', (data) => webrtcService.handleAnswer(socket, data));
  socket.on('ice_candidate', (data) => webrtcService.handleIceCandidate(socket, data));

  // Chat events
  socket.on('chat_message', (data) => chatService.handleMessage(socket, data));
  socket.on('typing', (data) => chatService.handleTyping(socket, data));
  socket.on('file_share', (data) => chatService.handleFileShare(socket, data));
  socket.on('message_reaction', (data) => chatService.handleReaction(socket, data));

  // Whiteboard events
  socket.on('whiteboard_draw', (data) => whiteboardService.handleDraw(socket, data));
  socket.on('whiteboard_clear', (data) => whiteboardService.handleClear(socket, data));
  socket.on('whiteboard_undo', (data) => whiteboardService.handleUndo(socket, data));

  socket.on('disconnect', () => {
    logger.info(`Client disconnected: ${socket.id}`);
    metrics.activeConnections.dec();
  });

  socket.on('error', (error) => {
    logger.error(`Socket error: ${error.message}`);
    metrics.webrtcErrors.inc();
  });
});

// Error handling
app.use((err, req, res, next) => {
  logger.error('Error:', err);
  res.status(500).json({ status: 'error', message: err.message });
});

// Start server
const PORT = config.port;
const HOST = config.host;

server.listen(PORT, HOST, (error) => {
  if (error) {
    logger.error('Failed to start server:', error);
    process.exit(1);
  }
  logger.info(`WebSocket server running on ${HOST}:${PORT}`);
}); 
}); 