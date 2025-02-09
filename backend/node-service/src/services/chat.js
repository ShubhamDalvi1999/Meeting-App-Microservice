const { logger } = require('../utils/logger');
const { metrics } = require('../utils/metrics');

class ChatService {
  constructor(io) {
    this.io = io;
    this.messageHistory = new Map(); // roomId -> array of messages
    this.MAX_HISTORY = 100; // Maximum number of messages to keep per room
    this.typingUsers = new Map(); // roomId -> Set of typing users
  }

  // Initialize a new room's chat
  initRoom(roomId) {
    if (!this.messageHistory.has(roomId)) {
      this.messageHistory.set(roomId, []);
    }
  }

  // Handle new message
  handleMessage(socket, data) {
    const { roomId, message } = data;
    logger.info(`New message in room ${roomId} from user ${socket.id}`);
    
    this.io.to(roomId).emit('chat-message', {
      userId: socket.id,
      message,
      timestamp: Date.now()
    });
  }

  // Handle file sharing
  handleFileShare(socket, data) {
    const { roomId, fileInfo } = data;
    logger.info(`File shared in room ${roomId} by user ${socket.id}`);
    
    this.io.to(roomId).emit('file-shared', {
      userId: socket.id,
      fileInfo,
      timestamp: Date.now()
    });
  }

  // Get chat history
  getChatHistory(roomId) {
    return this.messageHistory.get(roomId) || [];
  }

  // Handle user typing status
  handleTyping(socket, data) {
    const { roomId, isTyping } = data;
    
    if (!this.typingUsers.has(roomId)) {
      this.typingUsers.set(roomId, new Set());
    }

    const roomTyping = this.typingUsers.get(roomId);
    if (isTyping) {
      roomTyping.add(socket.id);
    } else {
      roomTyping.delete(socket.id);
    }

    socket.to(roomId).emit('typing-update', {
      userId: socket.id,
      isTyping
    });
  }

  // Clean up room when it's empty
  cleanupRoom(roomId) {
    this.messageHistory.delete(roomId);
  }

  // Handle message reaction
  handleReaction(socket, data) {
    const { roomId, messageId, reaction } = data;
    
    this.io.to(roomId).emit('message-reaction', {
      userId: socket.id,
      messageId,
      reaction,
      timestamp: Date.now()
    });
  }

  handleDisconnect(socket) {
    // Remove user from typing lists in all rooms
    this.typingUsers.forEach((users, roomId) => {
      if (users.has(socket.id)) {
        users.delete(socket.id);
        if (users.size === 0) {
          this.typingUsers.delete(roomId);
        }
        // Notify room that user stopped typing
        socket.to(roomId).emit('typing-update', {
          userId: socket.id,
          isTyping: false
        });
      }
    });
  }
}

module.exports = ChatService; 