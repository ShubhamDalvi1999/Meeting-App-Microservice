import React, { createContext, useContext, useEffect, useRef, useState, useCallback } from 'react';
import { fabric } from 'fabric';
import { useWebSocket } from './WebSocketContext';

interface Point {
  x: number;
  y: number;
}

interface DrawingPath {
  points: Point[];
  color: string;
  width: number;
  type: 'brush' | 'eraser';
}

interface DrawingObject {
  type: string;
  options: fabric.IObjectOptions & {
    path?: DrawingPath;
    points?: Point[];
    radius?: number;
    width?: number;
    height?: number;
    text?: string;
  };
}

interface CanvasState {
  version: string;
  objects: DrawingObject[];
  background?: string;
}

interface WhiteboardState {
  objects: DrawingObject[];
  background: string;
  dimensions: {
    width: number;
    height: number;
  };
}

interface WhiteboardContextType {
  canvas: fabric.Canvas | null;
  currentColor: string;
  setCurrentColor: (color: string) => void;
  currentBrushSize: number;
  setCurrentBrushSize: (size: number) => void;
  clearCanvas: () => void;
  undo: () => void;
  redo: () => void;
  addText: (text: string) => void;
  addShape: (type: 'rectangle' | 'circle' | 'line') => void;
  setMode: (mode: 'draw' | 'erase' | 'select') => void;
  currentMode: string;
  canUndo: boolean;
  canRedo: boolean;
  saveState: () => WhiteboardState;
  loadState: (state: WhiteboardState) => void;
}

const WhiteboardContext = createContext<WhiteboardContextType | undefined>(undefined);

