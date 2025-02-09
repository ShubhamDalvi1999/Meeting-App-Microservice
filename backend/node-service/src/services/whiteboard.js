const { logger } = require('../utils/logger');
const { metrics } = require('../utils/metrics');

class WhiteboardService {
  constructor(io) {
    this.io = io;
    this.whiteboards = new Map();
  }

  handleDraw(socket, data) {
    const { roomId, path } = data;
    logger.info(`New drawing in room ${roomId} from user ${socket.id}`);
    
    if (!this.whiteboards.has(roomId)) {
      this.whiteboards.set(roomId, {
        paths: [],
        undoStack: [],
        redoStack: []
      });
    }

    const whiteboard = this.whiteboards.get(roomId);
    whiteboard.paths.push({
      userId: socket.id,
      path,
      timestamp: Date.now()
    });
    whiteboard.redoStack = []; // Clear redo stack on new draw

    this.io.to(roomId).emit('draw', {
      userId: socket.id,
      path
    });
  }

  handleClear(socket, data) {
    const { roomId } = data;
    logger.info(`Clearing whiteboard in room ${roomId}`);
    
    if (this.whiteboards.has(roomId)) {
      const whiteboard = this.whiteboards.get(roomId);
      whiteboard.undoStack.push([...whiteboard.paths]);
      whiteboard.paths = [];
      whiteboard.redoStack = [];
    }

    this.io.to(roomId).emit('clear', {
      userId: socket.id
    });
  }

  handleUndo(socket, data) {
    const { roomId } = data;
    
    if (this.whiteboards.has(roomId)) {
      const whiteboard = this.whiteboards.get(roomId);
      if (whiteboard.paths.length > 0) {
        const lastPath = whiteboard.paths.pop();
        whiteboard.undoStack.push(lastPath);
        
        this.io.to(roomId).emit('undo', {
          userId: socket.id,
          pathId: lastPath.timestamp
        });
      }
    }
  }

  handleRedo(socket, data) {
    const { roomId } = data;
    
    if (this.whiteboards.has(roomId)) {
      const whiteboard = this.whiteboards.get(roomId);
      if (whiteboard.undoStack.length > 0) {
        const pathToRedo = whiteboard.undoStack.pop();
        whiteboard.paths.push(pathToRedo);
        
        this.io.to(roomId).emit('redo', {
          userId: socket.id,
          path: pathToRedo.path
        });
      }
    }
  }

  handleDisconnect(socket) {
    // No cleanup needed for whiteboard data
    // Data persists until room is deleted
  }

  // Get current whiteboard state for a room
  getWhiteboardState(roomId) {
    return this.whiteboards.get(roomId) || { paths: [], undoStack: [], redoStack: [] };
  }
}

module.exports = WhiteboardService; 