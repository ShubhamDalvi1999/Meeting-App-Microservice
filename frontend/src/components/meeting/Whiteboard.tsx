import React, { useEffect, useRef, useState } from 'react';
import { useWebSocket } from '@/contexts/WebSocketContext';

interface WhiteboardProps {
  roomId?: string;
}

interface DrawData {
  type: 'start' | 'draw' | 'end';
  x: number;
  y: number;
  color: string;
  width: number;
}

export default function Whiteboard({ roomId }: WhiteboardProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const contextRef = useRef<CanvasRenderingContext2D | null>(null);
  const { socket, isConnected, sendWhiteboardUpdate } = useWebSocket();
  const [isDrawing, setIsDrawing] = useState(false);
  const [color, setColor] = useState('#000000');
  const [lineWidth, setLineWidth] = useState(2);

  // Initialize canvas
  useEffect(() => {
    if (!canvasRef.current) return;

    const canvas = canvasRef.current;
    const context = canvas.getContext('2d');
    if (!context) return;

    // Set canvas size
    const parent = canvas.parentElement;
    if (parent) {
      canvas.width = parent.clientWidth;
      canvas.height = parent.clientHeight;
    }

    // Configure context
    context.lineCap = 'round';
    context.strokeStyle = color;
    context.lineWidth = lineWidth;
    contextRef.current = context;

    // Handle window resize
    const handleResize = () => {
      if (parent) {
        const imageData = context.getImageData(0, 0, canvas.width, canvas.height);
        canvas.width = parent.clientWidth;
        canvas.height = parent.clientHeight;
        context.putImageData(imageData, 0, 0);
        context.lineCap = 'round';
        context.strokeStyle = color;
        context.lineWidth = lineWidth;
      }
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [color, lineWidth]);

  // Handle whiteboard updates from other users
  useEffect(() => {
    if (!socket || !isConnected || !roomId || !contextRef.current) return;

    const handleWhiteboardUpdate = ({ data }: { data: DrawData }) => {
      const context = contextRef.current;
      if (!context) return;

      context.strokeStyle = data.color;
      context.lineWidth = data.width;

      switch (data.type) {
        case 'start':
          context.beginPath();
          context.moveTo(data.x, data.y);
          break;
        case 'draw':
          context.lineTo(data.x, data.y);
          context.stroke();
          break;
        case 'end':
          context.closePath();
          break;
      }

      // Reset to current user's settings
      context.strokeStyle = color;
      context.lineWidth = lineWidth;
    };

    socket.on('whiteboard-update', handleWhiteboardUpdate);

    return () => {
      socket.off('whiteboard-update', handleWhiteboardUpdate);
    };
  }, [socket, isConnected, roomId, color, lineWidth]);

  const startDrawing = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!contextRef.current || !roomId) return;

    const { offsetX, offsetY } = e.nativeEvent;
    contextRef.current.beginPath();
    contextRef.current.moveTo(offsetX, offsetY);
    setIsDrawing(true);

    sendWhiteboardUpdate(roomId, {
      type: 'start',
      x: offsetX,
      y: offsetY,
      color,
      width: lineWidth,
    });
  };

  const draw = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDrawing || !contextRef.current || !roomId) return;

    const { offsetX, offsetY } = e.nativeEvent;
    contextRef.current.lineTo(offsetX, offsetY);
    contextRef.current.stroke();

    sendWhiteboardUpdate(roomId, {
      type: 'draw',
      x: offsetX,
      y: offsetY,
      color,
      width: lineWidth,
    });
  };

  const stopDrawing = () => {
    if (!contextRef.current || !roomId) return;

    contextRef.current.closePath();
    setIsDrawing(false);

    sendWhiteboardUpdate(roomId, {
      type: 'end',
      x: 0,
      y: 0,
      color,
      width: lineWidth,
    });
  };

  const clearCanvas = () => {
    if (!canvasRef.current || !contextRef.current) return;

    const canvas = canvasRef.current;
    const context = contextRef.current;
    context.clearRect(0, 0, canvas.width, canvas.height);
  };

  return (
    <div className="flex flex-col h-full">
      {/* Controls */}
      <div className="p-4 border-b flex items-center space-x-4">
        <input
          type="color"
          value={color}
          onChange={(e) => setColor(e.target.value)}
          className="w-8 h-8 rounded-full"
        />
        <select
          value={lineWidth}
          onChange={(e) => setLineWidth(Number(e.target.value))}
          className="border rounded px-2 py-1"
        >
          <option value="2">Thin</option>
          <option value="4">Medium</option>
          <option value="6">Thick</option>
        </select>
        <button
          onClick={clearCanvas}
          className="px-4 py-1 bg-red-500 text-white rounded hover:bg-red-600"
        >
          Clear
        </button>
      </div>

      {/* Canvas */}
      <div className="flex-1 relative">
        <canvas
          ref={canvasRef}
          onMouseDown={startDrawing}
          onMouseMove={draw}
          onMouseUp={stopDrawing}
          onMouseLeave={stopDrawing}
          className="absolute inset-0 bg-white cursor-crosshair"
        />
      </div>
    </div>
  );
} 