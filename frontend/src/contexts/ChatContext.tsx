import React, { createContext, useContext, useEffect, useState } from 'react';
import { useWebSocket } from './WebSocketContext';

interface Message {
  id: string;
  userId: string;
  message: string;
  type: 'text' | 'file';
  fileUrl?: string;
  fileType?: string;
  fileSize?: number;
  timestamp: string;
  reactions?: Record<string, Set<string>>;
}

interface ChatContextType {
  messages: Message[];
  sendMessage: (message: string) => void;
  sendFile: (file: File) => Promise<void>;
  addReaction: (messageId: string, reaction: string) => void;
  isTyping: boolean;
  setIsTyping: (typing: boolean) => void;
  typingUsers: Set<string>;
}

interface UserTypingEvent {
  userId: string;
  isTyping: boolean;
}

interface MessageReactionEvent {
  messageId: string;
  reaction: string;
  userId: string;
  count: number;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export function ChatProvider({ children }: { children: React.ReactNode }) {
  const { socket } = useWebSocket();
  const [messages, setMessages] = useState<Message[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const [typingUsers, setTypingUsers] = useState<Set<string>>(new Set());
  const [typingTimeout, setTypingTimeout] = useState<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (!socket) return;

    socket.on('chat_message', (message: Message) => {
      const messageWithUTC = {
        ...message,
        timestamp: new Date(message.timestamp).toISOString()
      };
      setMessages((prev: Message[]) => [...prev, messageWithUTC]);
    });

    socket.on('user_typing', ({ userId, isTyping }: UserTypingEvent) => {
      setTypingUsers((prev: Set<string>) => {
        const newSet = new Set(prev);
        if (isTyping) {
          newSet.add(userId);
        } else {
          newSet.delete(userId);
        }
        return newSet;
      });
    });

    socket.on('message_reaction', ({ messageId, reaction, userId, count }: MessageReactionEvent) => {
      setMessages((prev: Message[]) => {
        return prev.map((msg: Message) => {
          if (msg.id === messageId) {
            return {
              ...msg,
              reactions: {
                ...msg.reactions,
                [reaction]: new Set([...Array.from(msg.reactions?.[reaction] || []), userId])
              }
            };
          }
          return msg;
        });
      });
    });

    return () => {
      socket.off('chat_message');
      socket.off('user_typing');
      socket.off('message_reaction');
    };
  }, [socket]);

  const sendMessage = (message: string) => {
    if (!socket) return;
    socket.emit('chat_message', { message });
  };

  const sendFile = async (file: File) => {
    if (!socket) return;

    // Convert file to base64
    const reader = new FileReader();
    reader.readAsDataURL(file);

    reader.onload = () => {
      const base64 = reader.result as string;
      socket.emit('chat_message', {
        message: file.name,
        type: 'file',
        fileData: {
          name: file.name,
          type: file.type,
          size: file.size,
          url: base64
        }
      });
    };
  };

  const addReaction = (messageId: string, reaction: string) => {
    if (!socket) return;
    socket.emit('message_reaction', { messageId, reaction });
  };

  // Handle typing status
  useEffect(() => {
    if (!socket || !isTyping) return;

    socket.emit('user_typing', { isTyping: true });

    if (typingTimeout) {
      clearTimeout(typingTimeout);
    }

    const timeout = setTimeout(() => {
      socket.emit('user_typing', { isTyping: false });
      setIsTyping(false);
    }, 3000);

    setTypingTimeout(timeout);

    return () => {
      if (typingTimeout) {
        clearTimeout(typingTimeout);
      }
    };
  }, [isTyping, socket]);

  return (
    <ChatContext.Provider
      value={{
        messages,
        sendMessage,
        sendFile,
        addReaction,
        isTyping,
        setIsTyping,
        typingUsers
      }}
    >
      {children}
    </ChatContext.Provider>
  );
}

export function useChat() {
  const context = useContext(ChatContext);
  if (context === undefined) {
    throw new Error('useChat must be used within a ChatProvider');
  }
  return context;
} 