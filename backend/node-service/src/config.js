require('dotenv').config();

const config = {
  // Server configuration
  port: process.env.PORT || 3001,
  host: process.env.HOST || '0.0.0.0',

  // CORS configuration
  cors: {
    origin: process.env.CORS_ORIGIN || 'http://localhost:3000',
    methods: ['GET', 'POST'],
    credentials: true
  },

  // Redis configuration
  redis: {
    url: process.env.REDIS_URL || 'redis://redis:6379',
    options: {
      retryStrategy: (times) => {
        const delay = Math.min(times * 50, 2000);
        return delay;
      },
      maxRetriesPerRequest: 3
    }
  },

  // JWT configuration
  jwt: {
    secret: process.env.JWT_SECRET || 'your-secret-key',
    expiresIn: process.env.JWT_EXPIRES_IN || '24h'
  },

  // WebRTC configuration
  webrtc: {
    iceServers: [
      {
        urls: process.env.STUN_SERVERS?.split(',') || [
          'stun:stun.l.google.com:19302',
          'stun:stun1.l.google.com:19302'
        ]
      },
      {
        urls: process.env.TURN_SERVERS?.split(',') || [],
        username: process.env.TURN_USERNAME,
        credential: process.env.TURN_CREDENTIAL
      }
    ].filter(server => server.urls.length > 0)
  },

  // Metrics configuration
  metrics: {
    enabled: process.env.ENABLE_METRICS === 'true',
    prefix: 'meeting_app_',
    defaultLabels: {
      app: 'meeting-app',
      env: process.env.NODE_ENV || 'development'
    }
  },

  // Logging configuration
  logging: {
    level: process.env.LOG_LEVEL || 'info',
    format: process.env.LOG_FORMAT || 'json'
  },

  // File sharing configuration
  fileSharing: {
    maxSize: parseInt(process.env.MAX_FILE_SIZE) || 10 * 1024 * 1024, // 10MB
    allowedTypes: process.env.ALLOWED_FILE_TYPES?.split(',') || [
      'image/*',
      'application/pdf',
      'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'text/plain'
    ]
  },

  // Room configuration
  room: {
    maxParticipants: parseInt(process.env.MAX_ROOM_PARTICIPANTS) || 12,
    timeout: parseInt(process.env.ROOM_TIMEOUT) || 30 * 60 * 1000 // 30 minutes
  }
};

module.exports = config; 