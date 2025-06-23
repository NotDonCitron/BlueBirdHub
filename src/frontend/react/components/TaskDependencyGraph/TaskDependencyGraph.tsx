import React, { useState, useEffect, useRef } from 'react';
import { makeApiRequest } from '../../lib/api';
import './TaskDependencyGraph.css';

interface Node {
  id: string;
  type: 'current' | 'dependency' | 'blocked';
  x?: number;
  y?: number;
  title?: string;
  status?: string;
}

interface Edge {
  from: string;
  to: string;
  type: 'blocks' | 'depends';
}

interface DependencyGraphProps {
  taskId: string;
  onTaskSelect?: (taskId: string) => void;
  interactive?: boolean;
}

const TaskDependencyGraph: React.FC<DependencyGraphProps> = ({
  taskId,
  onTaskSelect,
  interactive = true
}) => {
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (taskId) {
      loadDependencyGraph();
    }
  }, [taskId]);

  useEffect(() => {
    if (nodes.length > 0) {
      calculateLayout();
      drawGraph();
    }
  }, [nodes, edges, selectedNode]);

  const loadDependencyGraph = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await makeApiRequest(`/tasks/${taskId}/dependencies`, 'GET');
      
      // Get task details for better visualization
      const taskDetails = await makeApiRequest(`/tasks/taskmaster/all`, 'GET');
      const taskMap = new Map(taskDetails.tasks.map((t: any) => [t.id, t]));
      
      const graphNodes: Node[] = response.dependency_graph.nodes.map((node: any) => ({
        ...node,
        title: taskMap.get(node.id)?.title || node.id,
        status: taskMap.get(node.id)?.status || 'unknown'
      }));
      
      // Add blocked tasks
      response.blocked_tasks.forEach((blockedId: string) => {
        if (!graphNodes.find(n => n.id === blockedId)) {
          graphNodes.push({
            id: blockedId,
            type: 'blocked',
            title: taskMap.get(blockedId)?.title || blockedId,
            status: taskMap.get(blockedId)?.status || 'unknown'
          });
        }
      });
      
      setNodes(graphNodes);
      setEdges(response.dependency_graph.edges);
      
    } catch (err: any) {
      setError(err.message || 'Failed to load dependency graph');
    } finally {
      setLoading(false);
    }
  };

  const calculateLayout = () => {
    const canvas = canvasRef.current;
    if (!canvas || nodes.length === 0) return;

    const width = canvas.width;
    const height = canvas.height;
    const centerX = width / 2;
    const centerY = height / 2;

    // Force-directed layout simulation
    const updatedNodes = [...nodes];
    
    // Initialize positions
    updatedNodes.forEach((node, index) => {
      if (!node.x || !node.y) {
        if (node.type === 'current') {
          node.x = centerX;
          node.y = centerY;
        } else {
          const angle = (index / updatedNodes.length) * 2 * Math.PI;
          const radius = 120;
          node.x = centerX + Math.cos(angle) * radius;
          node.y = centerY + Math.sin(angle) * radius;
        }
      }
    });

    // Simple force simulation
    for (let iteration = 0; iteration < 50; iteration++) {
      // Repulsion between nodes
      for (let i = 0; i < updatedNodes.length; i++) {
        for (let j = i + 1; j < updatedNodes.length; j++) {
          const nodeA = updatedNodes[i];
          const nodeB = updatedNodes[j];
          
          const dx = nodeA.x! - nodeB.x!;
          const dy = nodeA.y! - nodeB.y!;
          const distance = Math.sqrt(dx * dx + dy * dy);
          
          if (distance < 100) {
            const force = (100 - distance) / distance * 0.1;
            const fx = dx * force;
            const fy = dy * force;
            
            nodeA.x! += fx;
            nodeA.y! += fy;
            nodeB.x! -= fx;
            nodeB.y! -= fy;
          }
        }
      }

      // Attraction along edges
      edges.forEach(edge => {
        const fromNode = updatedNodes.find(n => n.id === edge.from);
        const toNode = updatedNodes.find(n => n.id === edge.to);
        
        if (fromNode && toNode) {
          const dx = toNode.x! - fromNode.x!;
          const dy = toNode.y! - fromNode.y!;
          const distance = Math.sqrt(dx * dx + dy * dy);
          const targetDistance = 150;
          
          if (distance > targetDistance) {
            const force = (distance - targetDistance) / distance * 0.1;
            const fx = dx * force;
            const fy = dy * force;
            
            fromNode.x! += fx;
            fromNode.y! += fy;
            toNode.x! -= fx;
            toNode.y! -= fy;
          }
        }
      });

      // Keep nodes within bounds
      updatedNodes.forEach(node => {
        node.x = Math.max(50, Math.min(width - 50, node.x!));
        node.y = Math.max(50, Math.min(height - 50, node.y!));
      });
    }

    setNodes(updatedNodes);
  };

  const drawGraph = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw edges
    edges.forEach(edge => {
      const fromNode = nodes.find(n => n.id === edge.from);
      const toNode = nodes.find(n => n.id === edge.to);
      
      if (fromNode && toNode && fromNode.x && fromNode.y && toNode.x && toNode.y) {
        drawEdge(ctx, fromNode, toNode, edge.type);
      }
    });

    // Draw nodes
    nodes.forEach(node => {
      if (node.x && node.y) {
        drawNode(ctx, node);
      }
    });
  };

  const drawEdge = (ctx: CanvasRenderingContext2D, from: Node, to: Node, type: string) => {
    const startX = from.x!;
    const startY = from.y!;
    const endX = to.x!;
    const endY = to.y!;

    // Calculate arrow position (stop at node edge)
    const dx = endX - startX;
    const dy = endY - startY;
    const length = Math.sqrt(dx * dx + dy * dy);
    const nodeRadius = 30;
    
    const adjustedEndX = endX - (dx / length) * nodeRadius;
    const adjustedEndY = endY - (dy / length) * nodeRadius;
    const adjustedStartX = startX + (dx / length) * nodeRadius;
    const adjustedStartY = startY + (dy / length) * nodeRadius;

    // Draw line
    ctx.strokeStyle = type === 'blocks' ? '#ef4444' : '#3b82f6';
    ctx.lineWidth = 2;
    ctx.setLineDash(type === 'blocks' ? [5, 5] : []);
    
    ctx.beginPath();
    ctx.moveTo(adjustedStartX, adjustedStartY);
    ctx.lineTo(adjustedEndX, adjustedEndY);
    ctx.stroke();

    // Draw arrow
    const arrowLength = 12;
    const arrowAngle = Math.PI / 6;
    const angle = Math.atan2(dy, dx);
    
    ctx.fillStyle = ctx.strokeStyle;
    ctx.beginPath();
    ctx.moveTo(adjustedEndX, adjustedEndY);
    ctx.lineTo(
      adjustedEndX - arrowLength * Math.cos(angle - arrowAngle),
      adjustedEndY - arrowLength * Math.sin(angle - arrowAngle)
    );
    ctx.lineTo(
      adjustedEndX - arrowLength * Math.cos(angle + arrowAngle),
      adjustedEndY - arrowLength * Math.sin(angle + arrowAngle)
    );
    ctx.closePath();
    ctx.fill();

    ctx.setLineDash([]);
  };

  const drawNode = (ctx: CanvasRenderingContext2D, node: Node) => {
    const x = node.x!;
    const y = node.y!;
    const radius = 30;
    const isSelected = selectedNode === node.id;

    // Node colors based on type and status
    let fillColor = '#e2e8f0';
    let borderColor = '#94a3b8';
    
    if (node.type === 'current') {
      fillColor = '#3b82f6';
      borderColor = '#1d4ed8';
    } else if (node.type === 'dependency') {
      fillColor = '#f59e0b';
      borderColor = '#d97706';
    } else if (node.type === 'blocked') {
      fillColor = '#ef4444';
      borderColor = '#dc2626';
    }

    // Status-based modifications
    if (node.status === 'done') {
      fillColor = '#10b981';
      borderColor = '#059669';
    } else if (node.status === 'in-progress') {
      fillColor = '#8b5cf6';
      borderColor = '#7c3aed';
    }

    // Draw node
    ctx.fillStyle = fillColor;
    ctx.strokeStyle = isSelected ? '#fbbf24' : borderColor;
    ctx.lineWidth = isSelected ? 4 : 2;
    
    ctx.beginPath();
    ctx.arc(x, y, radius, 0, 2 * Math.PI);
    ctx.fill();
    ctx.stroke();

    // Draw node text
    ctx.fillStyle = node.type === 'current' || node.status === 'done' ? 'white' : '#1e293b';
    ctx.font = 'bold 12px Inter, sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    
    const text = node.title || node.id;
    const maxWidth = radius * 1.5;
    
    if (ctx.measureText(text).width > maxWidth) {
      ctx.fillText(text.substring(0, 8) + '...', x, y);
    } else {
      ctx.fillText(text, x, y);
    }

    // Draw status indicator
    if (node.status === 'done') {
      ctx.fillStyle = 'white';
      ctx.font = '16px Inter, sans-serif';
      ctx.fillText('✓', x + radius - 8, y - radius + 8);
    }
  };

  const handleCanvasClick = (event: React.MouseEvent<HTMLCanvasElement>) => {
    if (!interactive) return;

    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    // Find clicked node
    const clickedNode = nodes.find(node => {
      if (!node.x || !node.y) return false;
      const distance = Math.sqrt((x - node.x) ** 2 + (y - node.y) ** 2);
      return distance <= 30;
    });

    if (clickedNode) {
      setSelectedNode(clickedNode.id);
      onTaskSelect?.(clickedNode.id);
    } else {
      setSelectedNode(null);
    }
  };

  const addDependency = async (dependencyId: string) => {
    try {
      const currentDeps = nodes
        .filter(n => n.type === 'dependency')
        .map(n => n.id);
      
      await makeApiRequest(`/tasks/${taskId}/dependencies`, 'PUT', {
        dependencies: [...currentDeps, dependencyId]
      });
      
      await loadDependencyGraph();
    } catch (err: any) {
      setError(`Failed to add dependency: ${err.message}`);
    }
  };

  if (loading) {
    return (
      <div className="dependency-graph loading">
        <div className="loading-spinner"></div>
        <p>Loading dependency graph...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="dependency-graph error">
        <p>Error: {error}</p>
        <button onClick={loadDependencyGraph}>Retry</button>
      </div>
    );
  }

  return (
    <div className="dependency-graph" ref={containerRef}>
      <div className="graph-header">
        <h3>Task Dependencies</h3>
        <div className="graph-legend">
          <div className="legend-item">
            <div className="legend-color current"></div>
            <span>Current Task</span>
          </div>
          <div className="legend-item">
            <div className="legend-color dependency"></div>
            <span>Dependencies</span>
          </div>
          <div className="legend-item">
            <div className="legend-color blocked"></div>
            <span>Blocked Tasks</span>
          </div>
        </div>
      </div>
      
      <canvas
        ref={canvasRef}
        width={600}
        height={400}
        className="dependency-canvas"
        onClick={handleCanvasClick}
      />
      
      {selectedNode && (
        <div className="node-info">
          <h4>Selected: {nodes.find(n => n.id === selectedNode)?.title}</h4>
          <p>ID: {selectedNode}</p>
          <p>Status: {nodes.find(n => n.id === selectedNode)?.status}</p>
          <button onClick={() => onTaskSelect?.(selectedNode)}>
            View Task Details
          </button>
        </div>
      )}
    </div>
  );
};

export default TaskDependencyGraph;