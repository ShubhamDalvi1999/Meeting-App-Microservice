const promClient = require('prom-client');
const config = require('../config');

// Initialize metrics registry
const register = new promClient.Registry();

// Add default labels from config
register.setDefaultLabels(config.metrics.defaultLabels);

// Define metrics
const metrics = {
  // Connection metrics
  activeConnections: new promClient.Gauge({
    name: `${config.metrics.prefix}active_connections`,
    help: 'Number of active WebSocket connections',
    registers: [register]
  }),

  // Room metrics
  activeRooms: new promClient.Gauge({
    name: `${config.metrics.prefix}active_rooms`,
    help: 'Number of active meeting rooms',
    registers: [register]
  }),

  usersPerRoom: new promClient.Gauge({
    name: `${config.metrics.prefix}users_per_room`,
    help: 'Number of users in each room',
    labelNames: ['room'],
    registers: [register]
  }),

  // WebRTC metrics
  webrtcOffers: new promClient.Counter({
    name: `${config.metrics.prefix}webrtc_offers_total`,
    help: 'Total number of WebRTC offers sent',
    registers: [register]
  }),

  webrtcAnswers: new promClient.Counter({
    name: `${config.metrics.prefix}webrtc_answers_total`,
    help: 'Total number of WebRTC answers sent',
    registers: [register]
  }),

  iceCandidates: new promClient.Counter({
    name: `${config.metrics.prefix}ice_candidates_total`,
    help: 'Total number of ICE candidates exchanged',
    registers: [register]
  }),

  webrtcErrors: new promClient.Counter({
    name: `${config.metrics.prefix}webrtc_errors_total`,
    help: 'Total number of WebRTC errors',
    registers: [register]
  }),

  // Chat metrics
  chatMessages: new promClient.Counter({
    name: `${config.metrics.prefix}chat_messages_total`,
    help: 'Total number of chat messages sent',
    labelNames: ['type'],
    registers: [register]
  }),

  messageReactions: new promClient.Counter({
    name: `${config.metrics.prefix}message_reactions_total`,
    help: 'Total number of message reactions',
    registers: [register]
  }),

  // File sharing metrics
  fileShares: new promClient.Counter({
    name: `${config.metrics.prefix}file_shares_total`,
    help: 'Total number of files shared',
    registers: [register]
  }),

  fileShareBytes: new promClient.Counter({
    name: `${config.metrics.prefix}file_share_bytes_total`,
    help: 'Total bytes of shared files',
    registers: [register]
  }),

  // Whiteboard metrics
  whiteboardStrokes: new promClient.Counter({
    name: `${config.metrics.prefix}whiteboard_strokes_total`,
    help: 'Total number of whiteboard strokes',
    registers: [register]
  }),

  whiteboardClears: new promClient.Counter({
    name: `${config.metrics.prefix}whiteboard_clears_total`,
    help: 'Total number of whiteboard clears',
    registers: [register]
  }),

  whiteboardUndos: new promClient.Counter({
    name: `${config.metrics.prefix}whiteboard_undos_total`,
    help: 'Total number of whiteboard undos',
    registers: [register]
  }),

  whiteboardRedos: new promClient.Counter({
    name: `${config.metrics.prefix}whiteboard_redos_total`,
    help: 'Total number of whiteboard redos',
    registers: [register]
  })
};

// Create metrics middleware
const metricsMiddleware = async (req, res) => {
  try {
    res.set('Content-Type', register.contentType);
    res.end(await register.metrics());
  } catch (error) {
    res.status(500).end(error.message);
  }
};

module.exports = {
  metrics,
  metricsMiddleware,
  register
}; 