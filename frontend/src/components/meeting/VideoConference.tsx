import React, { useEffect, useRef, useState } from 'react';
import SimplePeer from 'simple-peer';
import { useWebSocket } from '@/contexts/WebSocketContext';
import { useAuth } from '@/contexts/AuthContext';

interface Peer {
  userId: string;
  stream: MediaStream;
  peer: SimplePeer.Instance;
}

interface VideoConferenceProps {
  roomId: string;
}

interface UserConnectedEvent {
  userId: string;
}

interface UserDisconnectedEvent {
  userId: string;
}

interface SignalEvent {
  userId: string;
  signal: SimplePeer.SignalData;
}

export default function VideoConference({ roomId }: VideoConferenceProps) {
  const { socket, isConnected } = useWebSocket();
  const { user } = useAuth();
  const [peers, setPeers] = useState<Map<string, Peer>>(new Map());
  const [localStream, setLocalStream] = useState<MediaStream | null>(null);
  const [isMuted, setIsMuted] = useState(false);
  const [isVideoOff, setIsVideoOff] = useState(false);
  const localVideoRef = useRef<HTMLVideoElement>(null);

  // Initialize local media stream
  useEffect(() => {
    const initializeMedia = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: true,
          audio: true
        });
        setLocalStream(stream);
        if (localVideoRef.current) {
          localVideoRef.current.srcObject = stream;
        }
      } catch (err) {
        console.error('Failed to get media devices:', err);
      }
    };

    initializeMedia();

    return () => {
      localStream?.getTracks().forEach((track: MediaStreamTrack) => track.stop());
    };
  }, []);

  // Handle socket events
  useEffect(() => {
    if (!socket || !isConnected || !localStream) return;

    // Join the room
    socket.emit('join-room', { roomId });

    // Handle new user connections
    socket.on('user-connected', ({ userId }: UserConnectedEvent) => {
      if (userId === user?.id?.toString()) return;
      
      const peer = createPeer(userId, localStream);
      setPeers((prev: Map<string, Peer>) => new Map(prev).set(userId, {
        userId,
        stream: localStream,
        peer
      }));
    });

    // Handle user disconnections
    socket.on('user-disconnected', ({ userId }: UserDisconnectedEvent) => {
      if (peers.has(userId)) {
        peers.get(userId)?.peer.destroy();
        const newPeers = new Map(peers);
        newPeers.delete(userId);
        setPeers(newPeers);
      }
    });

    // Handle incoming signals
    socket.on('signal', ({ userId, signal }: SignalEvent) => {
      const peer = peers.get(userId)?.peer;
      if (peer) {
        peer.signal(signal);
      }
    });

    return () => {
      socket.off('user-connected');
      socket.off('user-disconnected');
      socket.off('signal');
      peers.forEach((peer: Peer) => peer.peer.destroy());
    };
  }, [socket, isConnected, localStream, roomId, user?.id]);

  // Create a new peer connection
  const createPeer = (userId: string, stream: MediaStream): SimplePeer.Instance => {
    const peer = new SimplePeer({
      initiator: true,
      trickle: false,
      stream
    });

    peer.on('signal', (signal: SimplePeer.SignalData) => {
      socket?.emit('signal', { userId, signal });
    });

    peer.on('stream', (remoteStream: MediaStream) => {
      setPeers((prev: Map<string, Peer>) => {
        const newPeers = new Map(prev);
        const peerData = newPeers.get(userId);
        if (peerData) {
          newPeers.set(userId, {
            ...peerData,
            stream: remoteStream
          });
        }
        return newPeers;
      });
    });

    return peer;
  };

  // Toggle audio
  const toggleAudio = () => {
    if (localStream) {
      localStream.getAudioTracks().forEach((track: MediaStreamTrack) => {
        track.enabled = !track.enabled;
      });
      setIsMuted(!isMuted);
    }
  };

  // Toggle video
  const toggleVideo = () => {
    if (localStream) {
      localStream.getVideoTracks().forEach((track: MediaStreamTrack) => {
        track.enabled = !track.enabled;
      });
      setIsVideoOff(!isVideoOff);
    }
  };

  return (
    <div className="h-full flex flex-col">
      {/* Controls */}
      <div className="bg-gray-800 p-4 flex items-center justify-center space-x-4">
        <button
          onClick={toggleAudio}
          className={`p-2 rounded-full ${isMuted ? 'bg-red-500' : 'bg-gray-600'}`}
        >
          {isMuted ? 'Unmute' : 'Mute'}
        </button>
        <button
          onClick={toggleVideo}
          className={`p-2 rounded-full ${isVideoOff ? 'bg-red-500' : 'bg-gray-600'}`}
        >
          {isVideoOff ? 'Start Video' : 'Stop Video'}
        </button>
      </div>

      {/* Video Grid */}
      <div className="flex-1 grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 p-4">
        {/* Local Video */}
        <div className="relative aspect-video bg-gray-900 rounded-lg overflow-hidden">
          <video
            ref={localVideoRef}
            autoPlay
            playsInline
            muted
            className="w-full h-full object-cover"
          />
          <div className="absolute bottom-2 left-2 text-white text-sm bg-black bg-opacity-50 px-2 py-1 rounded">
            You
          </div>
        </div>

        {/* Remote Videos */}
        {Array.from(peers.values()).map((peer: Peer) => (
          <div key={peer.userId} className="relative aspect-video bg-gray-900 rounded-lg overflow-hidden">
            <video
              autoPlay
              playsInline
              ref={(video: HTMLVideoElement | null) => {
                if (video) video.srcObject = peer.stream;
              }}
              className="w-full h-full object-cover"
            />
            <div className="absolute bottom-2 left-2 text-white text-sm bg-black bg-opacity-50 px-2 py-1 rounded">
              User {peer.userId}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
} 