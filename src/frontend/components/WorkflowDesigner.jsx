/**
 * Visual Workflow Designer Component
 * 
 * Provides a drag-and-drop interface for creating and editing workflows
 * with visual step connections, conditional logic, and real-time validation.
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  DndProvider,
  useDrag,
  useDrop,
  DragDropContext,
  Droppable,
  Draggable
} from 'react-beautiful-dnd';
import { HTML5Backend } from 'react-dnd-html5-backend';
import {
  Box,
  Paper,
  Typography,
  Toolbar,
  IconButton,
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  Tooltip,
  Zoom,
  Fab,
  Grid,
  Card,
  CardContent,
  CardActions,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Tab,
  Tabs,
  TabPanel,
  Switch,
  FormControlLabel,
  Alert,
  Snackbar
} from '@mui/material';
import {
  Add as AddIcon,
  PlayArrow as PlayIcon,
  Save as SaveIcon,
  Undo as UndoIcon,
  Redo as RedoIcon,
  ZoomIn as ZoomInIcon,
  ZoomOut as ZoomOutIcon,
  CenterFocusStrong as CenterIcon,
  Settings as SettingsIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  Link as LinkIcon,
  Schedule as ScheduleIcon,
  Webhook as WebhookIcon,
  Email as EmailIcon,
  Task as TaskIcon,
  Folder as FolderIcon,
  Analytics as AnalyticsIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  ExpandMore as ExpandMoreIcon,
  DragIndicator as DragIcon,
  ContentCopy as CopyIcon,
  Visibility as PreviewIcon
} from '@mui/icons-material';
import { styled } from '@mui/material/styles';
import { v4 as uuidv4 } from 'uuid';

// Styled components
const DesignerContainer = styled(Box)(({ theme }) => ({
  display: 'flex',
  height: '100vh',
  backgroundColor: theme.palette.background.default,
}));

const ToolboxDrawer = styled(Drawer)(({ theme }) => ({
  width: 300,
  flexShrink: 0,
  '& .MuiDrawer-paper': {
    width: 300,
    boxSizing: 'border-box',
    borderRight: `1px solid ${theme.palette.divider}`,
  },
}));

const CanvasContainer = styled(Box)(({ theme }) => ({
  flex: 1,
  display: 'flex',
  flexDirection: 'column',
  overflow: 'hidden',
  position: 'relative',
}));

const Canvas = styled(Box)(({ theme, zoom = 1 }) => ({
  flex: 1,
  position: 'relative',
  overflow: 'auto',
  transform: `scale(${zoom})`,
  transformOrigin: 'top left',
  backgroundImage: `
    radial-gradient(circle, ${theme.palette.action.disabled} 1px, transparent 1px)
  `,
  backgroundSize: '20px 20px',
  cursor: 'grab',
  '&:active': {
    cursor: 'grabbing',
  },
}));

const StepNode = styled(Paper)(({ theme, selected, hasError }) => ({
  position: 'absolute',
  width: 200,
  minHeight: 100,
  padding: theme.spacing(2),
  cursor: 'pointer',
  border: selected 
    ? `2px solid ${theme.palette.primary.main}` 
    : hasError 
    ? `2px solid ${theme.palette.error.main}`
    : `1px solid ${theme.palette.divider}`,
  borderRadius: theme.shape.borderRadius,
  boxShadow: selected 
    ? theme.shadows[8] 
    : theme.shadows[2],
  backgroundColor: theme.palette.background.paper,
  transition: 'all 0.2s ease-in-out',
  '&:hover': {
    boxShadow: theme.shadows[4],
    transform: 'translateY(-2px)',
  },
  '& .step-header': {
    display: 'flex',
    alignItems: 'center',
    marginBottom: theme.spacing(1),
  },
  '& .step-icon': {
    marginRight: theme.spacing(1),
    color: theme.palette.primary.main,
  },
  '& .step-title': {
    fontWeight: 600,
    fontSize: '0.9rem',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
  },
  '& .step-description': {
    fontSize: '0.8rem',
    color: theme.palette.text.secondary,
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    display: '-webkit-box',
    WebkitLineClamp: 2,
    WebkitBoxOrient: 'vertical',
  },
  '& .step-status': {
    position: 'absolute',
    top: 8,
    right: 8,
  },
}));

const ConnectionLine = styled('svg')(({ theme }) => ({
  position: 'absolute',
  top: 0,
  left: 0,
  width: '100%',
  height: '100%',
  pointerEvents: 'none',
  zIndex: 1,
  '& path': {
    stroke: theme.palette.primary.main,
    strokeWidth: 2,
    fill: 'none',
    markerEnd: 'url(#arrowhead)',
  },
  '& .connection-conditional': {
    stroke: theme.palette.warning.main,
    strokeDasharray: '5,5',
  },
  '& .connection-error': {
    stroke: theme.palette.error.main,
  },
}));

const PropertiesPanel = styled(Drawer)(({ theme }) => ({
  width: 350,
  flexShrink: 0,
  '& .MuiDrawer-paper': {
    width: 350,
    boxSizing: 'border-box',
    borderLeft: `1px solid ${theme.palette.divider}`,
  },
}));

const ZoomControls = styled(Box)(({ theme }) => ({
  position: 'absolute',
  bottom: 20,
  right: 20,
  display: 'flex',
  flexDirection: 'column',
  gap: theme.spacing(1),
  zIndex: 1000,
}));

// Step types configuration
const STEP_TYPES = {
  CREATE_TASK: {
    icon: <TaskIcon />,
    label: 'Create Task',
    category: 'Tasks',
    color: '#1976d2',
    description: 'Create a new task'
  },
  UPDATE_TASK: {
    icon: <EditIcon />,
    label: 'Update Task',
    category: 'Tasks',
    color: '#1976d2',
    description: 'Update existing task'
  },
  ASSIGN_TASK: {
    icon: <LinkIcon />,
    label: 'Assign Task',
    category: 'Tasks',
    color: '#1976d2',
    description: 'Assign task to user'
  },
  SEND_EMAIL: {
    icon: <EmailIcon />,
    label: 'Send Email',
    category: 'Communication',
    color: '#f57c00',
    description: 'Send email notification'
  },
  SEND_NOTIFICATION: {
    icon: <WarningIcon />,
    label: 'Send Notification',
    category: 'Communication',
    color: '#f57c00',
    description: 'Send system notification'
  },
  CREATE_WORKSPACE: {
    icon: <FolderIcon />,
    label: 'Create Workspace',
    category: 'Workspaces',
    color: '#388e3c',
    description: 'Create new workspace'
  },
  AI_ANALYSIS: {
    icon: <AnalyticsIcon />,
    label: 'AI Analysis',
    category: 'AI',
    color: '#7b1fa2',
    description: 'Perform AI analysis'
  },
  CONDITIONAL: {
    icon: <WarningIcon />,
    label: 'Condition',
    category: 'Logic',
    color: '#d32f2f',
    description: 'Conditional branching'
  },
  WAIT: {
    icon: <ScheduleIcon />,
    label: 'Wait',
    category: 'Logic',
    color: '#616161',
    description: 'Wait for specified time'
  },
  APPROVAL: {
    icon: <CheckCircleIcon />,
    label: 'Approval',
    category: 'Logic',
    color: '#00796b',
    description: 'Require approval'
  },
  WEBHOOK_CALL: {
    icon: <WebhookIcon />,
    label: 'Webhook',
    category: 'Integration',
    color: '#5d4037',
    description: 'Call external webhook'
  },
};

// Trigger types
const TRIGGER_TYPES = {
  MANUAL: {
    icon: <PlayIcon />,
    label: 'Manual Trigger',
    description: 'Start workflow manually'
  },
  SCHEDULE: {
    icon: <ScheduleIcon />,
    label: 'Scheduled Trigger',
    description: 'Start workflow on schedule'
  },
  WEBHOOK: {
    icon: <WebhookIcon />,
    label: 'Webhook Trigger',
    description: 'Start workflow via webhook'
  },
  EVENT: {
    icon: <WarningIcon />,
    label: 'Event Trigger',
    description: 'Start workflow on system event'
  },
};

// Main WorkflowDesigner component
const WorkflowDesigner = ({ 
  workflowId, 
  onSave, 
  onExecute, 
  readOnly = false,
  initialWorkflow = null 
}) => {
  // State management
  const [workflow, setWorkflow] = useState({
    id: workflowId,
    name: 'New Workflow',
    description: '',
    steps: [],
    triggers: [],
    variables: {},
    config: {}
  });
  
  const [selectedStep, setSelectedStep] = useState(null);
  const [selectedTrigger, setSelectedTrigger] = useState(null);
  const [zoom, setZoom] = useState(1);
  const [canvasOffset, setCanvasOffset] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [connections, setConnections] = useState([]);
  const [isConnecting, setIsConnecting] = useState(false);
  const [connectingFrom, setConnectingFrom] = useState(null);
  const [errors, setErrors] = useState([]);
  const [showPropertiesPanel, setShowPropertiesPanel] = useState(true);
  const [showStepDialog, setShowStepDialog] = useState(false);
  const [showTriggerDialog, setShowTriggerDialog] = useState(false);
  const [editingStep, setEditingStep] = useState(null);
  const [notification, setNotification] = useState({ open: false, message: '', type: 'info' });

  const canvasRef = useRef(null);
  const dragRef = useRef({ isDragging: false, startPos: { x: 0, y: 0 } });

  // Initialize workflow
  useEffect(() => {
    if (initialWorkflow) {
      setWorkflow(initialWorkflow);
      // Calculate connections from step dependencies
      const newConnections = [];
      initialWorkflow.steps.forEach(step => {
        if (step.depends_on && step.depends_on.length > 0) {
          step.depends_on.forEach(depId => {
            newConnections.push({
              from: depId,
              to: step.id,
              type: 'dependency'
            });
          });
        }
      });
      setConnections(newConnections);
    }
  }, [initialWorkflow]);

  // Canvas interaction handlers
  const handleCanvasMouseDown = useCallback((e) => {
    if (e.target === e.currentTarget) {
      setIsDragging(true);
      dragRef.current = {
        isDragging: true,
        startPos: { x: e.clientX - canvasOffset.x, y: e.clientY - canvasOffset.y }
      };
    }
  }, [canvasOffset]);

  const handleCanvasMouseMove = useCallback((e) => {
    if (dragRef.current.isDragging) {
      setCanvasOffset({
        x: e.clientX - dragRef.current.startPos.x,
        y: e.clientY - dragRef.current.startPos.y
      });
    }
  }, []);

  const handleCanvasMouseUp = useCallback(() => {
    setIsDragging(false);
    dragRef.current.isDragging = false;
  }, []);

  // Step management
  const addStep = useCallback((stepType, position = null) => {
    const newStep = {
      id: uuidv4(),
      name: STEP_TYPES[stepType].label,
      description: STEP_TYPES[stepType].description,
      step_type: stepType,
      order: workflow.steps.length + 1,
      config: {},
      input_mapping: {},
      output_mapping: {},
      depends_on: [],
      conditions: [],
      on_error: 'fail',
      retry_count: 0,
      timeout_seconds: 300,
      position_x: position ? position.x : 100 + (workflow.steps.length * 250),
      position_y: position ? position.y : 100 + (Math.floor(workflow.steps.length / 4) * 150),
    };

    setWorkflow(prev => ({
      ...prev,
      steps: [...prev.steps, newStep]
    }));

    return newStep;
  }, [workflow.steps]);

  const updateStep = useCallback((stepId, updates) => {
    setWorkflow(prev => ({
      ...prev,
      steps: prev.steps.map(step => 
        step.id === stepId ? { ...step, ...updates } : step
      )
    }));
  }, []);

  const deleteStep = useCallback((stepId) => {
    setWorkflow(prev => ({
      ...prev,
      steps: prev.steps.filter(step => step.id !== stepId)
    }));
    
    // Remove connections involving this step
    setConnections(prev => 
      prev.filter(conn => conn.from !== stepId && conn.to !== stepId)
    );
    
    if (selectedStep?.id === stepId) {
      setSelectedStep(null);
    }
  }, [selectedStep]);

  // Connection management
  const startConnection = useCallback((stepId) => {
    setIsConnecting(true);
    setConnectingFrom(stepId);
  }, []);

  const completeConnection = useCallback((toStepId) => {
    if (isConnecting && connectingFrom && connectingFrom !== toStepId) {
      // Add dependency
      updateStep(toStepId, {
        depends_on: [...(workflow.steps.find(s => s.id === toStepId)?.depends_on || []), connectingFrom]
      });
      
      // Add visual connection
      setConnections(prev => [...prev, {
        from: connectingFrom,
        to: toStepId,
        type: 'dependency'
      }]);
    }
    
    setIsConnecting(false);
    setConnectingFrom(null);
  }, [isConnecting, connectingFrom, updateStep, workflow.steps]);

  // Validation
  const validateWorkflow = useCallback(() => {
    const newErrors = [];
    
    // Check for circular dependencies
    const checkCircular = (stepId, visited = new Set()) => {
      if (visited.has(stepId)) {
        newErrors.push(`Circular dependency detected involving step ${stepId}`);
        return;
      }
      
      visited.add(stepId);
      const step = workflow.steps.find(s => s.id === stepId);
      if (step?.depends_on) {
        step.depends_on.forEach(depId => checkCircular(depId, new Set(visited)));
      }
    };
    
    workflow.steps.forEach(step => checkCircular(step.id));
    
    // Check for missing required fields
    workflow.steps.forEach(step => {
      if (!step.name.trim()) {
        newErrors.push(`Step ${step.id} is missing a name`);
      }
      if (!step.step_type) {
        newErrors.push(`Step ${step.id} is missing a type`);
      }
    });
    
    setErrors(newErrors);
    return newErrors.length === 0;
  }, [workflow]);

  // Save workflow
  const handleSave = useCallback(async () => {
    if (!validateWorkflow()) {
      setNotification({
        open: true,
        message: 'Please fix validation errors before saving',
        type: 'error'
      });
      return;
    }
    
    try {
      await onSave(workflow);
      setNotification({
        open: true,
        message: 'Workflow saved successfully',
        type: 'success'
      });
    } catch (error) {
      setNotification({
        open: true,
        message: `Failed to save workflow: ${error.message}`,
        type: 'error'
      });
    }
  }, [workflow, validateWorkflow, onSave]);

  // Execute workflow
  const handleExecute = useCallback(async () => {
    if (!validateWorkflow()) {
      setNotification({
        open: true,
        message: 'Please fix validation errors before executing',
        type: 'error'
      });
      return;
    }
    
    try {
      await onExecute(workflow);
      setNotification({
        open: true,
        message: 'Workflow execution started',
        type: 'success'
      });
    } catch (error) {
      setNotification({
        open: true,
        message: `Failed to execute workflow: ${error.message}`,
        type: 'error'
      });
    }
  }, [workflow, validateWorkflow, onExecute]);

  // Zoom controls
  const handleZoomIn = useCallback(() => {
    setZoom(prev => Math.min(prev + 0.1, 2));
  }, []);

  const handleZoomOut = useCallback(() => {
    setZoom(prev => Math.max(prev - 0.1, 0.5));
  }, []);

  const handleZoomReset = useCallback(() => {
    setZoom(1);
    setCanvasOffset({ x: 0, y: 0 });
  }, []);

  return (
    <DndProvider backend={HTML5Backend}>
      <DesignerContainer>
        {/* Toolbox */}
        <ToolboxDrawer variant="permanent">
          <Toolbar>
            <Typography variant="h6">Toolbox</Typography>
          </Toolbar>
          <Divider />
          
          {/* Step Types */}
          <List>
            <ListItem>
              <Typography variant="subtitle2" color="textSecondary">
                WORKFLOW STEPS
              </Typography>
            </ListItem>
            {Object.entries(STEP_TYPES).map(([type, config]) => (
              <DraggableStepType
                key={type}
                type={type}
                config={config}
                onAdd={addStep}
              />
            ))}
          </List>
          
          <Divider />
          
          {/* Triggers */}
          <List>
            <ListItem>
              <Typography variant="subtitle2" color="textSecondary">
                TRIGGERS
              </Typography>
            </ListItem>
            {Object.entries(TRIGGER_TYPES).map(([type, config]) => (
              <ListItem 
                key={type}
                button
                onClick={() => {
                  setSelectedTrigger({ type, ...config });
                  setShowTriggerDialog(true);
                }}
              >
                <ListItemIcon>{config.icon}</ListItemIcon>
                <ListItemText 
                  primary={config.label}
                  secondary={config.description}
                />
              </ListItem>
            ))}
          </List>
        </ToolboxDrawer>

        {/* Main Canvas Area */}
        <CanvasContainer>
          {/* Toolbar */}
          <Toolbar sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <TextField
              value={workflow.name}
              onChange={(e) => setWorkflow(prev => ({ ...prev, name: e.target.value }))}
              variant="outlined"
              size="small"
              sx={{ mr: 2, minWidth: 200 }}
              placeholder="Workflow Name"
              disabled={readOnly}
            />
            
            <Button
              startIcon={<SaveIcon />}
              onClick={handleSave}
              disabled={readOnly}
              sx={{ mr: 1 }}
            >
              Save
            </Button>
            
            <Button
              startIcon={<PlayIcon />}
              onClick={handleExecute}
              variant="contained"
              sx={{ mr: 2 }}
            >
              Execute
            </Button>
            
            <Divider orientation="vertical" flexItem sx={{ mx: 2 }} />
            
            <IconButton onClick={() => {}}>
              <UndoIcon />
            </IconButton>
            <IconButton onClick={() => {}}>
              <RedoIcon />
            </IconButton>
            
            <Box sx={{ flexGrow: 1 }} />
            
            <FormControlLabel
              control={
                <Switch
                  checked={showPropertiesPanel}
                  onChange={(e) => setShowPropertiesPanel(e.target.checked)}
                />
              }
              label="Properties"
            />
            
            {errors.length > 0 && (
              <Chip
                icon={<ErrorIcon />}
                label={`${errors.length} errors`}
                color="error"
                size="small"
                sx={{ ml: 1 }}
              />
            )}
          </Toolbar>

          {/* Canvas */}
          <Canvas
            ref={canvasRef}
            zoom={zoom}
            onMouseDown={handleCanvasMouseDown}
            onMouseMove={handleCanvasMouseMove}
            onMouseUp={handleCanvasMouseUp}
          >
            {/* Connection Lines */}
            <ConnectionLine>
              <defs>
                <marker
                  id="arrowhead"
                  markerWidth="10"
                  markerHeight="7"
                  refX="9"
                  refY="3.5"
                  orient="auto"
                >
                  <polygon points="0 0, 10 3.5, 0 7" fill="currentColor" />
                </marker>
              </defs>
              {connections.map((connection, index) => {
                const fromStep = workflow.steps.find(s => s.id === connection.from);
                const toStep = workflow.steps.find(s => s.id === connection.to);
                
                if (!fromStep || !toStep) return null;
                
                const fromX = fromStep.position_x + 200;
                const fromY = fromStep.position_y + 50;
                const toX = toStep.position_x;
                const toY = toStep.position_y + 50;
                
                const midX = (fromX + toX) / 2;
                
                return (
                  <path
                    key={index}
                    d={`M ${fromX} ${fromY} C ${midX} ${fromY}, ${midX} ${toY}, ${toX} ${toY}`}
                    className={`connection-${connection.type}`}
                  />
                );
              })}
            </ConnectionLine>

            {/* Workflow Steps */}
            {workflow.steps.map((step) => (
              <WorkflowStep
                key={step.id}
                step={step}
                selected={selectedStep?.id === step.id}
                onSelect={setSelectedStep}
                onUpdate={updateStep}
                onDelete={deleteStep}
                onStartConnection={startConnection}
                onCompleteConnection={completeConnection}
                isConnecting={isConnecting}
                readOnly={readOnly}
              />
            ))}
          </Canvas>

          {/* Zoom Controls */}
          <ZoomControls>
            <Fab size="small" onClick={handleZoomIn}>
              <ZoomInIcon />
            </Fab>
            <Fab size="small" onClick={handleZoomOut}>
              <ZoomOutIcon />
            </Fab>
            <Fab size="small" onClick={handleZoomReset}>
              <CenterIcon />
            </Fab>
          </ZoomControls>
        </CanvasContainer>

        {/* Properties Panel */}
        {showPropertiesPanel && (
          <PropertiesPanel variant="permanent" anchor="right">
            <Toolbar>
              <Typography variant="h6">Properties</Typography>
            </Toolbar>
            <Divider />
            
            {selectedStep ? (
              <StepPropertiesPanel
                step={selectedStep}
                onUpdate={updateStep}
                readOnly={readOnly}
              />
            ) : (
              <WorkflowPropertiesPanel
                workflow={workflow}
                onUpdate={setWorkflow}
                readOnly={readOnly}
              />
            )}
          </PropertiesPanel>
        )}

        {/* Dialogs */}
        <StepConfigDialog
          open={showStepDialog}
          onClose={() => setShowStepDialog(false)}
          step={editingStep}
          onSave={(stepConfig) => {
            if (editingStep) {
              updateStep(editingStep.id, stepConfig);
            }
            setShowStepDialog(false);
            setEditingStep(null);
          }}
        />

        <TriggerConfigDialog
          open={showTriggerDialog}
          onClose={() => setShowTriggerDialog(false)}
          trigger={selectedTrigger}
          onSave={(triggerConfig) => {
            setWorkflow(prev => ({
              ...prev,
              triggers: [...prev.triggers, { ...triggerConfig, id: uuidv4() }]
            }));
            setShowTriggerDialog(false);
            setSelectedTrigger(null);
          }}
        />

        {/* Notifications */}
        <Snackbar
          open={notification.open}
          autoHideDuration={4000}
          onClose={() => setNotification({ ...notification, open: false })}
        >
          <Alert 
            severity={notification.type} 
            onClose={() => setNotification({ ...notification, open: false })}
          >
            {notification.message}
          </Alert>
        </Snackbar>
      </DesignerContainer>
    </DndProvider>
  );
};

