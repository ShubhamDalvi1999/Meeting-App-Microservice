const winston = require('winston');
const morgan = require('morgan');
const config = require('../config');

// Create Winston logger
const logger = winston.createLogger({
  level: config.logging.level,
  format: winston.format.combine(
    winston.format.timestamp(),
    config.logging.format === 'json'
      ? winston.format.json()
      : winston.format.simple()
  ),
  defaultMeta: {
    service: 'meeting-app',
    env: process.env.NODE_ENV
  },
  transports: [
    new winston.transports.Console({
      format: winston.format.combine(
        winston.format.colorize(),
        winston.format.printf(({ timestamp, level, message, ...meta }) => {
          return `${timestamp} ${level}: ${message} ${
            Object.keys(meta).length ? JSON.stringify(meta) : ''
          }`;
        })
      )
    })
  ]
});

// Create HTTP request logger middleware
const requestLogger = morgan('combined', {
  stream: {
    write: (message) => logger.http(message.trim())
  }
});

// Create WebSocket logger middleware
const wsLogger = (socket, next) => {
  const start = Date.now();
  const clientIp = socket.handshake.address;
  const query = socket.handshake.query;

  logger.info('WebSocket connection attempt', {
    clientIp,
    query,
    socketId: socket.id
  });

  // Log successful connection
  socket.on('connect', () => {
    logger.info('WebSocket connected', {
      clientIp,
      socketId: socket.id,
      connectionTime: Date.now() - start
    });
  });

  // Log disconnection
  socket.on('disconnect', (reason) => {
    logger.info('WebSocket disconnected', {
      clientIp,
      socketId: socket.id,
      reason,
      duration: Date.now() - start
    });
  });

  // Log errors
  socket.on('error', (error) => {
    logger.error('WebSocket error', {
      clientIp,
      socketId: socket.id,
      error: error.message,
      stack: error.stack
    });
  });

  next();
};

module.exports = {
  logger,
  requestLogger,
  wsLogger
}; 