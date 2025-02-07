const { logger } = require('../utils/logger');
const { metrics } = require('../utils/metrics');

class WebRTCSignaling {
  constructor(io) {
    this.io = io;
    this.rooms = new Map(); // roomId -> Set of socket IDs
  }

  handleJoin(socket, roomId) {
    try {
      // Join the room
      socket.join(roomId);
      
      // Initialize room if it doesn't exist
      if (!this.rooms.has(roomId)) {
        this.rooms.set(roomId, new Set());
      }
      
      const room = this.rooms.get(roomId);
      room.add(socket.id);

      // Notify others in the room
      socket.to(roomId).emit('peer_joined', {
        peerId: socket.id,
        userId: socket.userId,
        username: socket.user.username
      });

      // Send list of existing peers to the new participant
      const peers = Array.from(room).filter(id => id !== socket.id);
      socket.emit('room_users', {
        peers: peers.map(peerId => ({
          peerId,
          userId: this.io.sockets.sockets.get(peerId)?.userId,
          username: this.io.sockets.sockets.get(peerId)?.user?.username
        }))
      });

      logger.info(`User ${socket.userId} joined room ${roomId}`);
      metrics.activeRooms.set(this.rooms.size);
      metrics.usersPerRoom.set({ room: roomId }, room.size);
    } catch (error) {
      logger.error('Error in handleJoin:', error);
      socket.emit('error', { message: 'Failed to join room' });
    }
  }

  handleLeave(socket, roomId) {
    try {
      socket.leave(roomId);
      
      const room = this.rooms.get(roomId);
      if (room) {
        room.delete(socket.id);
        
        if (room.size === 0) {
          this.rooms.delete(roomId);
        }

        // Notify others that peer has left
        socket.to(roomId).emit('peer_left', {
          peerId: socket.id,
          userId: socket.userId
        });

        logger.info(`User ${socket.userId} left room ${roomId}`);
        metrics.activeRooms.set(this.rooms.size);
        metrics.usersPerRoom.set({ room: roomId }, room.size);
      }
    } catch (error) {
      logger.error('Error in handleLeave:', error);
    }
  }

  handleOffer(socket, data) {
    try {
      const { targetId, sdp } = data;
      
      socket.to(targetId).emit('rtc_offer', {
        sdp,
        offererId: socket.id,
        userId: socket.userId
      });

      metrics.webrtcOffers.inc();
    } catch (error) {
      logger.error('Error in handleOffer:', error);
      socket.emit('error', { message: 'Failed to send offer' });
    }
  }

  handleAnswer(socket, data) {
    try {
      const { targetId, sdp } = data;
      
      socket.to(targetId).emit('rtc_answer', {
        sdp,
        answererId: socket.id,
        userId: socket.userId
      });

      metrics.webrtcAnswers.inc();
    } catch (error) {
      logger.error('Error in handleAnswer:', error);
      socket.emit('error', { message: 'Failed to send answer' });
    }
  }

  handleIceCandidate(socket, data) {
    try {
      const { targetId, candidate } = data;
      
      socket.to(targetId).emit('ice_candidate', {
        candidate,
        senderId: socket.id
      });

      metrics.iceCandidates.inc();
    } catch (error) {
      logger.error('Error in handleIceCandidate:', error);
      socket.emit('error', { message: 'Failed to send ICE candidate' });
    }
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
}

module.exports = WebRTCSignaling; 