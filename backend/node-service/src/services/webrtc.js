const { logger } = require('../utils/logger');
const { metrics } = require('../utils/metrics');

class WebRTCSignaling {
  constructor(io) {
    this.io = io;
    this.rooms = new Map(); // roomId -> Set of socket IDs
  }

  handleJoin(socket, roomId) {
    logger.info(`User ${socket.id} joining room ${roomId}`);
    socket.join(roomId);
    
    if (!this.rooms.has(roomId)) {
      this.rooms.set(roomId, new Set());
    }
    this.rooms.get(roomId).add(socket.id);

    // Notify others in the room
    socket.to(roomId).emit('user-joined', { userId: socket.id });

    // Send list of existing peers to the new participant
    const peers = Array.from(this.rooms.get(roomId)).filter(id => id !== socket.id);
    socket.emit('room_users', {
      peers: peers.map(peerId => ({
        peerId,
        userId: this.io.sockets.sockets.get(peerId)?.userId,
        username: this.io.sockets.sockets.get(peerId)?.user?.username
      }))
    });

    logger.info(`User ${socket.userId} joined room ${roomId}`);
    metrics.activeRooms.set(this.rooms.size);
    metrics.usersPerRoom.set({ room: roomId }, this.rooms.get(roomId).size);
  }

  handleLeave(socket, roomId) {
    logger.info(`User ${socket.id} leaving room ${roomId}`);
    socket.leave(roomId);
    
    if (this.rooms.has(roomId)) {
      this.rooms.get(roomId).delete(socket.id);
      if (this.rooms.get(roomId).size === 0) {
        this.rooms.delete(roomId);
      }
    }

    // Notify others in the room
    socket.to(roomId).emit('user-left', { userId: socket.id });

    logger.info(`User ${socket.userId} left room ${roomId}`);
    metrics.activeRooms.set(this.rooms.size);
    metrics.usersPerRoom.set({ room: roomId }, this.rooms.get(roomId)?.size || 0);
  }

  handleOffer(socket, data) {
    const { targetId, offer } = data;
    logger.info(`Relaying offer from ${socket.id} to ${targetId}`);
    this.io.to(targetId).emit('offer', {
      userId: socket.id,
      offer
    });

    metrics.webrtcOffers.inc();
  }

  handleAnswer(socket, data) {
    const { targetId, answer } = data;
    logger.info(`Relaying answer from ${socket.id} to ${targetId}`);
    this.io.to(targetId).emit('answer', {
      userId: socket.id,
      answer
    });

    metrics.webrtcAnswers.inc();
  }

  handleIceCandidate(socket, data) {
    const { targetId, candidate } = data;
    logger.info(`Relaying ICE candidate from ${socket.id} to ${targetId}`);
    this.io.to(targetId).emit('ice-candidate', {
      userId: socket.id,
      candidate
    });

    metrics.iceCandidates.inc();
  }

  // Handle media stream events
  handleMediaStreamStart(socket, { roomId, type }) {
    socket.to(roomId).emit('media_stream_start', {
      userId: socket.userId,
      type // 'video', 'audio', or 'screen'
    });
  }

  handleMediaStreamStop(socket, { roomId, type }) {
    socket.to(roomId).emit('media_stream_stop', {
      userId: socket.userId,
      type
    });
  }

  // Handle connection state changes
  handleConnectionStateChange(socket, { roomId, state }) {
    socket.to(roomId).emit('peer_connection_state', {
      userId: socket.userId,
      state
    });
  }

  handleDisconnect(socket) {
    // Remove user from all rooms they were in
    this.rooms.forEach((users, roomId) => {
      if (users.has(socket.id)) {
        this.handleLeave(socket, roomId);
      }
    });
  }
}

module.exports = WebRTCSignaling; 