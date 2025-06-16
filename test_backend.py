#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Einfaches Test-Backend für OrdnungsHub Development
Startet schnell und funktioniert immer - ohne komplexe Dependencies
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
from typing import Optional

# Simple in-memory storage
automation_rules = [
    {
        'id': 'R001',
        'name': 'PDF Rechnungen → Finanzen',
        'description': 'Alle PDF-Rechnungen automatisch in Finanzen/Rechnungen ablegen',
        'conditions': {
            'file_extension': '.pdf',
            'filename_contains': ['rechnung', 'invoice', 'bill'],
            'content_keywords': ['invoice', 'rechnung', 'total', 'gesamt']
        },
        'actions': {
            'move_to_workspace': 4,  # Finanzen
            'move_to_folder': 'Rechnungen',
            'add_tags': ['rechnung', 'finanzen', 'auto-organized'],
            'priority': 'high'
        },
        'enabled': True,
        'created_at': '2024-06-10T10:00:00Z',
        'last_triggered': '2024-06-10T14:30:00Z',
        'trigger_count': 23
    },
    {
        'id': 'R002',
        'name': 'Bilder → Marketing/Grafiken',
        'description': 'Alle Bildateien in Marketing Grafiken Ordner',
        'conditions': {
            'file_extension': ['.jpg', '.png', '.gif', '.svg'],
            'file_size_mb': {'max': 50}
        },
        'actions': {
            'move_to_workspace': 3,  # Marketing
            'move_to_folder': 'Grafiken',
            'add_tags': ['image', 'grafik', 'auto-organized']
        },
        'enabled': True,
        'created_at': '2024-06-09T09:00:00Z',
        'last_triggered': '2024-06-10T11:15:00Z',
        'trigger_count': 45
    },
    {
        'id': 'R003',
        'name': 'Große Dateien → Archiv',
        'description': 'Dateien über 100MB automatisch archivieren',
        'conditions': {
            'file_size_mb': {'min': 100}
        },
        'actions': {
            'move_to_folder': 'Archiv',
            'compress': True,
            'add_tags': ['large-file', 'archived', 'auto-organized'],
            'notify': True
        },
        'enabled': False,
        'created_at': '2024-06-08T08:00:00Z',
        'last_triggered': None,
        'trigger_count': 0
    }
]

scheduled_tasks = [
    {
        'id': 'S001',
        'name': 'Tägliche Organisation',
        'description': 'Organisiere alle neuen Dateien jeden Tag um 9 Uhr',
        'schedule': {
            'type': 'daily',
            'time': '09:00',
            'timezone': 'Europe/Berlin'
        },
        'actions': [
            'organize_unassigned_files',
            'apply_automation_rules',
            'clean_empty_folders'
        ],
        'enabled': True,
        'last_run': '2024-06-10T09:00:00Z',
        'next_run': '2024-06-11T09:00:00Z',
        'run_count': 15,
        'status': 'success'
    },
    {
        'id': 'S002',
        'name': 'Wöchentliche Bereinigung',
        'description': 'Duplikate finden und alte Dateien archivieren',
        'schedule': {
            'type': 'weekly',
            'day': 'sunday',
            'time': '22:00',
            'timezone': 'Europe/Berlin'
        },
        'actions': [
            'find_duplicates',
            'archive_old_files',
            'generate_storage_report'
        ],
        'enabled': True,
        'last_run': '2024-06-09T22:00:00Z',
        'next_run': '2024-06-16T22:00:00Z',
        'run_count': 8,
        'status': 'success'
    },
    {
        'id': 'S003',
        'name': 'Monatlicher Bericht',
        'description': 'Erstelle monatlichen Organisationsbericht',
        'schedule': {
            'type': 'monthly',
            'day_of_month': 1,
            'time': '08:00',
            'timezone': 'Europe/Berlin'
        },
        'actions': [
            'generate_monthly_report',
            'analyze_file_patterns',
            'suggest_new_rules'
        ],
        'enabled': False,
        'last_run': '2024-06-01T08:00:00Z',
        'next_run': '2024-07-01T08:00:00Z',
        'run_count': 3,
        'status': 'success'
    }
]

tasks = [
    {'id': 'T001', 'title': 'Setup File Manager', 'status': 'completed', 'priority': 'high', 'description': 'Implement drag and drop functionality', 'workspace_id': 1, 'related_files': ['f1', 'f4']},
    {'id': 'T002', 'title': 'Test Drag & Drop', 'status': 'pending', 'priority': 'medium', 'description': 'Verify file upload works correctly', 'workspace_id': 1, 'related_files': []},
    {'id': 'T003', 'title': 'Performance Optimization', 'status': 'completed', 'priority': 'high', 'description': 'Optimize file scanner for large directories', 'workspace_id': 1, 'related_files': ['f2']},
    {'id': 'T004', 'title': 'Marketing Kampagne Q4', 'status': 'pending', 'priority': 'high', 'description': 'Entwicklung der Q4 Marketing Kampagne', 'workspace_id': 3, 'related_files': ['f11']},
    {'id': 'T005', 'title': 'Budget Analyse 2024', 'status': 'in_progress', 'priority': 'high', 'description': 'Jahresbudget analysieren und optimieren', 'workspace_id': 4, 'related_files': ['f13']},
    {'id': 'T006', 'title': 'Lieferanten Bewertung', 'status': 'pending', 'priority': 'medium', 'description': 'Lieferanten für Q1 2025 bewerten', 'workspace_id': 2, 'related_files': ['f8', 'f9']}
]

workspaces = [
    {'id': 1, 'name': 'Website', 'is_active': True, 'file_count': 23, 'color': '#3b82f6', 'files': []},
    {'id': 2, 'name': 'Einkauf', 'is_active': False, 'file_count': 12, 'color': '#10b981', 'files': []},
    {'id': 3, 'name': 'Marketing', 'is_active': False, 'file_count': 18, 'color': '#f59e0b', 'files': []},
    {'id': 4, 'name': 'Finanzen', 'is_active': False, 'file_count': 8, 'color': '#ef4444', 'files': []}
]

# Enhanced workspace structure with folders
workspace_structure = {
    1: {  # Website
        'folders': {
            'HTML': {'count': 3, 'size': '28KB'},
            'CSS': {'count': 5, 'size': '42KB'}, 
            'JavaScript': {'count': 4, 'size': '67KB'},
            'Images': {'count': 8, 'size': '234KB'},
            'Assets': {'count': 6, 'size': '89KB'},
            'Backup': {'count': 2, 'size': '156KB'}
        }
    },
    2: {  # Einkauf
        'folders': {
            'Lieferanten': {'count': 4, 'size': '345KB'},
            'Bestellungen': {'count': 6, 'size': '1.2MB'},
            'Verträge': {'count': 3, 'size': '567KB'},
            'Rechnungen': {'count': 8, 'size': '2.1MB'}
        }
    },
    3: {  # Marketing
        'folders': {
            'Kampagnen': {'count': 5, 'size': '12MB'},
            'Social Media': {'count': 12, 'size': '456KB'},
            'Grafiken': {'count': 15, 'size': '3.4MB'},
            'Berichte': {'count': 4, 'size': '890KB'}
        }
    },
    4: {  # Finanzen
        'folders': {
            'Budget': {'count': 3, 'size': '234KB'},
            'Rechnungen': {'count': 12, 'size': '1.8MB'},
            'Berichte': {'count': 5, 'size': '567KB'},
            'Steuern': {'count': 7, 'size': '1.2MB'}
        }
    }
}

