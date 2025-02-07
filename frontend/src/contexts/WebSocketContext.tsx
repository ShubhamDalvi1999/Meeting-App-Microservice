import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { io, Socket } from 'socket.io-client';
import { useAuth } from './AuthContext';

interface WebSocketContextType {
  socket: Socket | null;
  isConnected: boolean;
  connectionError: string | null;
  joinRoom: (roomId: string) => void;
  leaveRoom: (roomId: string) => void;
  sendMessage: (roomId: string, message: string) => void;
  sendSignal: (userId: string, signal: any) => void;
  sendWhiteboardUpdate: (roomId: string, data: any) => void;
}

const WebSocketContext = createContext<WebSocketContextType>({
  socket: null,
  isConnected: false,
  connectionError: null,
  joinRoom: () => {},
  leaveRoom: () => {},
  sendMessage: () => {},
  sendSignal: () => {},
  sendWhiteboardUpdate: () => {},
});

export const useWebSocket = () => useContext(WebSocketContext);

export const WebSocketProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [socket, setSocket] = useState<Socket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const [reconnectAttempts, setReconnectAttempts] = useState(0);
  const { token } = useAuth();

  const MAX_RECONNECT_ATTEMPTS = 5;
  const RECONNECT_INTERVAL = 5000;
  const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:3001';

  const connectSocket = useCallback(() => {
    if (!token) return;

    try {
      const socketInstance = io(WS_URL, {
        auth: { token },
        transports: ['websocket'],
        reconnection: true,
        reconnectionAttempts: MAX_RECONNECT_ATTEMPTS,
        reconnectionDelay: RECONNECT_INTERVAL,
      });

      socketInstance.on('connect', () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setConnectionError(null);
        setReconnectAttempts(0);
      });

      socketInstance.on('disconnect', (reason) => {
        console.log('WebSocket disconnected:', reason);
        setIsConnected(false);
        if (reason === 'io server disconnect') {
          // Server initiated disconnect, attempt to reconnect
          setTimeout(() => {
            if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
              setReconnectAttempts(prev => prev + 1);
              socketInstance.connect();
            }
          }, RECONNECT_INTERVAL);
        }
      });

      socketInstance.on('connect_error', (error) => {
        console.error('WebSocket connection error:', error);
        setConnectionError(error.message);
        setIsConnected(false);
      });

      socketInstance.on('error', (error: Error) => {
        console.error('WebSocket error:', error);
        setConnectionError(error.message);
      });

      setSocket(socketInstance);

      return () => {
        socketInstance.disconnect();
      };
    } catch (error) {
      console.error('Error creating WebSocket connection:', error);
      setConnectionError(error instanceof Error ? error.message : 'Unknown error');
      return undefined;
    }
  }, [token, reconnectAttempts]);

  useEffect(() => {
    const cleanup = connectSocket();
    return () => cleanup?.();
  }, [connectSocket]);

  const joinRoom = useCallback((roomId: string) => {
    if (socket && isConnected) {
      socket.emit('join-room', { roomId });
    }
  }, [socket, isConnected]);

  const leaveRoom = useCallback((roomId: string) => {
    if (socket && isConnected) {
      socket.emit('leave-room', { roomId });
    }
  }, [socket, isConnected]);

  const sendMessage = useCallback((roomId: string, message: string) => {
    if (socket && isConnected) {
      socket.emit('send-message', { roomId, message });
    }
  }, [socket, isConnected]);

  const sendSignal = useCallback((userId: string, signal: any) => {
    if (socket && isConnected) {
      socket.emit('signal', { userId, signal });
    }
  }, [socket, isConnected]);

  const sendWhiteboardUpdate = useCallback((roomId: string, data: any) => {
    if (socket && isConnected) {
      socket.emit('whiteboard-update', { roomId, data });
    }
  }, [socket, isConnected]);

  return (
    <WebSocketContext.Provider
      value={{
        socket,
        isConnected,
        connectionError,
        joinRoom,
        leaveRoom,
        sendMessage,
        sendSignal,
        sendWhiteboardUpdate,
      }}
    >
      {children}
    </WebSocketContext.Provider>
  );
}; 