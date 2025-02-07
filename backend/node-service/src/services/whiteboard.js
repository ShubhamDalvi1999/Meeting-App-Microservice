const { logger } = require('../utils/logger');
const { metrics } = require('../utils/metrics');

class WhiteboardService {
  constructor(io) {
    this.io = io;
    this.whiteboards = new Map(); // roomId -> { strokes: [], undoStack: [] }
  }

  handleDraw(socket, data) {
    try {
      const { roomId, stroke } = data;

      // Initialize whiteboard for room if it doesn't exist
      if (!this.whiteboards.has(roomId)) {
        this.whiteboards.set(roomId, {
          strokes: [],
          undoStack: []
        });
      }

      const whiteboard = this.whiteboards.get(roomId);
      
      // Add stroke data
      const strokeData = {
        id: Date.now().toString(),
        userId: socket.userId,
        username: socket.user.username,
        ...stroke,
        timestamp: new Date().toISOString()
      };

      whiteboard.strokes.push(strokeData);
      whiteboard.undoStack = []; // Clear redo stack on new stroke

      // Broadcast stroke to room
      socket.to(roomId).emit('whiteboard_draw', strokeData);

      // Update metrics
      metrics.whiteboardStrokes.inc();
      logger.info(`New whiteboard stroke in room ${roomId} by user ${socket.userId}`);
    } catch (error) {
      logger.error('Error in handleDraw:', error);
      socket.emit('error', { message: 'Failed to draw stroke' });
    }
  }

  handleClear(socket, data) {
    try {
      const { roomId } = data;

      if (this.whiteboards.has(roomId)) {
        const whiteboard = this.whiteboards.get(roomId);
        
        // Store current state in undo stack
        whiteboard.undoStack.push([...whiteboard.strokes]);
        whiteboard.strokes = [];

        // Broadcast clear to room
        socket.to(roomId).emit('whiteboard_clear', {
          userId: socket.userId,
          username: socket.user.username,
          timestamp: new Date().toISOString()
        });

        // Update metrics
        metrics.whiteboardClears.inc();
        logger.info(`Whiteboard cleared in room ${roomId} by user ${socket.userId}`);
      }
    } catch (error) {
      logger.error('Error in handleClear:', error);
      socket.emit('error', { message: 'Failed to clear whiteboard' });
    }
  }

  handleUndo(socket, data) {
    try {
      const { roomId } = data;

      if (this.whiteboards.has(roomId)) {
        const whiteboard = this.whiteboards.get(roomId);
        
        if (whiteboard.strokes.length > 0) {
          // Store current state for redo
          const lastStroke = whiteboard.strokes.pop();
          whiteboard.undoStack.push(lastStroke);

          // Broadcast undo to room
          socket.to(roomId).emit('whiteboard_undo', {
            userId: socket.userId,
            username: socket.user.username,
            strokeId: lastStroke.id,
            timestamp: new Date().toISOString()
          });

          // Update metrics
          metrics.whiteboardUndos.inc();
          logger.info(`Stroke undone in room ${roomId} by user ${socket.userId}`);
        }
      }
    } catch (error) {
      logger.error('Error in handleUndo:', error);
      socket.emit('error', { message: 'Failed to undo stroke' });
    }
  }

  handleRedo(socket, data) {
    try {
      const { roomId } = data;

      if (this.whiteboards.has(roomId)) {
        const whiteboard = this.whiteboards.get(roomId);
        
        if (whiteboard.undoStack.length > 0) {
          // Restore last undone stroke
          const strokeToRedo = whiteboard.undoStack.pop();
          whiteboard.strokes.push(strokeToRedo);

          // Broadcast redo to room
          socket.to(roomId).emit('whiteboard_redo', {
            userId: socket.userId,
            username: socket.user.username,
            stroke: strokeToRedo,
            timestamp: new Date().toISOString()
          });

          // Update metrics
          metrics.whiteboardRedos.inc();
          logger.info(`Stroke redone in room ${roomId} by user ${socket.userId}`);
        }
      }
    } catch (error) {
      logger.error('Error in handleRedo:', error);
      socket.emit('error', { message: 'Failed to redo stroke' });
    }
  }

  // Get current whiteboard state for a room
  getWhiteboardState(roomId) {
    return this.whiteboards.get(roomId) || { strokes: [], undoStack: [] };
  }
}

module.exports = WhiteboardService; 