// Individual workflow step component
const WorkflowStep = ({ 
  step, 
  selected, 
  onSelect, 
  onUpdate, 
  onDelete, 
  onStartConnection,
  onCompleteConnection,
  isConnecting,
  readOnly 
}) => {
  const [{ isDragging }, drag] = useDrag({
    type: 'step',
    item: { id: step.id, type: 'step' },
    collect: (monitor) => ({
      isDragging: monitor.isDragging(),
    }),
  });

  const [, drop] = useDrop({
    accept: 'step',
    drop: (item, monitor) => {
      if (isConnecting && item.id !== step.id) {
        onCompleteConnection(step.id);
      }
    },
  });

  const stepType = STEP_TYPES[step.step_type];
  const hasError = !step.name || !step.step_type;

  return (
    <StepNode
      ref={(node) => drag(drop(node))}
      selected={selected}
      hasError={hasError}
      onClick={() => onSelect(step)}
      style={{
        left: step.position_x,
        top: step.position_y,
        opacity: isDragging ? 0.5 : 1,
      }}
    >
      <div className="step-header">
        <div className="step-icon">
          {stepType?.icon || <TaskIcon />}
        </div>
        <div className="step-title">
          {step.name}
        </div>
      </div>
      
      <div className="step-description">
        {step.description}
      </div>
      
      <div className="step-status">
        {hasError && <ErrorIcon color="error" fontSize="small" />}
        {step.depends_on?.length > 0 && (
          <Chip 
            size="small" 
            label={`Deps: ${step.depends_on.length}`}
            variant="outlined"
          />
        )}
      </div>
      
      {!readOnly && (
        <Box sx={{ position: 'absolute', top: -10, right: -10, display: 'none' }}>
          <IconButton
            size="small"
            onClick={(e) => {
              e.stopPropagation();
              onStartConnection(step.id);
            }}
          >
            <LinkIcon />
          </IconButton>
          <IconButton
            size="small"
            onClick={(e) => {
              e.stopPropagation();
              onDelete(step.id);
            }}
          >
            <DeleteIcon />
          </IconButton>
        </Box>
      )}
    </StepNode>
  );
};