# Files storage per workspace with folder organization
workspace_files = {
    1: {  # Website
        'HTML': [
            {'id': 'f1', 'name': 'index.html', 'type': 'code', 'size': '12KB', 'modified': '2024-06-10', 
             'tags': ['html', 'web', 'frontend', 'code'], 'category': 'development', 'priority': 'high'},
            {'id': 'f2', 'name': 'about.html', 'type': 'code', 'size': '8KB', 'modified': '2024-06-09',
             'tags': ['html', 'web', 'page'], 'category': 'development', 'priority': 'medium'},
            {'id': 'f3', 'name': 'contact.html', 'type': 'code', 'size': '6KB', 'modified': '2024-06-08',
             'tags': ['html', 'web', 'contact'], 'category': 'development', 'priority': 'low'}
        ],
        'CSS': [
            {'id': 'f4', 'name': 'main.css', 'type': 'code', 'size': '15KB', 'modified': '2024-06-10',
             'tags': ['css', 'styling', 'web', 'design'], 'category': 'development', 'priority': 'high'},
            {'id': 'f5', 'name': 'responsive.css', 'type': 'code', 'size': '12KB', 'modified': '2024-06-09',
             'tags': ['css', 'responsive', 'mobile'], 'category': 'development', 'priority': 'medium'}
        ],
        'Images': [
            {'id': 'f6', 'name': 'logo.png', 'type': 'image', 'size': '45KB', 'modified': '2024-06-09',
             'tags': ['logo', 'branding', 'image', 'design'], 'category': 'design', 'priority': 'high'},
            {'id': 'f7', 'name': 'hero-banner.jpg', 'type': 'image', 'size': '89KB', 'modified': '2024-06-08',
             'tags': ['banner', 'hero', 'image'], 'category': 'design', 'priority': 'high'}
        ]
    },
    2: {  # Einkauf
        'Lieferanten': [
            {'id': 'f8', 'name': 'lieferanten_liste.xlsx', 'type': 'document', 'size': '234KB', 'modified': '2024-06-08',
             'tags': ['supplier', 'excel', 'business', 'data'], 'category': 'business', 'priority': 'high'},
            {'id': 'f9', 'name': 'bewertung_lieferanten.pdf', 'type': 'document', 'size': '156KB', 'modified': '2024-06-07',
             'tags': ['supplier', 'evaluation', 'pdf'], 'category': 'business', 'priority': 'medium'}
        ],
        'Bestellungen': [
            {'id': 'f10', 'name': 'bestellung_Q2.pdf', 'type': 'document', 'size': '1.2MB', 'modified': '2024-06-07',
             'tags': ['order', 'quarter', 'pdf', 'procurement'], 'category': 'business', 'priority': 'medium'}
        ]
    },
    3: {  # Marketing
        'Kampagnen': [
            {'id': 'f11', 'name': 'kampagne_2024.pptx', 'type': 'document', 'size': '5.6MB', 'modified': '2024-06-06',
             'tags': ['campaign', 'marketing', 'presentation', '2024'], 'category': 'marketing', 'priority': 'high'}
        ],
        'Social Media': [
            {'id': 'f12', 'name': 'social_media_plan.docx', 'type': 'document', 'size': '89KB', 'modified': '2024-06-05',
             'tags': ['social', 'media', 'plan', 'strategy'], 'category': 'marketing', 'priority': 'medium'}
        ]
    },
    4: {  # Finanzen 
        'Budget': [
            {'id': 'f13', 'name': 'budget_2024.xlsx', 'type': 'document', 'size': '156KB', 'modified': '2024-06-04',
             'tags': ['budget', 'finance', 'money', '2024'], 'category': 'finance', 'priority': 'high'}
        ],
        'Rechnungen': [
            {'id': 'f14', 'name': 'rechnung_mai.pdf', 'type': 'document', 'size': '890KB', 'modified': '2024-06-03',
             'tags': ['invoice', 'may', 'billing', 'payment'], 'category': 'finance', 'priority': 'medium'}
        ]
    }
}

# Global search index for all files (updated for folder structure)
all_files_search = []
for workspace_id, folders in workspace_files.items():
    workspace_name = next(w['name'] for w in workspaces if w['id'] == workspace_id)
    for folder_name, files in folders.items():
        for file in files:
            all_files_search.append({
                **file,
                'workspace_id': workspace_id,
                'workspace_name': workspace_name,
                'folder': folder_name
            })

app = FastAPI(title="OrdnungsHub Test Backend", version="1.0.0")

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],  # Erlaubt alle Origins für Development
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# Models
class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = ''
    priority: Optional[str] = 'medium'
    workspace_id: Optional[int] = None

class TaskUpdate(BaseModel):
    status: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None

class WorkspaceRename(BaseModel):
    name: str

class FileMove(BaseModel):
    file_id: str
    source_workspace_id: int
    target_workspace_id: int

class TaskWorkspaceLink(BaseModel):
    task_id: str
    workspace_id: int

class TaskFileLink(BaseModel):
    task_id: str
    file_id: str
    action: str  # 'add' or 'remove'

class AutomationRuleCreate(BaseModel):
    name: str
    description: str
    conditions: dict
    actions: dict
    enabled: bool = True

class ScheduledTaskCreate(BaseModel):
    name: str
    description: str
    schedule: dict
    actions: list
    enabled: bool = True

# Basic endpoints
@app.get('/')
async def root():
    return {'status': 'running', 'message': 'OrdnungsHub Test Backend', 'version': '1.0.0'}

@app.get('/health')
async def health():
    return {'status': 'healthy', 'backend': 'test', 'database': 'mock'}

# Dashboard
@app.get('/api/dashboard/stats')
async def get_stats():
    completed = len([t for t in tasks if t['status'] == 'completed'])
    return {
        'total_tasks': len(tasks),
        'completed_tasks': completed,
        'active_workspaces': len([w for w in workspaces if w['is_active']]),
        'total_files': sum(w['file_count'] for w in workspaces),
        'completion_percentage': int((completed / len(tasks)) * 100) if tasks else 0
    }

# Tasks
@app.get('/tasks/taskmaster/all')
async def get_tasks():
    return {'success': True, 'tasks': tasks}

@app.post('/tasks/taskmaster/add')
async def add_task(task: TaskCreate):
    new_task = {
        'id': f'T{len(tasks) + 1:03d}',
        'title': task.title,
        'description': task.description or '',
        'priority': task.priority or 'medium',
        'status': 'pending',
        'workspace_id': task.workspace_id,
        'related_files': []
    }
    tasks.append(new_task)
    return {'success': True, 'task': new_task}

@app.put('/tasks/taskmaster/{task_id}/status')
async def update_task_status(task_id: str, update: TaskUpdate):
    for task in tasks:
        if task['id'] == task_id:
            if update.status:
                task['status'] = update.status
            if update.title:
                task['title'] = update.title
            if update.description:
                task['description'] = update.description
            if update.priority:
                task['priority'] = update.priority
            return {'success': True, 'task': task}
    return {'success': False, 'error': 'Task not found'}

@app.get('/tasks/taskmaster/progress')
async def get_progress():
    completed = len([t for t in tasks if t['status'] == 'completed'])
    return {
        'success': True,
        'total_tasks': len(tasks),
        'completed_tasks': completed,
        'progress_percentage': int((completed / len(tasks)) * 100) if tasks else 0,
        'recent_completions': [t['id'] for t in tasks if t['status'] == 'completed'][-3:]
    }

@app.get('/tasks/taskmaster/next')
async def get_next():
    pending_tasks = [t for t in tasks if t['status'] == 'pending']
    if pending_tasks:
        return {'success': True, 'next_task': pending_tasks[0]}
    return {'success': True, 'next_task': None}

@app.post('/tasks/taskmaster/analyze-complexity')
async def analyze_complexity():
    # Mock complexity analysis
    return {
        'success': True,
        'analysis': {
            'total_tasks': len(tasks),
            'high_priority_tasks': len([t for t in tasks if t.get('priority') == 'high']),
            'pending_tasks': len([t for t in tasks if t['status'] == 'pending']),
            'completed_tasks': len([t for t in tasks if t['status'] == 'completed']),
            'complexity_score': 7.5,
            'recommendations': [
                'Consider breaking down large tasks into smaller subtasks',
                'Focus on high priority items first',
                'Review and update task priorities regularly'
            ],
            'categories': {
                'development': len([t for t in tasks if 'code' in t.get('description', '').lower()]),
                'documentation': len([t for t in tasks if 'doc' in t.get('description', '').lower()]),
                'testing': len([t for t in tasks if 'test' in t.get('description', '').lower()])
            }
        }
    }

