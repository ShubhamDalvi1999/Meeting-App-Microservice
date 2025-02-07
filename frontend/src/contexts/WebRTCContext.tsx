import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { useWebSocket } from './WebSocketContext';
import { useAuth } from './AuthContext';

interface MediaStreamError {
  name: string;
  message: string;
}

interface PeerConnection {
  userId: string;
  connection: RTCPeerConnection;
  stream: MediaStream;
}

interface SignalData {
  type: 'offer' | 'answer' | 'candidate';
  sdp?: string;
  candidate?: RTCIceCandidateInit;
}

interface WebRTCContextType {
  localStream: MediaStream | null;
  remoteStreams: Map<string, MediaStream>;
  error: MediaStreamError | null;
  startLocalStream: () => Promise<void>;
  stopLocalStream: () => void;
  toggleAudio: () => void;
  toggleVideo: () => void;
  startScreenShare: () => Promise<MediaStream | void>;
  stopScreenShare: () => void;
  isAudioEnabled: boolean;
  isVideoEnabled: boolean;
  isScreenSharing: boolean;
}

const WebRTCContext = createContext<WebRTCContextType>({
  localStream: null,
  remoteStreams: new Map(),
  error: null,
  startLocalStream: async () => {},
  stopLocalStream: () => {},
  toggleAudio: () => {},
  toggleVideo: () => {},
  startScreenShare: async () => {},
  stopScreenShare: () => {},
  isAudioEnabled: false,
  isVideoEnabled: false,
  isScreenSharing: false,
});

export const useWebRTC = () => useContext(WebRTCContext);

export const WebRTCProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [localStream, setLocalStream] = useState<MediaStream | null>(null);
  const [remoteStreams, setRemoteStreams] = useState<Map<string, MediaStream>>(new Map());
  const [error, setError] = useState<MediaStreamError | null>(null);
  const [isAudioEnabled, setIsAudioEnabled] = useState(true);
  const [isVideoEnabled, setIsVideoEnabled] = useState(true);
  const [isScreenSharing, setIsScreenSharing] = useState(false);
  const [screenStream, setScreenStream] = useState<MediaStream | null>(null);
  const [peerConnections] = useState<Map<string, PeerConnection>>(new Map());
  
  const { socket } = useWebSocket();
  const { user } = useAuth();

  const handleMediaError = (error: Error) => {
    setError({
      name: error.name,
      message: error.message
    });
    console.error('Media error:', error);
  };

  const startLocalStream = async () => {
    try {
      setError(null);
      const stream = await navigator.mediaDevices.getUserMedia({
        video: true,
        audio: true,
      });
      setLocalStream(stream);
      setIsAudioEnabled(true);
      setIsVideoEnabled(true);
    } catch (err) {
      handleMediaError(err instanceof Error ? err : new Error('Failed to access media devices'));
      throw err;
    }
  };

  const stopLocalStream = useCallback(() => {
    if (localStream) {
      localStream.getTracks().forEach(track => track.stop());
      setLocalStream(null);
      setIsAudioEnabled(false);
      setIsVideoEnabled(false);
    }
  }, [localStream]);

  const toggleAudio = useCallback(() => {
    if (localStream) {
      const audioTrack = localStream.getAudioTracks()[0];
      if (audioTrack) {
        audioTrack.enabled = !audioTrack.enabled;
        setIsAudioEnabled(audioTrack.enabled);
      }
    }
  }, [localStream]);

  const toggleVideo = useCallback(() => {
    if (localStream) {
      const videoTrack = localStream.getVideoTracks()[0];
      if (videoTrack) {
        videoTrack.enabled = !videoTrack.enabled;
        setIsVideoEnabled(videoTrack.enabled);
      }
    }
  }, [localStream]);

  const startScreenShare = async () => {
    try {
      setError(null);
      const stream = await navigator.mediaDevices.getDisplayMedia({
        video: true,
        audio: true
      });
      
      setScreenStream(stream);
      setIsScreenSharing(true);

      // Handle when user stops sharing via browser UI
      stream.getVideoTracks()[0].onended = () => {
        stopScreenShare();
      };

      return stream;
    } catch (err) {
      handleMediaError(err instanceof Error ? err : new Error('Failed to start screen sharing'));
      throw err;
    }
  };

  const stopScreenShare = useCallback(() => {
    if (screenStream) {
      screenStream.getTracks().forEach(track => track.stop());
      setScreenStream(null);
      setIsScreenSharing(false);
    }
  }, [screenStream]);

  // Clean up when component unmounts
  useEffect(() => {
    return () => {
      stopLocalStream();
      stopScreenShare();
      peerConnections.forEach(peer => {
        peer.connection.close();
      });
    };
  }, [stopLocalStream, stopScreenShare, peerConnections]);

  return (
    <WebRTCContext.Provider
      value={{
        localStream,
        remoteStreams,
        error,
        startLocalStream,
        stopLocalStream,
        toggleAudio,
        toggleVideo,
        startScreenShare,
        stopScreenShare,
        isAudioEnabled,
        isVideoEnabled,
        isScreenSharing,
      }}
    >
      {children}
    </WebRTCContext.Provider>
  );
}; 