export function WhiteboardProvider({ children }: { children: React.ReactNode }) {
  const { socket } = useWebSocket();
  const [canvas, setCanvas] = useState<fabric.Canvas | null>(null);
  const [currentColor, setCurrentColor] = useState('#000000');
  const [currentBrushSize, setCurrentBrushSize] = useState(2);
  const [currentMode, setCurrentMode] = useState<string>('draw');
  const [canUndo, setCanUndo] = useState(false);
  const [canRedo, setCanRedo] = useState(false);
  
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const historyRef = useRef<CanvasState[]>([]);
  const redoHistoryRef = useRef<CanvasState[]>([]);

  useEffect(() => {
    if (!canvasRef.current) return;

    const newCanvas = new fabric.Canvas(canvasRef.current, {
      isDrawingMode: true,
      width: window.innerWidth * 0.8,
      height: window.innerHeight * 0.8,
      backgroundColor: '#ffffff'
    });

    newCanvas.freeDrawingBrush.color = currentColor;
    newCanvas.freeDrawingBrush.width = currentBrushSize;

    newCanvas.on('object:added', () => {
      const state = canvas?.toJSON() as CanvasState;
      if (state) {
        historyRef.current.push(state);
        redoHistoryRef.current = [];
        updateUndoRedoState();
      }
    });

    setCanvas(newCanvas);

    const handleResize = () => {
      newCanvas.setDimensions({
        width: window.innerWidth * 0.8,
        height: window.innerHeight * 0.8
      });
      newCanvas.renderAll();
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      newCanvas.dispose();
    };
  }, []);

  const updateUndoRedoState = useCallback(() => {
    setCanUndo(historyRef.current.length > 0);
    setCanRedo(redoHistoryRef.current.length > 0);
  }, []);

  const setMode = useCallback((mode: 'draw' | 'erase' | 'select') => {
    if (!canvas) return;

    setCurrentMode(mode);
    canvas.isDrawingMode = mode === 'draw';

    if (mode === 'erase') {
      canvas.freeDrawingBrush = new fabric.EraseBrush(canvas);
    } else if (mode === 'draw') {
      canvas.freeDrawingBrush = new fabric.PencilBrush(canvas);
      canvas.freeDrawingBrush.color = currentColor;
      canvas.freeDrawingBrush.width = currentBrushSize;
    }

    canvas.selection = mode === 'select';
    canvas.renderAll();
  }, [canvas, currentColor, currentBrushSize]);

  const clearCanvas = useCallback(() => {
    if (!canvas) return;
    
    canvas.clear();
    canvas.backgroundColor = '#ffffff';
    canvas.renderAll();
    
    // Save state for undo
    const state = canvas.toJSON() as CanvasState;
    if (state) {
      historyRef.current.push(state);
      updateUndoRedoState();
    }

    // Emit clear event
    socket?.emit('whiteboard-clear');
  }, [canvas, socket, updateUndoRedoState]);

  const undo = useCallback(() => {
    if (!canvas || historyRef.current.length === 0) return;

    const currentState = canvas.toJSON() as CanvasState;
    redoHistoryRef.current.push(currentState);
    
    const previousState = historyRef.current.pop();
    if (previousState) {
      canvas.loadFromJSON(previousState, () => {
        canvas.renderAll();
        updateUndoRedoState();
      });
    }
  }, [canvas, updateUndoRedoState]);

  const redo = useCallback(() => {
    if (!canvas || redoHistoryRef.current.length === 0) return;

    const currentState = canvas.toJSON() as CanvasState;
    historyRef.current.push(currentState);
    
    const nextState = redoHistoryRef.current.pop();
    if (nextState) {
      canvas.loadFromJSON(nextState, () => {
        canvas.renderAll();
        updateUndoRedoState();
      });
    }
  }, [canvas, updateUndoRedoState]);

  const addText = useCallback((text: string) => {
    if (!canvas) return;

    const textObject = new fabric.IText(text, {
      left: canvas.width! / 2,
      top: canvas.height! / 2,
      fontSize: 20,
      fill: currentColor
    });

    canvas.add(textObject);
    canvas.setActiveObject(textObject);
    canvas.renderAll();
  }, [canvas, currentColor]);

  const addShape = useCallback((type: 'rectangle' | 'circle' | 'line') => {
    if (!canvas) return;

    let shape: fabric.Object;

    switch (type) {
      case 'rectangle':
        shape = new fabric.Rect({
          left: canvas.width! / 2 - 25,
          top: canvas.height! / 2 - 25,
          width: 50,
          height: 50,
          fill: 'transparent',
          stroke: currentColor,
          strokeWidth: 2
        });
        break;
      case 'circle':
        shape = new fabric.Circle({
          left: canvas.width! / 2 - 25,
          top: canvas.height! / 2 - 25,
          radius: 25,
          fill: 'transparent',
          stroke: currentColor,
          strokeWidth: 2
        });
        break;
      case 'line':
        shape = new fabric.Line([50, 50, 200, 50], {
          left: canvas.width! / 2 - 75,
          top: canvas.height! / 2,
          stroke: currentColor,
          strokeWidth: 2
        });
        break;
      default:
        return;
    }

    canvas.add(shape);
    canvas.setActiveObject(shape);
    canvas.renderAll();
  }, [canvas, currentColor]);

  const saveState = useCallback((): WhiteboardState => {
    if (!canvas) {
      return {
        objects: [],
        background: '#ffffff',
        dimensions: { width: 0, height: 0 }
      };
    }

    const state = canvas.toJSON() as CanvasState;
    return {
      objects: state.objects || [],
      background: state.background || '#ffffff',
      dimensions: {
        width: canvas.width!,
        height: canvas.height!
      }
    };
  }, [canvas]);

  const loadState = useCallback((state: WhiteboardState) => {
    if (!canvas) return;

    canvas.clear();
    canvas.backgroundColor = state.background;
    canvas.setDimensions(state.dimensions);

    canvas.loadFromJSON({ objects: state.objects }, () => {
      canvas.renderAll();
      historyRef.current = [canvas.toJSON() as CanvasState];
      redoHistoryRef.current = [];
      updateUndoRedoState();
    });
  }, [canvas, updateUndoRedoState]);

  return (
    <WhiteboardContext.Provider
      value={{
        canvas,
        currentColor,
        setCurrentColor,
        currentBrushSize,
        setCurrentBrushSize,
        clearCanvas,
        undo,
        redo,
        addText,
        addShape,
        setMode,
        currentMode,
        canUndo,
        canRedo,
        saveState,
        loadState
      }}
    >
      {children}
    </WhiteboardContext.Provider>
  );
}

export function useWhiteboard() {
  const context = useContext(WhiteboardContext);
  if (context === undefined) {
    throw new Error('useWhiteboard must be used within a WhiteboardProvider');
  }
  return context;
} 