@app.post('/tasks/taskmaster/{task_id}/expand')
async def expand_task(task_id: str):
    # Mock task expansion
    return {
        'success': True,
        'message': f'Task {task_id} expanded with AI suggestions',
        'subtasks_created': 2
    }

# Task-Workspace Integration Endpoints
@app.get('/tasks/taskmaster/{task_id}/workspace')
async def get_task_workspace(task_id: str):
    task = next((t for t in tasks if t['id'] == task_id), None)
    if not task:
        return {'success': False, 'error': 'Task not found'}
    
    workspace_id = task.get('workspace_id')
    if workspace_id:
        workspace = next((w for w in workspaces if w['id'] == workspace_id), None)
        return {
            'success': True,
            'task': task,
            'workspace': workspace,
            'related_files': task.get('related_files', [])
        }
    
    return {'success': True, 'task': task, 'workspace': None, 'related_files': []}

@app.post('/tasks/taskmaster/{task_id}/link-workspace')
async def link_task_to_workspace(task_id: str, link_data: TaskWorkspaceLink):
    for task in tasks:
        if task['id'] == task_id:
            task['workspace_id'] = link_data.workspace_id
            return {
                'success': True,
                'message': f'Task {task_id} linked to workspace {link_data.workspace_id}',
                'task': task
            }
    return {'success': False, 'error': 'Task not found'}

@app.post('/tasks/taskmaster/{task_id}/link-file')
async def link_task_to_file(task_id: str, file_link: TaskFileLink):
    for task in tasks:
        if task['id'] == task_id:
            related_files = task.get('related_files', [])
            
            if file_link.action == 'add' and file_link.file_id not in related_files:
                related_files.append(file_link.file_id)
            elif file_link.action == 'remove' and file_link.file_id in related_files:
                related_files.remove(file_link.file_id)
            
            task['related_files'] = related_files
            return {
                'success': True,
                'message': f'File {file_link.file_id} {file_link.action}ed to task {task_id}',
                'task': task
            }
    return {'success': False, 'error': 'Task not found'}

@app.get('/workspaces/{workspace_id}/tasks')
async def get_workspace_tasks(workspace_id: int):
    workspace_tasks = [t for t in tasks if t.get('workspace_id') == workspace_id]
    return {
        'success': True,
        'workspace_id': workspace_id,
        'tasks': workspace_tasks,
        'task_count': len(workspace_tasks)
    }

@app.post('/tasks/taskmaster/suggest-workspace')
async def suggest_workspace_for_task(task_data: dict):
    task_title = task_data.get('title', '').lower()
    task_description = task_data.get('description', '').lower()
    combined_text = task_title + ' ' + task_description
    
    # Simple AI workspace suggestion based on keywords
    suggestions = []
    
    # Website workspace
    if any(word in combined_text for word in ['html', 'css', 'js', 'web', 'site', 'frontend', 'backend', 'code', 'entwicklung', 'programmierung']):
        suggestions.append({
            'workspace_id': 1,
            'workspace_name': 'Website',
            'confidence': 0.9,
            'reason': 'Enthält Web-Entwicklung Keywords'
        })
    
    # Marketing workspace
    if any(word in combined_text for word in ['marketing', 'kampagne', 'social', 'media', 'grafik', 'design', 'werbung', 'präsentation']):
        suggestions.append({
            'workspace_id': 3,
            'workspace_name': 'Marketing',
            'confidence': 0.85,
            'reason': 'Enthält Marketing Keywords'
        })
    
    # Einkauf workspace - Enhanced for shopping tasks
    if any(word in combined_text for word in ['einkauf', 'kaufen', 'kauf', 'shop', 'besorg', 'holen', 'lieferant', 'bestellung', 'supplier', 'procurement', 'vertrag', 'milch', 'brot', 'lebensmittel', 'supermarkt', 'laden']):
        suggestions.append({
            'workspace_id': 2,
            'workspace_name': 'Einkauf',
            'confidence': 0.9,
            'reason': 'Enthält Einkaufs-/Shopping Keywords'
        })
    
    # Finanzen workspace
    if any(word in combined_text for word in ['budget', 'finance', 'geld', 'kosten', 'rechnung', 'steuer', 'zahlung', 'bezahlen', 'euro', '€']):
        suggestions.append({
            'workspace_id': 4,
            'workspace_name': 'Finanzen',
            'confidence': 0.85,
            'reason': 'Enthält Finanz-Keywords'
        })
    
    # If no suggestions yet, try more general matching
    if not suggestions:
        # Check for shopping/groceries pattern
        shopping_items = ['milch', 'brot', 'butter', 'käse', 'eier', 'obst', 'gemüse', 'fleisch', 'fisch', 'getränke']
        if any(item in combined_text for item in shopping_items):
            suggestions.append({
                'workspace_id': 2,
                'workspace_name': 'Einkauf',
                'confidence': 0.75,
                'reason': 'Einkaufsliste erkannt'
            })
    
    # Sort by confidence
    suggestions.sort(key=lambda x: x['confidence'], reverse=True)
    
    return {
        'success': True,
        'suggestions': suggestions[:3],  # Top 3 suggestions
        'auto_suggestion': suggestions[0] if suggestions else None
    }