// Draggable step type from toolbox
const DraggableStepType = ({ type, config, onAdd }) => {
  const [{ isDragging }, drag] = useDrag({
    type: 'stepType',
    item: { type, config },
    collect: (monitor) => ({
      isDragging: monitor.isDragging(),
    }),
  });

  return (
    <ListItem
      ref={drag}
      button
      onClick={() => onAdd(type)}
      sx={{ opacity: isDragging ? 0.5 : 1 }}
    >
      <ListItemIcon sx={{ color: config.color }}>
        {config.icon}
      </ListItemIcon>
      <ListItemText 
        primary={config.label}
        secondary={config.description}
      />
    </ListItem>
  );
};

// Step properties panel
const StepPropertiesPanel = ({ step, onUpdate, readOnly }) => {
  const [localStep, setLocalStep] = useState(step);

  useEffect(() => {
    setLocalStep(step);
  }, [step]);

  const handleChange = (field, value) => {
    const updated = { ...localStep, [field]: value };
    setLocalStep(updated);
    onUpdate(step.id, { [field]: value });
  };

  return (
    <Box sx={{ p: 2 }}>
      <Typography variant="h6" gutterBottom>
        Step Configuration
      </Typography>
      
      <TextField
        fullWidth
        label="Name"
        value={localStep.name || ''}
        onChange={(e) => handleChange('name', e.target.value)}
        margin="normal"
        disabled={readOnly}
      />
      
      <TextField
        fullWidth
        label="Description"
        value={localStep.description || ''}
        onChange={(e) => handleChange('description', e.target.value)}
        margin="normal"
        multiline
        rows={2}
        disabled={readOnly}
      />
      
      <FormControl fullWidth margin="normal">
        <InputLabel>Error Handling</InputLabel>
        <Select
          value={localStep.on_error || 'fail'}
          onChange={(e) => handleChange('on_error', e.target.value)}
          disabled={readOnly}
        >
          <MenuItem value="fail">Fail Workflow</MenuItem>
          <MenuItem value="continue">Continue</MenuItem>
          <MenuItem value="retry">Retry</MenuItem>
        </Select>
      </FormControl>
      
      <TextField
        fullWidth
        label="Retry Count"
        type="number"
        value={localStep.retry_count || 0}
        onChange={(e) => handleChange('retry_count', parseInt(e.target.value))}
        margin="normal"
        disabled={readOnly}
        inputProps={{ min: 0, max: 5 }}
      />
      
      <TextField
        fullWidth
        label="Timeout (seconds)"
        type="number"
        value={localStep.timeout_seconds || 300}
        onChange={(e) => handleChange('timeout_seconds', parseInt(e.target.value))}
        margin="normal"
        disabled={readOnly}
        inputProps={{ min: 1, max: 3600 }}
      />
      
      {/* Step-specific configuration */}
      <Accordion sx={{ mt: 2 }}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography>Step Configuration</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <StepConfigForm
            stepType={localStep.step_type}
            config={localStep.config || {}}
            onChange={(config) => handleChange('config', config)}
            readOnly={readOnly}
          />
        </AccordionDetails>
      </Accordion>
      
      <Accordion>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography>Conditions</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <StepConditionsForm
            conditions={localStep.conditions || []}
            onChange={(conditions) => handleChange('conditions', conditions)}
            readOnly={readOnly}
          />
        </AccordionDetails>
      </Accordion>
    </Box>
  );
};

