require('dotenv').config();
const express = require('express');
const { createServer } = require('http');
const { Server } = require('socket.io');
const cors = require('cors');
const Redis = require('ioredis');
const morgan = require('morgan');
const helmet = require('helmet');
const compression = require('compression');
const jwt = require('jsonwebtoken');
const { logger } = require('./utils/logger');
const WebRTCSignaling = require('./services/webrtc');
const ChatService = require('./services/chat');
const WhiteboardService = require('./services/whiteboard');
const config = require('./config');

const app = express();
const server = createServer(app);
const io = new Server(server, {
  cors: {
    origin: process.env.CORS_ORIGINS?.split(',') || ['http://localhost:3000'],
    methods: ['GET', 'POST'],
    credentials: true
  }
});

// Initialize Redis client
const redis = new Redis(config.redis.url, config.redis.options);

// Initialize services
const webrtcService = new WebRTCSignaling(io);
const chatService = new ChatService(io);
const whiteboardService = new WhiteboardService(io);

// Middleware
app.use(cors());
app.use(helmet());
app.use(compression());
app.use(morgan('combined', { stream: { write: message => logger.info(message.trim()) } }));
app.use(express.json());

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Socket.io middleware for authentication
io.use(async (socket, next) => {
  const token = socket.handshake.auth.token;
  if (!token) {
    return next(new Error('Authentication token required'));
  }

  try {
    // Verify token with Redis
    const isValid = await redis.get(`token:${token}`);
    if (!isValid) {
      return next(new Error('Invalid token'));
    }
    next();
  } catch (error) {
    logger.error('Socket authentication error:', error);
    next(new Error('Authentication error'));
  }
});

// Socket.io connection handling
io.on('connection', (socket) => {
  logger.info(`Client connected: ${socket.id}`);

  // Join room
  socket.on('join-room', (roomId) => {
    socket.join(roomId);
    logger.info(`Client ${socket.id} joined room ${roomId}`);
    io.to(roomId).emit('user-connected', { userId: socket.id });
  });

  // Leave room
  socket.on('leave-room', (roomId) => {
    socket.leave(roomId);
    logger.info(`Client ${socket.id} left room ${roomId}`);
    io.to(roomId).emit('user-disconnected', { userId: socket.id });
  });

  // WebRTC events
  socket.on('offer', (data) => webrtcService.handleOffer(socket, data));
  socket.on('answer', (data) => webrtcService.handleAnswer(socket, data));
  socket.on('ice-candidate', (data) => webrtcService.handleIceCandidate(socket, data));

  // Chat events
  socket.on('send-message', (data) => chatService.handleMessage(socket, data));
  socket.on('typing', (data) => chatService.handleTyping(socket, data));
  socket.on('file-share', (data) => chatService.handleFileShare(socket, data));
  socket.on('message-reaction', (data) => chatService.handleReaction(socket, data));

  // Whiteboard events
  socket.on('draw', (data) => whiteboardService.handleDraw(socket, data));
  socket.on('clear', (data) => whiteboardService.handleClear(socket, data));
  socket.on('undo', (data) => whiteboardService.handleUndo(socket, data));
  socket.on('redo', (data) => whiteboardService.handleRedo(socket, data));

  // Disconnect handling
  socket.on('disconnect', () => {
    logger.info(`Client disconnected: ${socket.id}`);
    webrtcService.handleDisconnect(socket);
    chatService.handleDisconnect(socket);
    whiteboardService.handleDisconnect(socket);
  });
});

// Start server
const PORT = process.env.PORT || 3001;
server.listen(PORT, '0.0.0.0', () => {
  logger.info(`WebSocket server running on port ${PORT}`);
}); 