@app.get('/tasks/taskmaster/workspace-overview')
async def get_workspace_task_overview():
    overview = {}
    
    for workspace in workspaces:
        workspace_id = workspace['id']
        workspace_tasks = [t for t in tasks if t.get('workspace_id') == workspace_id]
        
        # Calculate task statistics
        total_tasks = len(workspace_tasks)
        completed_tasks = len([t for t in workspace_tasks if t['status'] == 'completed'])
        in_progress_tasks = len([t for t in workspace_tasks if t['status'] == 'in_progress'])
        pending_tasks = len([t for t in workspace_tasks if t['status'] == 'pending'])
        
        # Get recent activity
        recent_tasks = sorted(workspace_tasks, key=lambda x: x.get('modified', '2024-06-10'), reverse=True)[:3]
        
        overview[workspace_id] = {
            'workspace_name': workspace['name'],
            'workspace_color': workspace['color'],
            'statistics': {
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'in_progress_tasks': in_progress_tasks,
                'pending_tasks': pending_tasks,
                'completion_rate': (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            },
            'recent_tasks': recent_tasks,
            'tasks': workspace_tasks
        }
    
    return {
        'success': True,
        'overview': overview,
        'total_workspaces': len(workspaces)
    }

# Workspaces
@app.get('/workspaces/')
async def get_workspaces():
    return workspaces

@app.post('/workspaces/{workspace_id}/switch')
async def switch_workspace(workspace_id: int):
    for workspace in workspaces:
        workspace['is_active'] = (workspace['id'] == workspace_id)
    return {'success': True, 'active_workspace_id': workspace_id}

@app.put('/workspaces/{workspace_id}/rename')
async def rename_workspace(workspace_id: int, rename_data: WorkspaceRename):
    for workspace in workspaces:
        if workspace['id'] == workspace_id:
            workspace['name'] = rename_data.name
            return {'success': True, 'workspace': workspace}
    return {'success': False, 'error': 'Workspace not found'}

@app.get('/workspaces/{workspace_id}/files')
async def get_workspace_files(workspace_id: int):
    folders = workspace_files.get(workspace_id, {})
    structure = workspace_structure.get(workspace_id, {'folders': {}})
    
    return {
        'success': True, 
        'folders': folders,
        'structure': structure['folders'],
        'workspace_id': workspace_id
    }

@app.get('/workspaces/{workspace_id}/folders/{folder_name}/files')
async def get_folder_files(workspace_id: int, folder_name: str):
    folders = workspace_files.get(workspace_id, {})
    files = folders.get(folder_name, [])
    
    return {
        'success': True,
        'files': files,
        'folder_name': folder_name,
        'workspace_id': workspace_id
    }

@app.post('/workspaces/{workspace_id}/files')
async def add_file_to_workspace(workspace_id: int, file_data: dict):
    if workspace_id not in workspace_files:
        workspace_files[workspace_id] = {}
    
    filename = file_data.get('name', 'Neue Datei')
    
    # AI-Auto-Organization: Determine best folder based on file type and name
    suggested_folder = await ai_suggest_folder(workspace_id, filename, file_data.get('content_preview', ''))
    
    new_file = {
        'id': f'f{len([f for folders in workspace_files.values() for files in folders.values() for f in files]) + 1}',
        'name': filename,
        'type': file_data.get('type', 'document'),
        'size': file_data.get('size', '0KB'),
        'modified': '2024-06-10',
        'tags': [],
        'category': 'general',
        'priority': 'medium'
    }
    
    # Generate AI tags for the file
    ai_response = await categorize_file({'filename': filename})
    new_file.update({
        'tags': ai_response['tags'],
        'category': ai_response['category'],
        'priority': ai_response['priority']
    })
    
    # Add file to suggested folder
    if suggested_folder['folder'] not in workspace_files[workspace_id]:
        workspace_files[workspace_id][suggested_folder['folder']] = []
    
    workspace_files[workspace_id][suggested_folder['folder']].append(new_file)
    
    # Update workspace structure stats
    if workspace_id in workspace_structure:
        if suggested_folder['folder'] not in workspace_structure[workspace_id]['folders']:
            workspace_structure[workspace_id]['folders'][suggested_folder['folder']] = {'count': 0, 'size': '0KB'}
        
        # Update folder stats
        folder_files = workspace_files[workspace_id][suggested_folder['folder']]
        workspace_structure[workspace_id]['folders'][suggested_folder['folder']]['count'] = len(folder_files)
    
    # Update global search index
    all_files_search.append({
        **new_file,
        'workspace_id': workspace_id,
        'workspace_name': next(w['name'] for w in workspaces if w['id'] == workspace_id),
        'folder': suggested_folder['folder']
    })
    
    return {
        'success': True, 
        'file': new_file,
        'ai_organization': suggested_folder,
        'message': f'Datei automatisch in Ordner "{suggested_folder["folder"]}" organisiert'
    }

@app.delete('/workspaces/{workspace_id}/files/{file_id}')
async def remove_file_from_workspace(workspace_id: int, file_id: str):
    if workspace_id in workspace_files:
        workspace_files[workspace_id] = [f for f in workspace_files[workspace_id] if f['id'] != file_id]
        
        # Update file count
        for workspace in workspaces:
            if workspace['id'] == workspace_id:
                workspace['file_count'] = len(workspace_files[workspace_id])
                break
        
        return {'success': True, 'removed_file_id': file_id}
    
    return {'success': False, 'error': 'File or workspace not found'}

@app.post('/workspaces/files/move')
async def move_file_between_workspaces(move_data: FileMove):
    source_id = move_data.source_workspace_id
    target_id = move_data.target_workspace_id
    file_id = move_data.file_id
    
    # Find and remove file from source
    moved_file = None
    if source_id in workspace_files:
        for file in workspace_files[source_id]:
            if file['id'] == file_id:
                moved_file = file
                workspace_files[source_id].remove(file)
                break
    
    if not moved_file:
        return {'success': False, 'error': 'File not found in source workspace'}
    
    # Add file to target
    if target_id not in workspace_files:
        workspace_files[target_id] = []
    
    workspace_files[target_id].append(moved_file)
    
    # Update file counts
    for workspace in workspaces:
        if workspace['id'] == source_id:
            workspace['file_count'] = len(workspace_files[source_id])
        elif workspace['id'] == target_id:
            workspace['file_count'] = len(workspace_files[target_id])
    
    return {'success': True, 'moved_file': moved_file, 'from': source_id, 'to': target_id}

# File Management
@app.get('/file-management/workspace-templates')
async def get_templates():
    return {
        'templates': [
            {'name': 'default', 'description': 'General purpose workspace', 'folders': ['Documents', 'Images', 'Projects']},
            {'name': 'development', 'description': 'Software development workspace', 'folders': ['src', 'docs', 'tests']},
            {'name': 'creative', 'description': 'Creative projects workspace', 'folders': ['Designs', 'Assets', 'Exports']},
            {'name': 'business', 'description': 'Business workspace', 'folders': ['Contracts', 'Reports', 'Presentations']}
        ]
    }

@app.get('/file-management/quick-actions')
async def get_quick_actions(user_id: int = 1):
    return {
        'quick_actions': [
            {
                'action': 'organize',
                'title': 'Organize Files',
                'description': 'Organize your files with AI categorization',
                'priority': 'medium'
            },
            {
                'action': 'deduplicate',
                'title': 'Remove Duplicates',
                'description': 'Find and remove duplicate files',
                'priority': 'low'
            }
        ],
        'total_files': sum(w['file_count'] for w in workspaces),
        'total_size_gb': 2.5
    }

@app.post('/file-management/organize-by-category')
async def organize_files(request: dict):
    return {
        'success': True,
        'total_files': 15,
        'organized_files': 12,
        'categories': {
            'documents': {'count': 5, 'size': 1024000},
            'images': {'count': 4, 'size': 2048000},
            'code': {'count': 3, 'size': 512000}
        },
        'errors': 0,
        'message': 'Files organized successfully (test mode)'
    }

@app.post('/file-management/create-workspace')
async def create_file_workspace(request: dict):
    workspace_name = request.get('workspace_name', 'New Workspace')
    template = request.get('template', 'default')
    
    # Simulate workspace creation
    workspace_path = f"~/OrdnungsHub/Workspaces/{workspace_name}"
    
    # Template folder mapping
    template_folders = {
        'default': ['Documents', 'Images', 'Videos', 'Audio', 'Archives', 'Projects', 'Temp'],
        'development': ['src', 'docs', 'tests', 'resources', 'build', 'dist', 'config', '.vscode'],
        'creative': ['Designs', 'References', 'Exports', 'Projects', 'Assets/Images', 'Assets/Fonts', 'Assets/Icons', 'Archives'],
        'business': ['Contracts', 'Invoices', 'Reports', 'Presentations', 'Meeting Notes', 'Clients', 'Templates', 'Archives']
    }
    
    created_directories = template_folders.get(template, template_folders['default'])
    
    return {
        'workspace_name': workspace_name,
        'workspace_path': workspace_path,
        'template': template,
        'created_directories': created_directories,
        'info': {
            'total_folders': len(created_directories),
            'status': 'created',
            'timestamp': '2024-06-10T12:00:00Z'
        }
    }

# AI Endpoints
@app.post('/ai/analyze-text')
async def analyze_text(request: dict):
    text = request.get('text', '')
    
    # Mock analysis results
    return {
        'entities': {
            'emails': ['example@email.com'] if '@' in text else [],
            'phones': ['123-456-7890'] if any(char.isdigit() for char in text) else [],
            'urls': ['https://example.com'] if 'http' in text else []
        },
        'sentiment': {
            'label': 'positive' if any(word in text.lower() for word in ['good', 'great', 'awesome', 'excellent']) else 'neutral',
            'score': 0.8
        },
        'priority': 'high' if any(word in text.lower() for word in ['urgent', 'important', 'asap']) else 'medium',
        'category': 'work' if any(word in text.lower() for word in ['meeting', 'project', 'task']) else 'personal',
        'keywords': ['AI', 'analysis', 'text'] if len(text) > 20 else ['short', 'text']
    }

@app.post('/ai/suggest-tags')
async def suggest_tags(request: dict):
    text = request.get('text', '')
    
    # Generate mock tags based on content
    tags = []
    if 'project' in text.lower():
        tags.extend(['project', 'work'])
    if 'meeting' in text.lower():
        tags.extend(['meeting', 'schedule'])
    if 'email' in text.lower():
        tags.extend(['communication', 'email'])
    if len(text) > 100:
        tags.append('detailed')
    
    # Default tags if none found
    if not tags:
        tags = ['general', 'text', 'content']
    
    return {
        'tags': tags[:5]  # Limit to 5 tags
    }

@app.post('/ai/categorize-file')
async def categorize_file(request: dict):
    filename = request.get('filename', '')
    content = request.get('content', '')
    file_size = request.get('file_size', 0)
    
    # Enhanced categorization with content analysis
    if filename.endswith('.pdf'):
        category = 'documents'
        tags = ['pdf', 'document', 'text']
        
        # Analyze PDF content if available
        if content:
            if any(word in content.lower() for word in ['invoice', 'bill', 'payment', 'total', 'amount']):
                tags.extend(['invoice', 'billing', 'finance'])
                category = 'invoices'
            elif any(word in content.lower() for word in ['contract', 'agreement', 'terms', 'conditions']):
                tags.extend(['contract', 'legal', 'agreement'])
                category = 'contracts'
            elif any(word in content.lower() for word in ['report', 'analysis', 'findings', 'summary']):
                tags.extend(['report', 'analysis', 'business'])
                category = 'reports'
            elif any(word in content.lower() for word in ['manual', 'guide', 'instructions', 'tutorial']):
                tags.extend(['manual', 'documentation', 'guide'])
                category = 'documentation'
        
    elif filename.endswith(('.jpg', '.png', '.gif', '.jpeg', '.webp', '.svg')):
        category = 'images'
        tags = ['image', 'visual', 'media']
        
        # Analyze image content patterns
        if 'screenshot' in filename.lower() or 'screen' in filename.lower():
            tags.extend(['screenshot', 'capture'])
        elif any(word in filename.lower() for word in ['logo', 'brand', 'icon']):
            tags.extend(['logo', 'branding', 'design'])
        elif any(word in filename.lower() for word in ['photo', 'picture', 'img']):
            tags.extend(['photo', 'picture'])
        
        # Size-based analysis
        if file_size > 5 * 1024 * 1024:  # > 5MB
            tags.append('high-resolution')
        elif file_size < 100 * 1024:  # < 100KB
            tags.append('thumbnail')
            
    elif filename.endswith(('.mp4', '.mov', '.avi', '.mkv', '.webm')):
        category = 'videos'
        tags = ['video', 'media', 'entertainment']
        
        if any(word in filename.lower() for word in ['meeting', 'call', 'conference']):
            tags.extend(['meeting', 'recording', 'business'])
        elif any(word in filename.lower() for word in ['tutorial', 'guide', 'how-to']):
            tags.extend(['tutorial', 'educational'])
        elif any(word in filename.lower() for word in ['demo', 'presentation']):
            tags.extend(['demo', 'presentation'])
            
    elif filename.endswith(('.py', '.js', '.ts', '.html', '.css', '.java', '.cpp', '.c')):
        category = 'code'
        tags = ['code', 'development', 'programming']
        
        # Language-specific tags
        if filename.endswith('.py'):
            tags.append('python')
        elif filename.endswith(('.js', '.ts')):
            tags.extend(['javascript', 'typescript'])
        elif filename.endswith('.html'):
            tags.extend(['html', 'web'])
        elif filename.endswith('.css'):
            tags.extend(['css', 'styling'])
            
        # Content analysis for code
        if content:
            if 'class ' in content or 'function ' in content:
                tags.append('object-oriented')
            if 'import ' in content or 'require(' in content:
                tags.append('modules')
            if 'test' in filename.lower() or 'spec' in filename.lower():
                tags.extend(['testing', 'unit-tests'])
                
    elif filename.endswith(('.xlsx', '.csv', '.xls')):
        category = 'spreadsheets'
        tags = ['data', 'spreadsheet', 'analysis']
        
        if any(word in filename.lower() for word in ['budget', 'finance', 'cost']):
            tags.extend(['budget', 'finance'])
        elif any(word in filename.lower() for word in ['inventory', 'stock', 'products']):
            tags.extend(['inventory', 'stock'])
        elif any(word in filename.lower() for word in ['report', 'analysis', 'stats']):
            tags.extend(['report', 'analysis'])
            
    elif filename.endswith(('.docx', '.doc', '.txt', '.md')):
        category = 'documents'
        tags = ['document', 'text']
        
        if content:
            if any(word in content.lower() for word in ['meeting', 'agenda', 'minutes']):
                tags.extend(['meeting', 'notes'])
            elif any(word in content.lower() for word in ['project', 'plan', 'timeline']):
                tags.extend(['project', 'planning'])
            elif any(word in content.lower() for word in ['policy', 'procedure', 'guidelines']):
                tags.extend(['policy', 'guidelines'])
                
    elif filename.endswith(('.zip', '.rar', '.7z', '.tar', '.gz')):
        category = 'archives'
        tags = ['archive', 'compressed', 'backup']
        
        if 'backup' in filename.lower():
            tags.append('backup')
        elif 'source' in filename.lower() or 'code' in filename.lower():
            tags.extend(['source-code', 'development'])
            
    else:
        category = 'misc'
        tags = ['file', 'general']
    
    # Enhanced priority analysis
    priority = 'medium'
    if any(word in filename.lower() for word in ['important', 'urgent', 'critical', 'asap', 'priority']):
        priority = 'high'
    elif any(word in filename.lower() for word in ['draft', 'temp', 'tmp', 'backup', 'old']):
        priority = 'low'
    elif content and any(word in content.lower() for word in ['deadline', 'urgent', 'important', 'critical']):
        priority = 'high'
    
    # Content-based insights
    insights = []
    if content:
        word_count = len(content.split())
        if word_count > 1000:
            insights.append(f"Long document ({word_count} words)")
        
        # Detect languages
        if any(char in content for char in 'äöüß'):
            insights.append("German content detected")
        elif any(char in content for char in 'àáâãäåæçèéêë'):
            insights.append("French content detected")
        elif any(char in content for char in 'ñáéíóúü'):
            insights.append("Spanish content detected")
        
        # Detect technical content
        if any(word in content.lower() for word in ['algorithm', 'database', 'server', 'api', 'code']):
            insights.append("Technical content")
        elif any(word in content.lower() for word in ['business', 'market', 'revenue', 'profit']):
            insights.append("Business content")
        elif any(word in content.lower() for word in ['research', 'study', 'analysis', 'data']):
            insights.append("Research content")
    
    return {
        'category': category,
        'tags': tags,
        'priority': priority,
        'confidence': 0.95,
        'insights': insights,
        'word_count': len(content.split()) if content else 0,
        'estimated_reading_time': max(1, len(content.split()) // 200) if content else 0  # ~200 words per minute
    }

# Search Endpoints
@app.get('/search/files')
async def search_files(q: str = '', category: str = '', workspace: str = '', tags: str = ''):
    """
    Smart search across all files with AI-generated tags
    - q: Search query (searches in filename, tags, category)
    - category: Filter by category
    - workspace: Filter by workspace name
    - tags: Filter by specific tags (comma-separated)
    """
    results = all_files_search.copy()
    
    # Text search in filename and tags
    if q:
        q_lower = q.lower()
        results = [
            file for file in results
            if (q_lower in file['name'].lower() or
                any(q_lower in tag.lower() for tag in file['tags']) or
                q_lower in file['category'].lower())
        ]
    
    # Category filter
    if category:
        results = [file for file in results if file['category'].lower() == category.lower()]
    
    # Workspace filter
    if workspace:
        results = [file for file in results if workspace.lower() in file['workspace_name'].lower()]
    
    # Tags filter
    if tags:
        tag_list = [tag.strip().lower() for tag in tags.split(',')]
        results = [
            file for file in results
            if any(tag in [t.lower() for t in file['tags']] for tag in tag_list)
        ]
    
    return {
        'success': True,
        'results': results,
        'total_found': len(results),
        'query': {
            'text': q,
            'category': category,
            'workspace': workspace,
            'tags': tags
        }
    }

@app.get('/search/tags')
async def get_all_tags():
    """Get all available tags for autocomplete"""
    all_tags = set()
    for file in all_files_search:
        all_tags.update(file['tags'])
    
    return {
        'success': True,
        'tags': sorted(list(all_tags))
    }

@app.get('/search/categories')
async def get_all_categories():
    """Get all available categories"""
    categories = set(file['category'] for file in all_files_search)
    
    return {
        'success': True,
        'categories': sorted(list(categories))
    }

@app.post('/files/upload')
async def upload_file_with_ai_tagging(file_data: dict):
    """
    Simulate file upload with automatic AI tagging
    """
    filename = file_data.get('filename', 'unknown.txt')
    workspace_id = file_data.get('workspace_id', 1)
    content_preview = file_data.get('content_preview', '')
    
    # Generate AI tags based on filename and content
    ai_response = await categorize_file({'filename': filename})
    
    # Additional content-based tags if preview is available
    additional_tags = []
    if content_preview:
        if len(content_preview) > 500:
            additional_tags.append('detailed')
        if 'important' in content_preview.lower():
            additional_tags.append('important')
        if 'project' in content_preview.lower():
            additional_tags.append('project')
    
    new_file = {
        'id': f'f{len(all_files_search) + 1}',
        'name': filename,
        'type': ai_response['category'],
        'size': file_data.get('size', '0KB'),
        'modified': '2024-06-10',
        'tags': ai_response['tags'] + additional_tags,
        'category': ai_response['category'],
        'priority': ai_response['priority'],
        'workspace_id': workspace_id,
        'workspace_name': next(w['name'] for w in workspaces if w['id'] == workspace_id)
    }
    
    # Add to workspace files
    if workspace_id not in workspace_files:
        workspace_files[workspace_id] = []
    workspace_files[workspace_id].append(new_file)
    
    # Add to search index
    all_files_search.append(new_file)
    
    # Update workspace file count
    for workspace in workspaces:
        if workspace['id'] == workspace_id:
            workspace['file_count'] = len(workspace_files[workspace_id])
            break
    
    return {
        'success': True,
        'file': new_file,
        'ai_analysis': {
            'category': ai_response['category'],
            'tags': ai_response['tags'],
            'priority': ai_response['priority'],
            'additional_tags': additional_tags
        }
    }

@app.post('/file-management/analyze-storage')
async def analyze_storage(request: dict):
    """
    Analyze storage usage and provide insights
    """
    user_id = request.get('user_id', 1)
    
    # Mock storage analysis data
    return {
        'total_files': 847,
        'total_size_gb': 4.7,
        'category_stats': {
            'documents': {'count': 234, 'size': 1024000000},  # 1GB
            'images': {'count': 189, 'size': 1536000000},     # 1.5GB
            'videos': {'count': 45, 'size': 1073741824},      # 1GB
            'code': {'count': 156, 'size': 512000000},        # 512MB
            'archives': {'count': 78, 'size': 786432000},     # 750MB
            'other': {'count': 145, 'size': 268435456}        # 256MB
        },
        'insights': [
            {
                'type': 'duplicate_files',
                'message': '23 potentielle Duplikate gefunden (156MB Speicherplatz)',
                'action': 'Klicken um Duplikate zu überprüfen und zu entfernen'
            },
            {
                'type': 'large_files',
                'message': '8 Dateien sind größer als 100MB',
                'action': 'Diese Dateien für Archivierung oder Kompression prüfen'
            },
            {
                'type': 'old_files',
                'message': '67 Dateien wurden seit über 6 Monaten nicht verwendet',
                'action': 'Erwägen Sie diese ins Archiv oder externe Speicher zu verschieben'
            },
            {
                'type': 'organization',
                'message': '34 Dateien im Downloads-Ordner könnten organisiert werden',
                'action': 'KI-Organisation verwenden um diese Dateien zu sortieren'
            }
        ],
        'large_files': [
            {
                'path': '/Users/Documents/präsentation_final_v3.pptx',
                'size_mb': 245.8,
                'category': 'Präsentation'
            },
            {
                'path': '/Users/Videos/projekt_demo.mp4',
                'size_mb': 189.3,
                'category': 'Video'
            },
            {
                'path': '/Users/Downloads/software_installation.dmg',
                'size_mb': 156.7,
                'category': 'Installer'
            },
            {
                'path': '/Users/Documents/datenbank_backup.sql',
                'size_mb': 134.2,
                'category': 'Datenbank'
            },
            {
                'path': '/Users/Pictures/urlaub_fotos.zip',
                'size_mb': 123.9,
                'category': 'Archiv'
            },
            {
                'path': '/Users/Documents/jahresbericht_2023.pdf',
                'size_mb': 98.4,
                'category': 'Dokument'
            },
            {
                'path': '/Users/Code/node_modules.tar.gz',
                'size_mb': 87.6,
                'category': 'Archiv'
            },
            {
                'path': '/Users/Desktop/bildschirm_aufnahme.mov',
                'size_mb': 76.3,
                'category': 'Video'
            }
        ],
        'recommendations': [
            'Erwägen Sie Cloud-Speicher für Dateien größer als 100MB',
            'Regelmäßige Bereinigung des Downloads-Ordners empfohlen',
            'Alte Projektdateien auf externen Speicher archivieren',
            'Automatische Duplikaterkennung aktivieren'
        ]
    }

# AI-Auto-Organization Functions
async def ai_suggest_folder(workspace_id: int, filename: str, content_preview: str = '') -> dict:
    """
    AI-powered folder suggestion based on file type, name, and workspace context
    """
    
    # Get available folders for this workspace
    available_folders = list(workspace_structure.get(workspace_id, {}).get('folders', {}).keys())
    
    # Default workspace folder mappings
    workspace_folder_rules = {
        1: {  # Website
            'html': 'HTML',
            'css': 'CSS', 
            'js': 'JavaScript',
            'javascript': 'JavaScript',
            'png': 'Images',
            'jpg': 'Images',
            'jpeg': 'Images',
            'gif': 'Images',
            'svg': 'Images',
            'backup': 'Backup',
            'font': 'Assets',
            'woff': 'Assets'
        },
        2: {  # Einkauf
            'lieferant': 'Lieferanten',
            'supplier': 'Lieferanten',
            'bestellung': 'Bestellungen',
            'order': 'Bestellungen',
            'vertrag': 'Verträge',
            'contract': 'Verträge',
            'rechnung': 'Rechnungen',
            'invoice': 'Rechnungen'
        },
        3: {  # Marketing
            'kampagne': 'Kampagnen',
            'campaign': 'Kampagnen',
            'social': 'Social Media',
            'media': 'Social Media',
            'grafik': 'Grafiken',
            'design': 'Grafiken',
            'bericht': 'Berichte',
            'report': 'Berichte'
        },
        4: {  # Finanzen
            'budget': 'Budget',
            'rechnung': 'Rechnungen',
            'invoice': 'Rechnungen',
            'bericht': 'Berichte',
            'report': 'Berichte',
            'steuer': 'Steuern',
            'tax': 'Steuern'
        }
    }
    
    filename_lower = filename.lower()
    
    # Get file extension
    file_extension = filename_lower.split('.')[-1] if '.' in filename_lower else ''
    
    # Get workspace-specific rules
    rules = workspace_folder_rules.get(workspace_id, {})
    
    # Check file extension first
    if file_extension in rules:
        suggested_folder = rules[file_extension]
        confidence = 0.9
        reason = f"Dateiendung .{file_extension} → {suggested_folder}"
    else:
        # Check filename keywords
        suggested_folder = None
        confidence = 0.0
        reason = "Standardordner"
        
        for keyword, folder in rules.items():
            if keyword in filename_lower:
                suggested_folder = folder
                confidence = 0.8
                reason = f"Keyword '{keyword}' im Dateinamen → {folder}"
                break
        
        # Check content preview for additional context
        if content_preview and not suggested_folder:
            content_lower = content_preview.lower()
            for keyword, folder in rules.items():
                if keyword in content_lower:
                    suggested_folder = folder
                    confidence = 0.7
                    reason = f"Keyword '{keyword}' im Inhalt → {folder}"
                    break
    
    # Fallback to first available folder if no match
    if not suggested_folder and available_folders:
        suggested_folder = available_folders[0]
        confidence = 0.3
        reason = f"Fallback → {suggested_folder}"
    elif not suggested_folder:
        suggested_folder = "Allgemein"
        confidence = 0.1
        reason = "Neuer Ordner erstellt"
    
    return {
        'folder': suggested_folder,
        'confidence': confidence,
        'reason': reason,
        'alternative_folders': [f for f in available_folders if f != suggested_folder][:3]
    }

@app.post('/ai/suggest-organization')
async def suggest_file_organization(request: dict):
    """
    Suggest organization for multiple files at once
    """
    files = request.get('files', [])
    workspace_id = request.get('workspace_id', 1)
    
    suggestions = []
    for file_info in files:
        suggestion = await ai_suggest_folder(
            workspace_id, 
            file_info.get('name', ''), 
            file_info.get('content_preview', '')
        )
        suggestions.append({
            'file': file_info,
            'suggestion': suggestion
        })
    
    return {
        'success': True,
        'suggestions': suggestions,
        'workspace_id': workspace_id
    }

@app.post('/ai/auto-organize-workspace')
async def auto_organize_workspace(request: dict):
    """
    Auto-organize all unorganized files in a workspace
    """
    workspace_id = request.get('workspace_id', 1)
    
    # Simulate finding unorganized files
    unorganized_files = [
        {'name': 'homepage_new.html', 'size': '15KB'},
        {'name': 'logo_updated.png', 'size': '67KB'},
        {'name': 'invoice_june.pdf', 'size': '234KB'},
        {'name': 'styles_responsive.css', 'size': '12KB'}
    ]
    
    organized_count = 0
    organization_results = []
    
    for file_info in unorganized_files:
        suggestion = await ai_suggest_folder(workspace_id, file_info['name'])
        if suggestion['confidence'] > 0.5:  # Only auto-organize if confident
            organized_count += 1
            organization_results.append({
                'file': file_info['name'],
                'folder': suggestion['folder'],
                'reason': suggestion['reason']
            })
    
    return {
        'success': True,
        'organized_files': organized_count,
        'total_files': len(unorganized_files),
        'results': organization_results,
        'message': f'{organized_count} von {len(unorganized_files)} Dateien automatisch organisiert'
    }

# Automation Rules Endpoints
@app.get('/automation/rules')
async def get_automation_rules():
    return {
        'success': True,
        'rules': automation_rules,
        'total_rules': len(automation_rules),
        'enabled_rules': len([r for r in automation_rules if r['enabled']])
    }

@app.post('/automation/rules')
async def create_automation_rule(rule: AutomationRuleCreate):
    new_rule = {
        'id': f'R{len(automation_rules) + 1:03d}',
        'name': rule.name,
        'description': rule.description,
        'conditions': rule.conditions,
        'actions': rule.actions,
        'enabled': rule.enabled,
        'created_at': '2024-06-10T15:00:00Z',
        'last_triggered': None,
        'trigger_count': 0
    }
    automation_rules.append(new_rule)
    return {'success': True, 'rule': new_rule}

@app.put('/automation/rules/{rule_id}')
async def update_automation_rule(rule_id: str, rule_update: dict):
    for rule in automation_rules:
        if rule['id'] == rule_id:
            rule.update(rule_update)
            return {'success': True, 'rule': rule}
    return {'success': False, 'error': 'Rule not found'}

@app.delete('/automation/rules/{rule_id}')
async def delete_automation_rule(rule_id: str):
    global automation_rules
    automation_rules = [r for r in automation_rules if r['id'] != rule_id]
    return {'success': True, 'message': f'Rule {rule_id} deleted'}

@app.post('/automation/rules/{rule_id}/toggle')
async def toggle_automation_rule(rule_id: str):
    for rule in automation_rules:
        if rule['id'] == rule_id:
            rule['enabled'] = not rule['enabled']
            return {'success': True, 'rule': rule}
    return {'success': False, 'error': 'Rule not found'}

@app.post('/automation/rules/{rule_id}/test')
async def test_automation_rule(rule_id: str, test_file: dict):
    for rule in automation_rules:
        if rule['id'] == rule_id:
            # Simulate rule testing
            matches = check_rule_conditions(test_file, rule['conditions'])
            return {
                'success': True,
                'matches': matches,
                'rule': rule,
                'test_file': test_file,
                'would_apply': matches
            }
    return {'success': False, 'error': 'Rule not found'}

def check_rule_conditions(file_info: dict, conditions: dict) -> bool:
    """Check if a file matches rule conditions"""
    filename = file_info.get('name', '').lower()
    
    # Check file extension
    if 'file_extension' in conditions:
        extensions = conditions['file_extension']
        if isinstance(extensions, str):
            extensions = [extensions]
        if not any(filename.endswith(ext) for ext in extensions):
            return False
    
    # Check filename contains
    if 'filename_contains' in conditions:
        keywords = conditions['filename_contains']
        if not any(keyword.lower() in filename for keyword in keywords):
            return False
    
    # Check file size
    if 'file_size_mb' in conditions:
        file_size = file_info.get('size_mb', 0)
        if 'min' in conditions['file_size_mb'] and file_size < conditions['file_size_mb']['min']:
            return False
        if 'max' in conditions['file_size_mb'] and file_size > conditions['file_size_mb']['max']:
            return False
    
    return True

@app.post('/automation/apply-rules')
async def apply_automation_rules(files: list):
    """Apply all enabled automation rules to a list of files"""
    results = []
    
    for file_info in files:
        applied_rules = []
        for rule in automation_rules:
            if rule['enabled'] and check_rule_conditions(file_info, rule['conditions']):
                applied_rules.append({
                    'rule_id': rule['id'],
                    'rule_name': rule['name'],
                    'actions': rule['actions']
                })
                # Update trigger count
                rule['trigger_count'] += 1
                rule['last_triggered'] = '2024-06-10T15:30:00Z'
        
        results.append({
            'file': file_info,
            'applied_rules': applied_rules,
            'rule_count': len(applied_rules)
        })
    
    return {
        'success': True,
        'results': results,
        'total_files': len(files),
        'files_with_rules': len([r for r in results if r['rule_count'] > 0])
    }

# Scheduled Tasks Endpoints
@app.get('/automation/scheduled-tasks')
async def get_scheduled_tasks():
    return {
        'success': True,
        'tasks': scheduled_tasks,
        'total_tasks': len(scheduled_tasks),
        'enabled_tasks': len([t for t in scheduled_tasks if t['enabled']])
    }

@app.post('/automation/scheduled-tasks')
async def create_scheduled_task(task: ScheduledTaskCreate):
    new_task = {
        'id': f'S{len(scheduled_tasks) + 1:03d}',
        'name': task.name,
        'description': task.description,
        'schedule': task.schedule,
        'actions': task.actions,
        'enabled': task.enabled,
        'last_run': None,
        'next_run': calculate_next_run(task.schedule),
        'run_count': 0,
        'status': 'pending'
    }
    scheduled_tasks.append(new_task)
    return {'success': True, 'task': new_task}

@app.put('/automation/scheduled-tasks/{task_id}')
async def update_scheduled_task(task_id: str, task_update: dict):
    for task in scheduled_tasks:
        if task['id'] == task_id:
            task.update(task_update)
            if 'schedule' in task_update:
                task['next_run'] = calculate_next_run(task['schedule'])
            return {'success': True, 'task': task}
    return {'success': False, 'error': 'Task not found'}

@app.delete('/automation/scheduled-tasks/{task_id}')
async def delete_scheduled_task(task_id: str):
    global scheduled_tasks
    scheduled_tasks = [t for t in scheduled_tasks if t['id'] != task_id]
    return {'success': True, 'message': f'Scheduled task {task_id} deleted'}

@app.post('/automation/scheduled-tasks/{task_id}/toggle')
async def toggle_scheduled_task(task_id: str):
    for task in scheduled_tasks:
        if task['id'] == task_id:
            task['enabled'] = not task['enabled']
            return {'success': True, 'task': task}
    return {'success': False, 'error': 'Task not found'}

@app.post('/automation/scheduled-tasks/{task_id}/run')
async def run_scheduled_task_now(task_id: str):
    for task in scheduled_tasks:
        if task['id'] == task_id:
            # Simulate task execution
            task['last_run'] = '2024-06-10T15:45:00Z'
            task['next_run'] = calculate_next_run(task['schedule'])
            task['run_count'] += 1
            task['status'] = 'success'
            
            # Simulate action results
            results = []
            for action in task['actions']:
                results.append({
                    'action': action,
                    'status': 'completed',
                    'details': f'{action} executed successfully'
                })
            
            return {
                'success': True,
                'task': task,
                'execution_results': results
            }
    return {'success': False, 'error': 'Task not found'}

def calculate_next_run(schedule: dict) -> str:
    """Calculate next run time based on schedule (simplified)"""
    schedule_type = schedule.get('type', 'daily')
    
    if schedule_type == 'daily':
        return '2024-06-11T' + schedule.get('time', '09:00') + ':00Z'
    elif schedule_type == 'weekly':
        return '2024-06-17T' + schedule.get('time', '09:00') + ':00Z'
    elif schedule_type == 'monthly':
        return '2024-07-01T' + schedule.get('time', '09:00') + ':00Z'
    else:
        return '2024-06-11T09:00:00Z'

@app.get('/automation/dashboard')
async def get_automation_dashboard():
    """Get automation system overview"""
    # Calculate stats
    total_rules = len(automation_rules)
    enabled_rules = len([r for r in automation_rules if r['enabled']])
    total_rule_triggers = sum(r['trigger_count'] for r in automation_rules)
    
    total_schedules = len(scheduled_tasks)
    enabled_schedules = len([t for t in scheduled_tasks if t['enabled']])
    total_schedule_runs = sum(t['run_count'] for t in scheduled_tasks)
    
    # Get most active rules
    active_rules = sorted(automation_rules, key=lambda r: r['trigger_count'], reverse=True)[:3]
    
    # Get upcoming scheduled tasks
    upcoming_tasks = sorted([t for t in scheduled_tasks if t['enabled']], 
                           key=lambda t: t.get('next_run', ''))[:3]
    
    return {
        'success': True,
        'statistics': {
            'rules': {
                'total': total_rules,
                'enabled': enabled_rules,
                'total_triggers': total_rule_triggers
            },
            'scheduled_tasks': {
                'total': total_schedules,
                'enabled': enabled_schedules,
                'total_runs': total_schedule_runs
            }
        },
        'most_active_rules': active_rules,
        'upcoming_tasks': upcoming_tasks,
        'recent_activity': [
            {
                'timestamp': '2024-06-10T14:30:00Z',
                'type': 'rule_triggered',
                'message': 'Rule "PDF Rechnungen → Finanzen" angewendet auf invoice_2024.pdf'
            },
            {
                'timestamp': '2024-06-10T09:00:00Z',
                'type': 'schedule_executed',
                'message': 'Scheduled task "Tägliche Organisation" erfolgreich ausgeführt'
            }
        ]
    }

# Bulk File Operations
@app.post('/file-management/bulk-delete')
async def bulk_delete_files(request: dict):
    file_ids = request.get('file_ids', [])
    deleted_count = 0
    errors = []
    
    for file_id in file_ids:
        try:
            # Simulate file deletion
            deleted_count += 1
        except Exception as e:
            errors.append({'file_id': file_id, 'error': str(e)})
    
    return {
        'success': True,
        'deleted_count': deleted_count,
        'errors': errors,
        'message': f'Successfully deleted {deleted_count} files'
    }

@app.post('/file-management/bulk-move')
async def bulk_move_files(request: dict):
    file_ids = request.get('file_ids', [])
    target_workspace_id = request.get('target_workspace_id')
    target_folder = request.get('target_folder', '')
    moved_count = 0
    errors = []
    
    for file_id in file_ids:
        try:
            # Simulate file move
            moved_count += 1
        except Exception as e:
            errors.append({'file_id': file_id, 'error': str(e)})
    
    return {
        'success': True,
        'moved_count': moved_count,
        'errors': errors,
        'target_workspace_id': target_workspace_id,
        'target_folder': target_folder,
        'message': f'Successfully moved {moved_count} files'
    }

@app.post('/file-management/bulk-tag')
async def bulk_tag_files(request: dict):
    file_ids = request.get('file_ids', [])
    tags = request.get('tags', [])
    action = request.get('action', 'add')  # 'add' or 'remove'
    updated_count = 0
    errors = []
    
    for file_id in file_ids:
        try:
            # Simulate tag update
            updated_count += 1
        except Exception as e:
            errors.append({'file_id': file_id, 'error': str(e)})
    
    return {
        'success': True,
        'updated_count': updated_count,
        'errors': errors,
        'tags': tags,
        'action': action,
        'message': f'Successfully {action}ed tags for {updated_count} files'
    }

@app.post('/file-management/bulk-organize')
async def bulk_organize_files(request: dict):
    file_ids = request.get('file_ids', [])
    organized_count = 0
    errors = []
    organization_results = []
    
    for file_id in file_ids:
        try:
            # Simulate AI organization
            # Find the file in our mock data
            file_found = None
            for workspace_id, folders in workspace_files.items():
                for folder_name, files in folders.items():
                    for file in files:
                        if file['id'] == file_id:
                            file_found = file
                            break
            
            if file_found:
                # Suggest organization based on file type
                suggested_folder = await ai_suggest_folder(1, file_found['name'])  # Default to workspace 1
                organization_results.append({
                    'file_id': file_id,
                    'file_name': file_found['name'],
                    'suggested_folder': suggested_folder['folder'],
                    'confidence': suggested_folder['confidence'],
                    'reason': suggested_folder['reason']
                })
                organized_count += 1
        except Exception as e:
            errors.append({'file_id': file_id, 'error': str(e)})
    
    return {
        'success': True,
        'organized_count': organized_count,
        'errors': errors,
        'organization_results': organization_results,
        'message': f'Successfully organized {organized_count} files'
    }

@app.post('/file-management/deduplicate')
async def deduplicate_files(request: dict):
    delete_duplicates = request.get('delete_duplicates', False)
    
    # Mock duplicate detection results
    duplicates_found = [
        {
            'id': 'dup1',
            'original_file': 'document1.pdf',
            'duplicate_files': ['document1_copy.pdf', 'document1(1).pdf'],
            'space_wasted_mb': 5.2
        },
        {
            'id': 'dup2', 
            'original_file': 'image.jpg',
            'duplicate_files': ['image_backup.jpg'],
            'space_wasted_mb': 2.1
        }
    ]
    
    total_duplicates = sum(len(dup['duplicate_files']) for dup in duplicates_found)
    total_space_wasted = sum(dup['space_wasted_mb'] for dup in duplicates_found)
    
    result = {
        'success': True,
        'total_duplicates': total_duplicates,
        'space_wasted_mb': total_space_wasted,
        'duplicate_groups': duplicates_found
    }
    
    if delete_duplicates:
        result.update({
            'deleted_files': total_duplicates,
            'space_freed_mb': total_space_wasted,
            'message': f'Deleted {total_duplicates} duplicate files, freed {total_space_wasted:.1f} MB'
        })
    else:
        result['message'] = f'Found {total_duplicates} duplicate files wasting {total_space_wasted:.1f} MB'
    
    return result

if __name__ == '__main__':
    print('🚀 Starting OrdnungsHub Test Backend...')
    print('📡 Backend will be available at: http://127.0.0.1:8001')
    print('📋 All endpoints are mocked for easy testing')
    print('💾 Data is stored in memory (resets on restart)')
    uvicorn.run(app, host='127.0.0.1', port=8001, log_level='info')