// Workflow properties panel
const WorkflowPropertiesPanel = ({ workflow, onUpdate, readOnly }) => {
  return (
    <Box sx={{ p: 2 }}>
      <Typography variant="h6" gutterBottom>
        Workflow Configuration
      </Typography>
      
      <TextField
        fullWidth
        label="Name"
        value={workflow.name || ''}
        onChange={(e) => onUpdate(prev => ({ ...prev, name: e.target.value }))}
        margin="normal"
        disabled={readOnly}
      />
      
      <TextField
        fullWidth
        label="Description"
        value={workflow.description || ''}
        onChange={(e) => onUpdate(prev => ({ ...prev, description: e.target.value }))}
        margin="normal"
        multiline
        rows={3}
        disabled={readOnly}
      />
      
      <TextField
        fullWidth
        label="Timeout (minutes)"
        type="number"
        value={workflow.timeout_minutes || 60}
        onChange={(e) => onUpdate(prev => ({ 
          ...prev, 
          timeout_minutes: parseInt(e.target.value) 
        }))}
        margin="normal"
        disabled={readOnly}
        inputProps={{ min: 1, max: 1440 }}
      />
      
      <TextField
        fullWidth
        label="Max Retries"
        type="number"
        value={workflow.max_retries || 3}
        onChange={(e) => onUpdate(prev => ({ 
          ...prev, 
          max_retries: parseInt(e.target.value) 
        }))}
        margin="normal"
        disabled={readOnly}
        inputProps={{ min: 0, max: 10 }}
      />
      
      <FormControlLabel
        control={
          <Switch
            checked={workflow.is_parallel || false}
            onChange={(e) => onUpdate(prev => ({ 
              ...prev, 
              is_parallel: e.target.checked 
            }))}
            disabled={readOnly}
          />
        }
        label="Enable Parallel Execution"
        sx={{ mt: 2 }}
      />
      
      {/* Workflow Variables */}
      <Accordion sx={{ mt: 2 }}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography>Variables</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <WorkflowVariablesForm
            variables={workflow.variables || {}}
            onChange={(variables) => onUpdate(prev => ({ ...prev, variables }))}
            readOnly={readOnly}
          />
        </AccordionDetails>
      </Accordion>
      
      {/* Triggers */}
      <Accordion>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography>Triggers ({workflow.triggers?.length || 0})</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <WorkflowTriggersForm
            triggers={workflow.triggers || []}
            onChange={(triggers) => onUpdate(prev => ({ ...prev, triggers }))}
            readOnly={readOnly}
          />
        </AccordionDetails>
      </Accordion>
    </Box>
  );
};

