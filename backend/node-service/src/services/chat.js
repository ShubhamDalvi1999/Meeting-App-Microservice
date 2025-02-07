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
    try {
      const { roomId, message, type = 'text' } = data;
      
      const messageData = {
        id: Date.now().toString(),
        userId: socket.userId,
        username: socket.user.username,
        message,
        type,
        timestamp: new Date().toISOString()
      };

      // Broadcast message to room
      socket.to(roomId).emit('chat_message', messageData);

      // Update metrics
      metrics.chatMessages.inc({ type });
      logger.info(`Chat message sent in room ${roomId} by user ${socket.userId}`);
    } catch (error) {
      logger.error('Error in handleMessage:', error);
      socket.emit('error', { message: 'Failed to send message' });
    }
  }

  // Handle file sharing
  handleFileShare(socket, data) {
    try {
      const { roomId, fileData } = data;
      const { name, size, type, url } = fileData;

      const fileMessage = {
        id: Date.now().toString(),
        userId: socket.userId,
        username: socket.user.username,
        type: 'file',
        fileData: {
          name,
          size,
          type,
          url
        },
        timestamp: new Date().toISOString()
      };

      // Broadcast file share to room
      socket.to(roomId).emit('chat_message', fileMessage);

      // Update metrics
      metrics.fileShares.inc();
      metrics.fileShareBytes.inc(size);
      logger.info(`File shared in room ${roomId} by user ${socket.userId}`);
    } catch (error) {
      logger.error('Error in handleFileShare:', error);
      socket.emit('error', { message: 'Failed to share file' });
    }
  }

  // Get chat history
  getChatHistory(roomId) {
    return this.messageHistory.get(roomId) || [];
  }

  // Handle user typing status
  handleTyping(socket, data) {
    try {
      const { roomId, isTyping } = data;

      if (!this.typingUsers.has(roomId)) {
        this.typingUsers.set(roomId, new Set());
      }

      const typingUsers = this.typingUsers.get(roomId);
      
      if (isTyping) {
        typingUsers.add(socket.userId);
      } else {
        typingUsers.delete(socket.userId);
      }

      // Broadcast typing status to room
      socket.to(roomId).emit('typing_update', {
        userId: socket.userId,
        username: socket.user.username,
        isTyping
      });
    } catch (error) {
      logger.error('Error in handleTyping:', error);
    }
  }

  // Clean up room when it's empty
  cleanupRoom(roomId) {
    this.messageHistory.delete(roomId);
  }

  // Handle message reaction
  handleReaction(socket, data) {
    try {
      const { roomId, messageId, reaction } = data;

      const reactionData = {
        messageId,
        userId: socket.userId,
        username: socket.user.username,
        reaction
      };

      // Broadcast reaction to room
      socket.to(roomId).emit('message_reaction', reactionData);

      // Update metrics
      metrics.messageReactions.inc();
      logger.info(`Reaction added to message ${messageId} by user ${socket.userId}`);
    } catch (error) {
      logger.error('Error in handleReaction:', error);
      socket.emit('error', { message: 'Failed to add reaction' });
    }
  }
}

module.exports = ChatService; 