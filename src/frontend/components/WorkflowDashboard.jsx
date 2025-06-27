/**
 * Workflow Management Dashboard
 * 
 * Main dashboard for managing workflows, templates, executions, and analytics
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  CardActions,
  Typography,
  Button,
  Chip,
  IconButton,
  Menu,
  MenuItem,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Tabs,
  Tab,
  TabPanel,
  Fab,
  Tooltip,
  Snackbar,
  Alert,
  LinearProgress,
  Avatar,
  AvatarGroup,
  Badge,
  Divider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemSecondaryAction
} from '@mui/material';
import {
  Add as AddIcon,
  PlayArrow as PlayIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  MoreVert as MoreIcon,
  Schedule as ScheduleIcon,
  Share as ShareIcon,
  Analytics as AnalyticsIcon,
  History as HistoryIcon,
  FileCopy as CopyIcon,
  GetApp as ExportIcon,
  CloudUpload as ImportIcon,
  Settings as SettingsIcon,
  Visibility as ViewIcon,
  Stop as StopIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Pause as PauseIcon,
  Refresh as RefreshIcon,
  FilterList as FilterIcon,
  Search as SearchIcon,
  TrendingUp as TrendingUpIcon,
  Group as GroupIcon
} from '@mui/icons-material';
import { styled } from '@mui/material/styles';
import { format, formatDistanceToNow } from 'date-fns';

import WorkflowDesigner from './WorkflowDesigner';

// Styled components
const DashboardContainer = styled(Box)(({ theme }) => ({
  padding: theme.spacing(3),
  backgroundColor: theme.palette.background.default,
  minHeight: '100vh',
}));

const StatsCard = styled(Card)(({ theme }) => ({
  height: '100%',
  display: 'flex',
  flexDirection: 'column',
  position: 'relative',
  '& .stats-icon': {
    position: 'absolute',
    top: theme.spacing(2),
    right: theme.spacing(2),
    opacity: 0.1,
    fontSize: '3rem',
  },
}));

const WorkflowCard = styled(Card)(({ theme }) => ({
  height: '100%',
  display: 'flex',
  flexDirection: 'column',
  transition: 'all 0.2s ease-in-out',
  '&:hover': {
    transform: 'translateY(-2px)',
    boxShadow: theme.shadows[4],
  },
}));

const StatusChip = styled(Chip)(({ theme, status }) => {
  const statusColors = {
    active: theme.palette.success.main,
    draft: theme.palette.warning.main,
    paused: theme.palette.info.main,
    completed: theme.palette.success.light,
    failed: theme.palette.error.main,
    running: theme.palette.primary.main,
    pending: theme.palette.grey[500],
  };
  
  return {
    backgroundColor: statusColors[status] || theme.palette.grey[300],
    color: theme.palette.getContrastText(statusColors[status] || theme.palette.grey[300]),
  };
});

const WorkflowDashboard = () => {
  // State management
  const [currentTab, setCurrentTab] = useState(0);
  const [workflows, setWorkflows] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [executions, setExecutions] = useState([]);
  const [analytics, setAnalytics] = useState({});
  const [loading, setLoading] = useState(false);
  const [selectedWorkflow, setSelectedWorkflow] = useState(null);
  const [showDesigner, setShowDesigner] = useState(false);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showTemplateDialog, setShowTemplateDialog] = useState(false);
  const [menuAnchor, setMenuAnchor] = useState(null);
  const [menuWorkflow, setMenuWorkflow] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [notification, setNotification] = useState({ open: false, message: '', type: 'info' });

  // Load data
  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = useCallback(async () => {
    setLoading(true);
    try {
      // Load workflows, templates, executions, and analytics
      await Promise.all([
        loadWorkflows(),
        loadTemplates(),
        loadExecutions(),
        loadAnalytics()
      ]);
    } catch (error) {
      showNotification('Failed to load dashboard data', 'error');
    } finally {
      setLoading(false);
    }
  }, []);

  const loadWorkflows = async () => {
    try {
      const response = await fetch('/api/workflows/');
      const data = await response.json();
      setWorkflows(data.items || []);
    } catch (error) {
      console.error('Failed to load workflows:', error);
    }
  };

  const loadTemplates = async () => {
    try {
      const response = await fetch('/api/workflows/templates');
      const data = await response.json();
      setTemplates(data.items || []);
    } catch (error) {
      console.error('Failed to load templates:', error);
    }
  };

  const loadExecutions = async () => {
    try {
      // Load recent executions across all workflows
      const response = await fetch('/api/workflows/executions/recent');
      const data = await response.json();
      setExecutions(data.items || []);
    } catch (error) {
      console.error('Failed to load executions:', error);
    }
  };

  const loadAnalytics = async () => {
    try {
      const response = await fetch('/api/workflows/statistics');
      const data = await response.json();
      setAnalytics(data);
    } catch (error) {
      console.error('Failed to load analytics:', error);
    }
  };

  // Event handlers
  const handleCreateWorkflow = () => {
    setSelectedWorkflow(null);
    setShowDesigner(true);
  };

  const handleEditWorkflow = (workflow) => {
    setSelectedWorkflow(workflow);
    setShowDesigner(true);
  };

  const handleExecuteWorkflow = async (workflowId) => {
    try {
      const response = await fetch(`/api/workflows/${workflowId}/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      });
      
      if (response.ok) {
        showNotification('Workflow execution started', 'success');
        loadExecutions();
      } else {
        throw new Error('Failed to execute workflow');
      }
    } catch (error) {
      showNotification('Failed to execute workflow', 'error');
    }
  };

  const handleDeleteWorkflow = async (workflowId) => {
    if (!window.confirm('Are you sure you want to delete this workflow?')) {
      return;
    }
    
    try {
      const response = await fetch(`/api/workflows/${workflowId}`, {
        method: 'DELETE'
      });
      
      if (response.ok) {
        showNotification('Workflow deleted successfully', 'success');
        loadWorkflows();
      } else {
        throw new Error('Failed to delete workflow');
      }
    } catch (error) {
      showNotification('Failed to delete workflow', 'error');
    }
  };

  const handleSaveWorkflow = async (workflowData) => {
    try {
      const url = selectedWorkflow 
        ? `/api/workflows/${selectedWorkflow.id}`
        : '/api/workflows/';
      
      const method = selectedWorkflow ? 'PUT' : 'POST';
      
      const response = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(workflowData)
      });
      
      if (response.ok) {
        showNotification(
          selectedWorkflow ? 'Workflow updated successfully' : 'Workflow created successfully',
          'success'
        );
        setShowDesigner(false);
        loadWorkflows();
      } else {
        throw new Error('Failed to save workflow');
      }
    } catch (error) {
      showNotification('Failed to save workflow', 'error');
    }
  };

  const handleCreateFromTemplate = async (templateId, templateData) => {
    try {
      const response = await fetch('/api/workflows/from-template', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          template_id: templateId,
          workspace_id: 1, // TODO: Get current workspace
          name: templateData.name,
          description: templateData.description,
          variable_values: templateData.variables || {}
        })
      });
      
      if (response.ok) {
        showNotification('Workflow created from template successfully', 'success');
        setShowTemplateDialog(false);
        loadWorkflows();
      } else {
        throw new Error('Failed to create workflow from template');
      }
    } catch (error) {
      showNotification('Failed to create workflow from template', 'error');
    }
  };

  const showNotification = (message, type = 'info') => {
    setNotification({ open: true, message, type });
  };

  const handleMenuOpen = (event, workflow) => {
    setMenuAnchor(event.currentTarget);
    setMenuWorkflow(workflow);
  };

  const handleMenuClose = () => {
    setMenuAnchor(null);
    setMenuWorkflow(null);
  };

  // Filter workflows
  const filteredWorkflows = workflows.filter(workflow => {
    const matchesSearch = workflow.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         workflow.description?.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === 'all' || workflow.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  // Tab panel component
  const TabPanel = ({ children, value, index, ...other }) => (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`workflow-tabpanel-${index}`}
      aria-labelledby={`workflow-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );

  if (showDesigner) {
    return (
      <WorkflowDesigner
        workflowId={selectedWorkflow?.id}
        initialWorkflow={selectedWorkflow}
        onSave={handleSaveWorkflow}
        onExecute={(workflow) => handleExecuteWorkflow(workflow.id)}
        onClose={() => setShowDesigner(false)}
      />
    );
  }

  return (
    <DashboardContainer>
      {/* Header */}
      <Box display="flex" justifyContent="between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          Workflow Dashboard
        </Typography>
        <Box display="flex" gap={2}>
          <Button
            variant="outlined"
            startIcon={<ImportIcon />}
            onClick={() => setShowTemplateDialog(true)}
          >
            From Template
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleCreateWorkflow}
          >
            Create Workflow
          </Button>
        </Box>
      </Box>

      {/* Loading indicator */}
      {loading && <LinearProgress sx={{ mb: 2 }} />}

      {/* Statistics Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatsCard>
            <TrendingUpIcon className="stats-icon" />
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Workflows
              </Typography>
              <Typography variant="h4">
                {analytics.total_workflows || 0}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                {analytics.active_workflows || 0} active
              </Typography>
            </CardContent>
          </StatsCard>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <StatsCard>
            <PlayIcon className="stats-icon" />
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Executions Today
              </Typography>
              <Typography variant="h4">
                {analytics.total_executions || 0}
              </Typography>
              <Typography variant="body2" color="success.main">
                {analytics.successful_executions || 0} successful
              </Typography>
            </CardContent>
          </StatsCard>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <StatsCard>
            <SuccessIcon className="stats-icon" />
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Success Rate
              </Typography>
              <Typography variant="h4">
                {analytics.success_rate ? `${analytics.success_rate.toFixed(1)}%` : '0%'}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Last 30 days
              </Typography>
            </CardContent>
          </StatsCard>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <StatsCard>
            <ScheduleIcon className="stats-icon" />
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Avg. Execution Time
              </Typography>
              <Typography variant="h4">
                {analytics.avg_execution_time ? `${(analytics.avg_execution_time / 60).toFixed(1)}m` : '0m'}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Per workflow
              </Typography>
            </CardContent>
          </StatsCard>
        </Grid>
      </Grid>

      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={currentTab} onChange={(e, value) => setCurrentTab(value)}>
          <Tab label="Workflows" />
          <Tab label="Templates" />
          <Tab label="Executions" />
          <Tab label="Analytics" />
        </Tabs>
      </Box>

      {/* Workflows Tab */}
      <TabPanel value={currentTab} index={0}>
        {/* Filters */}
        <Box display="flex" gap={2} mb={3}>
          <TextField
            size="small"
            placeholder="Search workflows..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            InputProps={{
              startAdornment: <SearchIcon sx={{ mr: 1, color: 'action.active' }} />
            }}
            sx={{ minWidth: 300 }}
          />
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>Status</InputLabel>
            <Select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              label="Status"
            >
              <MenuItem value="all">All</MenuItem>
              <MenuItem value="active">Active</MenuItem>
              <MenuItem value="draft">Draft</MenuItem>
              <MenuItem value="paused">Paused</MenuItem>
            </Select>
          </FormControl>
          <Button startIcon={<RefreshIcon />} onClick={loadWorkflows}>
            Refresh
          </Button>
        </Box>

        {/* Workflows Grid */}
        <Grid container spacing={3}>
          {filteredWorkflows.map((workflow) => (
            <Grid item xs={12} sm={6} md={4} key={workflow.id}>
              <WorkflowCard>
                <CardContent sx={{ flexGrow: 1 }}>
                  <Box display="flex" justifyContent="between" alignItems="flex-start" mb={2}>
                    <Typography variant="h6" component="h2" noWrap>
                      {workflow.name}
                    </Typography>
                    <IconButton
                      size="small"
                      onClick={(e) => handleMenuOpen(e, workflow)}
                    >
                      <MoreIcon />
                    </IconButton>
                  </Box>
                  
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    {workflow.description || 'No description'}
                  </Typography>
                  
                  <Box display="flex" gap={1} alignItems="center" mb={2}>
                    <StatusChip
                      size="small"
                      label={workflow.status}
                      status={workflow.status}
                    />
                    <Chip
                      size="small"
                      label={`${workflow.steps?.length || 0} steps`}
                      variant="outlined"
                    />
                  </Box>
                  
                  <Typography variant="caption" color="text.secondary">
                    Last run: {workflow.last_executed_at 
                      ? formatDistanceToNow(new Date(workflow.last_executed_at), { addSuffix: true })
                      : 'Never'
                    }
                  </Typography>
                </CardContent>
                
                <CardActions>
                  <Button
                    size="small"
                    startIcon={<PlayIcon />}
                    onClick={() => handleExecuteWorkflow(workflow.id)}
                    disabled={workflow.status !== 'active'}
                  >
                    Run
                  </Button>
                  <Button
                    size="small"
                    startIcon={<EditIcon />}
                    onClick={() => handleEditWorkflow(workflow)}
                  >
                    Edit
                  </Button>
                  <Button
                    size="small"
                    startIcon={<AnalyticsIcon />}
                    onClick={() => {/* Show analytics */}}
                  >
                    Stats
                  </Button>
                </CardActions>
              </WorkflowCard>
            </Grid>
          ))}
        </Grid>

        {filteredWorkflows.length === 0 && (
          <Box textAlign="center" py={4}>
            <Typography variant="h6" color="text.secondary">
              No workflows found
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Create your first workflow to get started
            </Typography>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={handleCreateWorkflow}
            >
              Create Workflow
            </Button>
          </Box>
        )}
      </TabPanel>

      {/* Templates Tab */}
      <TabPanel value={currentTab} index={1}>
        <Grid container spacing={3}>
          {templates.map((template) => (
            <Grid item xs={12} sm={6} md={4} key={template.id}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    {template.name}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    {template.description}
                  </Typography>
                  <Chip size="small" label={template.category} sx={{ mb: 1 }} />
                  <Typography variant="caption" display="block">
                    Used {template.usage_count || 0} times
                  </Typography>
                </CardContent>
                <CardActions>
                  <Button
                    size="small"
                    onClick={() => handleCreateFromTemplate(template.id, template)}
                  >
                    Use Template
                  </Button>
                  <Button size="small" startIcon={<ViewIcon />}>
                    Preview
                  </Button>
                </CardActions>
              </Card>
            </Grid>
          ))}
        </Grid>
      </TabPanel>

      {/* Executions Tab */}
      <TabPanel value={currentTab} index={2}>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Workflow</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Started</TableCell>
                <TableCell>Duration</TableCell>
                <TableCell>Started By</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {executions.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage).map((execution) => (
                <TableRow key={execution.id}>
                  <TableCell>{execution.workflow_name}</TableCell>
                  <TableCell>
                    <StatusChip size="small" label={execution.status} status={execution.status} />
                  </TableCell>
                  <TableCell>
                    {format(new Date(execution.started_at), 'MMM dd, HH:mm')}
                  </TableCell>
                  <TableCell>
                    {execution.execution_time_seconds 
                      ? `${(execution.execution_time_seconds / 60).toFixed(1)}m`
                      : '-'
                    }
                  </TableCell>
                  <TableCell>{execution.started_by_name}</TableCell>
                  <TableCell>
                    <IconButton size="small">
                      <ViewIcon />
                    </IconButton>
                    {execution.status === 'running' && (
                      <IconButton size="small" color="error">
                        <StopIcon />
                      </IconButton>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
        <TablePagination
          component="div"
          count={executions.length}
          page={page}
          onPageChange={(e, newPage) => setPage(newPage)}
          rowsPerPage={rowsPerPage}
          onRowsPerPageChange={(e) => setRowsPerPage(parseInt(e.target.value))}
        />
      </TabPanel>

      {/* Analytics Tab */}
      <TabPanel value={currentTab} index={3}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Execution Trends
                </Typography>
                {/* Chart component would go here */}
                <Box height={300} display="flex" alignItems="center" justifyContent="center">
                  <Typography color="text.secondary">
                    Chart component placeholder
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Most Used Templates
                </Typography>
                <List>
                  {(analytics.most_used_templates || []).map((template, index) => (
                    <ListItem key={index}>
                      <ListItemText
                        primary={template.name}
                        secondary={`${template.usage_count} uses`}
                      />
                    </ListItem>
                  ))}
                </List>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      {/* Context Menu */}
      <Menu
        anchorEl={menuAnchor}
        open={Boolean(menuAnchor)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={() => {
          handleEditWorkflow(menuWorkflow);
          handleMenuClose();
        }}>
          <ListItemIcon><EditIcon /></ListItemIcon>
          <ListItemText>Edit</ListItemText>
        </MenuItem>
        <MenuItem onClick={() => {
          handleExecuteWorkflow(menuWorkflow.id);
          handleMenuClose();
        }}>
          <ListItemIcon><PlayIcon /></ListItemIcon>
          <ListItemText>Execute</ListItemText>
        </MenuItem>
        <MenuItem onClick={() => {
          // Handle duplicate
          handleMenuClose();
        }}>
          <ListItemIcon><CopyIcon /></ListItemIcon>
          <ListItemText>Duplicate</ListItemText>
        </MenuItem>
        <MenuItem onClick={() => {
          // Handle share
          handleMenuClose();
        }}>
          <ListItemIcon><ShareIcon /></ListItemIcon>
          <ListItemText>Share</ListItemText>
        </MenuItem>
        <Divider />
        <MenuItem 
          onClick={() => {
            handleDeleteWorkflow(menuWorkflow.id);
            handleMenuClose();
          }}
          sx={{ color: 'error.main' }}
        >
          <ListItemIcon><DeleteIcon color="error" /></ListItemIcon>
          <ListItemText>Delete</ListItemText>
        </MenuItem>
      </Menu>

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

      {/* Floating Action Button */}
      <Fab
        color="primary"
        aria-label="add workflow"
        sx={{ position: 'fixed', bottom: 16, right: 16 }}
        onClick={handleCreateWorkflow}
      >
        <AddIcon />
      </Fab>
    </DashboardContainer>
  );
};

export default WorkflowDashboard;