// Step configuration dialog
const StepConfigDialog = ({ open, onClose, step, onSave }) => {
  const [config, setConfig] = useState({});

  useEffect(() => {
    if (step) {
      setConfig(step.config || {});
    }
  }, [step]);

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>Configure Step</DialogTitle>
      <DialogContent>
        {step && (
          <StepConfigForm
            stepType={step.step_type}
            config={config}
            onChange={setConfig}
          />
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button onClick={() => onSave({ config })} variant="contained">
          Save
        </Button>
      </DialogActions>
    </Dialog>
  );
};

// Trigger configuration dialog
const TriggerConfigDialog = ({ open, onClose, trigger, onSave }) => {
  const [config, setConfig] = useState({
    name: '',
    trigger_type: 'MANUAL',
    config: {},
    conditions: [],
    is_enabled: true
  });

  useEffect(() => {
    if (trigger) {
      setConfig(prev => ({
        ...prev,
        name: trigger.label,
        trigger_type: trigger.type
      }));
    }
  }, [trigger]);

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>Configure Trigger</DialogTitle>
      <DialogContent>
        <TextField
          fullWidth
          label="Name"
          value={config.name}
          onChange={(e) => setConfig(prev => ({ ...prev, name: e.target.value }))}
          margin="normal"
        />
        
        <FormControl fullWidth margin="normal">
          <InputLabel>Trigger Type</InputLabel>
          <Select
            value={config.trigger_type}
            onChange={(e) => setConfig(prev => ({ ...prev, trigger_type: e.target.value }))}
          >
            {Object.entries(TRIGGER_TYPES).map(([type, triggerConfig]) => (
              <MenuItem key={type} value={type}>
                {triggerConfig.label}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        
        {config.trigger_type === 'SCHEDULE' && (
          <TextField
            fullWidth
            label="Cron Expression"
            value={config.cron_expression || ''}
            onChange={(e) => setConfig(prev => ({ 
              ...prev, 
              cron_expression: e.target.value 
            }))}
            margin="normal"
            helperText="e.g., 0 9 * * MON (Every Monday at 9 AM)"
          />
        )}
        
        <FormControlLabel
          control={
            <Switch
              checked={config.is_enabled}
              onChange={(e) => setConfig(prev => ({ 
                ...prev, 
                is_enabled: e.target.checked 
              }))}
            />
          }
          label="Enabled"
          sx={{ mt: 2 }}
        />
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button onClick={() => onSave(config)} variant="contained">
          Save
        </Button>
      </DialogActions>
    </Dialog>
  );
};

// Placeholder components for forms
const StepConfigForm = ({ stepType, config, onChange, readOnly }) => {
  // This would contain step-type-specific configuration forms
  return (
    <Box>
      <Typography variant="body2" color="textSecondary">
        Step-specific configuration for {stepType}
      </Typography>
      {/* Add specific configuration fields based on stepType */}
    </Box>
  );
};

const StepConditionsForm = ({ conditions, onChange, readOnly }) => {
  return (
    <Box>
      <Typography variant="body2" color="textSecondary">
        Conditional execution logic
      </Typography>
      {/* Add condition builder interface */}
    </Box>
  );
};

const WorkflowVariablesForm = ({ variables, onChange, readOnly }) => {
  return (
    <Box>
      <Typography variant="body2" color="textSecondary">
        Workflow variables
      </Typography>
      {/* Add variable management interface */}
    </Box>
  );
};

const WorkflowTriggersForm = ({ triggers, onChange, readOnly }) => {
  return (
    <Box>
      {triggers.map((trigger, index) => (
        <Chip
          key={index}
          label={trigger.name}
          onDelete={readOnly ? undefined : () => {
            onChange(triggers.filter((_, i) => i !== index));
          }}
          sx={{ mr: 1, mb: 1 }}
        />
      ))}
    </Box>
  );
};

export default WorkflowDesigner;