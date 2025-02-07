const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const cors = require('cors');
const jwt = require('jsonwebtoken');
require('dotenv').config();

const app = express();
const server = http.createServer(app);
const io = new Server(server, {
  cors: {
    origin: '*',
    methods: ['GET', 'POST']
  }
});

// Middleware
app.use(cors());
app.use(express.json());

// Socket authentication middleware
const authenticateSocket = (socket, next) => {
  const token = socket.handshake.auth.token;
  if (!token) {
    return next(new Error('Authentication error'));
  }

  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET_KEY);
    socket.userId = decoded.user_id;
    next();
  } catch (err) {
    next(new Error('Authentication error'));
  }
};

io.use(authenticateSocket);

// Store active users and their rooms
const activeUsers = new Map(); // userId -> socketId
const userRooms = new Map();  // socketId -> roomId

// WebSocket event handlers
io.on('connection', (socket) => {
  console.log(`User connected: ${socket.userId}`);
  activeUsers.set(socket.userId, socket.id);

  // Join meeting room
  socket.on('join_room', ({ roomId }) => {
    socket.join(roomId);
    userRooms.set(socket.id, roomId);
    
    const roomUsers = Array.from(io.sockets.adapter.rooms.get(roomId) || [])
      .map(socketId => {
        for (const [userId, sid] of activeUsers.entries()) {
          if (sid === socketId) return userId;
        }
      })
      .filter(Boolean);

    io.to(roomId).emit('room_users', { users: roomUsers });
  });

  // Handle WebRTC signaling
  socket.on('signal', ({ userId, signal }) => {
    const targetSocketId = activeUsers.get(userId);
    if (targetSocketId) {
      io.to(targetSocketId).emit('signal', {
        userId: socket.userId,
        signal
      });
    }
  });

  // Handle screen sharing
  socket.on('start_screen_share', () => {
    const roomId = userRooms.get(socket.id);
    if (roomId) {
      io.to(roomId).emit('user_screen_share', {
        userId: socket.userId,
        isSharing: true
      });
    }
  });

  socket.on('stop_screen_share', () => {
    const roomId = userRooms.get(socket.id);
    if (roomId) {
      io.to(roomId).emit('user_screen_share', {
        userId: socket.userId,
        isSharing: false
      });
    }
  });

  // Handle whiteboard events
  socket.on('whiteboard_draw', (data) => {
    const roomId = userRooms.get(socket.id);
    if (roomId) {
      socket.to(roomId).emit('whiteboard_draw', {
        ...data,
        userId: socket.userId
      });
    }
  });

  // Handle chat messages
  socket.on('chat_message', ({ message }) => {
    const roomId = userRooms.get(socket.id);
    if (roomId) {
      io.to(roomId).emit('chat_message', {
        userId: socket.userId,
        message,
        timestamp: new Date().toISOString()
      });
    }
  });

  // Handle disconnection
  socket.on('disconnect', () => {
    console.log(`User disconnected: ${socket.userId}`);
    const roomId = userRooms.get(socket.id);
    if (roomId) {
      io.to(roomId).emit('user_left', { userId: socket.userId });
      userRooms.delete(socket.id);
    }
    activeUsers.delete(socket.userId);
  });
});

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'healthy' });
});

const PORT = process.env.PORT || 4000;
server.listen(PORT, () => {
  console.log(`WebSocket server running on port ${PORT}`);
}); 