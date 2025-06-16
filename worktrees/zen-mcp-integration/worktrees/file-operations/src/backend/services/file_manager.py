"""
Advanced File Manager Service for OrdnungsHub
Provides comprehensive file operations with AI integration
"""

import os
import shutil
import hashlib
import mimetypes
from typing import List, Dict, Any, Optional, Union, Tuple
from datetime import datetime
from pathlib import Path
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor
import zipfile
import tarfile
from collections import defaultdict

from sqlalchemy.orm import Session
from loguru import logger

from src.backend.database.database import SessionLocal
from src.backend.crud.crud_file import file_metadata as crud_file, tag as crud_tag
from src.backend.schemas.file_metadata import FileMetadataCreate, FileMetadataUpdate
from .enhanced_ai_service import enhanced_ai_service
# from .file_scanner import file_scanner


class FileManagerService:
    """
    Advanced file management service with AI-powered organization
    """
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        # File operation configurations
        self.max_file_size_for_move = 5 * 1024 * 1024 * 1024  # 5GB
        self.chunk_size = 1024 * 1024  # 1MB chunks for large files
        
        # Workspace organization paths
        self.workspace_base_path = Path.home() / "OrdnungsHub" / "Workspaces"
        self.workspace_base_path.mkdir(parents=True, exist_ok=True)
        
        # Archive settings
        self.archive_path = Path.home() / "OrdnungsHub" / "Archives"
        self.archive_path.mkdir(parents=True, exist_ok=True)
        
        # Temporary files path
        self.temp_path = Path.home() / "OrdnungsHub" / "Temp"
        self.temp_path.mkdir(parents=True, exist_ok=True)
    
    async def organize_files_by_category(
        self, 
        user_id: int,
        source_directory: str,
        organize_mode: str = "copy"  # "copy" or "move"
    ) -> Dict[str, Any]:
        """
        Organize files from source directory into categorized folders
        Re-enabled with improved error handling
        """
        try:
            source_path = Path(source_directory).expanduser()
            
            if not source_path.exists():
                return {
                    "error": f"Source directory does not exist: {source_directory}",
                    "total_files": 0,
                    "organized_files": 0,
                    "categories": {},
                    "errors": 1
                }
            
            # Get all files in source directory
            all_files = []
            for file_path in source_path.rglob("*"):
                if file_path.is_file():
                    all_files.append(file_path)
            
            if not all_files:
                return {
                    "success": True,
                    "message": "No files found to organize",
                    "total_files": 0,
                    "organized_files": 0,
                    "categories": {},
                    "errors": 0
                }
            
            organized_count = 0
            categories = {}
            errors = 0
            
            # Simple file categorization without external scanner
            for file_path in all_files:
                try:
                    # Categorize based on file extension
                    category = self._categorize_file_simple(file_path)
                    
                    # Create category folder if it doesn't exist
                    category_path = source_path / f"Organized_{category}"
                    category_path.mkdir(exist_ok=True)
                    
                    # Move or copy file
                    target_path = category_path / file_path.name
                    
                    # Handle duplicate names
                    counter = 1
                    original_target = target_path
                    while target_path.exists():
                        name_parts = original_target.stem, original_target.suffix
                        target_path = original_target.parent / f"{name_parts[0]}_{counter}{name_parts[1]}"
                        counter += 1
                    
                    if organize_mode == "move":
                        file_path.rename(target_path)
                    else:  # copy
                        import shutil
                        shutil.copy2(file_path, target_path)
                    
                    # Track results
                    if category not in categories:
                        categories[category] = {"count": 0, "files": []}
                    categories[category]["count"] += 1
                    categories[category]["files"].append(str(target_path.name))
                    organized_count += 1
                    
                except Exception as e:
                    print(f"Error organizing file {file_path}: {e}")
                    errors += 1
                    continue
            
            return {
                "success": True,
                "message": f"Successfully organized {organized_count} files",
                "total_files": len(all_files),
                "organized_files": organized_count,
                "categories": categories,
                "errors": errors,
                "organize_mode": organize_mode
            }
            
        except Exception as e:
            return {
                "error": f"Failed to organize files: {str(e)}",
                "total_files": 0,
                "organized_files": 0,
                "categories": {},
                "errors": 1
            }
    
    async def _organize_files_by_category_disabled(
        self, 
        user_id: int,
        source_directory: str,
        organize_mode: str = "copy"  # "copy" or "move"
    ) -> Dict[str, Any]:
        """
        Organize files from source directory into categorized folders
        """
        source_path = Path(source_directory)
        if not source_path.exists() or not source_path.is_dir():
            raise ValueError(f"Source directory does not exist: {source_directory}")
        
        # First, scan the directory to get file information
        logger.info(f"Scanning directory for organization: {source_directory}")
        scan_result = await file_scanner.scan_directory(
            directory_path=source_directory,
            user_id=user_id,
            recursive=True
        )
        
        # Get all scanned files from database
        db = SessionLocal()
        try:
            files = crud_file.get_by_user(db, user_id=user_id, skip=0, limit=10000)
            
            # Group files by AI-determined category
            category_groups = defaultdict(list)
            for file_record in files:
                if file_record.file_path.startswith(source_directory):
                    category = file_record.ai_category or 'uncategorized'
                    category_groups[category].append(file_record)
            
            # Create category directories and organize files
            organized_stats = {
                'total_files': 0,
                'organized_files': 0,
                'errors': 0,
                'categories': {},
                'space_saved': 0
            }
            
            for category, file_records in category_groups.items():
                category_path = self.workspace_base_path / "Organized" / category
                category_path.mkdir(parents=True, exist_ok=True)
                
                organized_stats['categories'][category] = {
                    'count': 0,
                    'size': 0,
                    'files': []
                }
                
                for file_record in file_records:
                    organized_stats['total_files'] += 1
                    
                    try:
                        source_file = Path(file_record.file_path)
                        if not source_file.exists():
                            continue
                        
                        # Create subcategory based on file type or date
                        year_month = datetime.fromtimestamp(
                            source_file.stat().st_mtime
                        ).strftime("%Y-%m")
                        
                        dest_dir = category_path / year_month
                        dest_dir.mkdir(parents=True, exist_ok=True)
                        
                        dest_file = dest_dir / source_file.name
                        
                        # Handle duplicate filenames
                        if dest_file.exists():
                            dest_file = self._get_unique_filename(dest_file)
                        
                        # Perform file operation
                        if organize_mode == "move":
                            await self._move_file_async(source_file, dest_file)
                        else:
                            await self._copy_file_async(source_file, dest_file)
                        
                        # Update file record with new path
                        crud_file.update(
                            db, 
                            db_obj=file_record,
                            obj_in={"file_path": str(dest_file)}
                        )
                        
                        organized_stats['organized_files'] += 1
                        organized_stats['categories'][category]['count'] += 1
                        organized_stats['categories'][category]['size'] += file_record.file_size or 0
                        organized_stats['categories'][category]['files'].append({
                            'original': str(source_file),
                            'new': str(dest_file),
                            'size': file_record.file_size
                        })
                        
                        # Calculate space saved for duplicate detection
                        if organize_mode == "move" and self._is_duplicate(db, file_record):
                            organized_stats['space_saved'] += file_record.file_size or 0
                        
                    except Exception as e:
                        logger.error(f"Error organizing file {file_record.file_path}: {e}")
                        organized_stats['errors'] += 1
            
            db.commit()
            
            # Clean up empty directories if moving files
            if organize_mode == "move":
                self._cleanup_empty_directories(source_path)
            
            organized_stats['operation'] = organize_mode
            organized_stats['timestamp'] = datetime.utcnow()
            
            return organized_stats
            
        finally:
            db.close()
    
    async def create_workspace_structure(
        self,
        workspace_name: str,
        template: str = "default"
    ) -> Dict[str, Any]:
        """
        Create a structured workspace with predefined folders
        """
        workspace_path = self.workspace_base_path / workspace_name
        
        if workspace_path.exists():
            raise ValueError(f"Workspace already exists: {workspace_name}")
        
        # Define workspace templates
        templates = {
            "default": [
                "Documents",
                "Images",
                "Videos",
                "Audio",
                "Archives",
                "Projects",
                "Temp"
            ],
            "development": [
                "src",
                "docs",
                "tests",
                "resources",
                "build",
                "dist",
                "config",
                ".vscode"
            ],
            "creative": [
                "Designs",
                "References",
                "Exports",
                "Projects",
                "Assets/Images",
                "Assets/Fonts",
                "Assets/Icons",
                "Archives"
            ],
            "business": [
                "Contracts",
                "Invoices",
                "Reports",
                "Presentations",
                "Meeting Notes",
                "Clients",
                "Templates",
                "Archives"
            ]
        }
        
        # Get template structure
        structure = templates.get(template, templates["default"])
        
        # Create workspace directories
        created_dirs = []
        for folder in structure:
            folder_path = workspace_path / folder
            folder_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(folder_path))
        
        # Create workspace info file
        info_data = {
            "name": workspace_name,
            "template": template,
            "created_at": datetime.utcnow().isoformat(),
            "structure": structure,
            "path": str(workspace_path)
        }
        
        info_file = workspace_path / ".workspace_info.json"
        with open(info_file, 'w') as f:
            json.dump(info_data, f, indent=2)
        
        logger.info(f"Created workspace: {workspace_name} with template: {template}")
        
        return {
            "workspace_name": workspace_name,
            "workspace_path": str(workspace_path),
            "template": template,
            "created_directories": created_dirs,
            "info": info_data
        }
    
    async def smart_file_deduplication(
        self,
        user_id: int,
        directory: Optional[str] = None,
        delete_duplicates: bool = False
    ) -> Dict[str, Any]:
        """
        Find and optionally remove duplicate files using checksums
        """
        db = SessionLocal()
        try:
            # Get all files for user
            if directory:
                files = [
                    f for f in crud_file.get_by_user(db, user_id=user_id, skip=0, limit=10000)
                    if f.file_path.startswith(directory)
                ]
            else:
                files = crud_file.get_by_user(db, user_id=user_id, skip=0, limit=10000)
            
            # Group files by checksum
            checksum_groups = defaultdict(list)
            no_checksum_files = []
            
            for file_record in files:
                if file_record.checksum:
                    checksum_groups[file_record.checksum].append(file_record)
                else:
                    no_checksum_files.append(file_record)
            
            # Find duplicates
            duplicates = []
            space_wasted = 0
            
            for checksum, file_list in checksum_groups.items():
                if len(file_list) > 1:
                    # Sort by file path to keep the most organized one
                    file_list.sort(key=lambda f: (
                        'organized' not in f.file_path.lower(),
                        f.file_path
                    ))
                    
                    original = file_list[0]
                    duplicate_group = {
                        "checksum": checksum,
                        "original": {
                            "path": original.file_path,
                            "size": original.file_size,
                            "id": original.id
                        },
                        "duplicates": []
                    }
                    
                    for dup in file_list[1:]:
                        duplicate_group["duplicates"].append({
                            "path": dup.file_path,
                            "size": dup.file_size,
                            "id": dup.id
                        })
                        space_wasted += dup.file_size or 0
                    
                    duplicates.append(duplicate_group)
            
            # Process duplicates if requested
            deleted_count = 0
            if delete_duplicates and duplicates:
                for dup_group in duplicates:
                    for dup_info in dup_group["duplicates"]:
                        try:
                            # Delete the physical file
                            dup_path = Path(dup_info["path"])
                            if dup_path.exists():
                                dup_path.unlink()
                            
                            # Remove from database
                            crud_file.remove(db, id=dup_info["id"])
                            deleted_count += 1
                            
                        except Exception as e:
                            logger.error(f"Error deleting duplicate {dup_info['path']}: {e}")
            
            # Calculate checksums for files without them
            if no_checksum_files:
                logger.info(f"Calculating checksums for {len(no_checksum_files)} files...")
                for file_record in no_checksum_files[:100]:  # Limit to 100 files per run
                    try:
                        file_path = Path(file_record.file_path)
                        if file_path.exists() and file_path.stat().st_size < 100 * 1024 * 1024:  # < 100MB
                            checksum = await self._calculate_file_checksum(file_path)
                            crud_file.update(
                                db, 
                                db_obj=file_record,
                                obj_in={"checksum": checksum}
                            )
                    except Exception as e:
                        logger.debug(f"Error calculating checksum for {file_record.file_path}: {e}")
            
            db.commit()
            
            return {
                "total_files": len(files),
                "duplicate_groups": len(duplicates),
                "total_duplicates": sum(len(d["duplicates"]) for d in duplicates),
                "space_wasted": space_wasted,
                "space_wasted_mb": round(space_wasted / (1024 * 1024), 2),
                "deleted_count": deleted_count,
                "duplicates": duplicates[:20],  # Limit response size
                "files_without_checksum": len(no_checksum_files)
            }
            
        finally:
            db.close()
    
    async def batch_file_operations(
        self,
        operations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Perform batch file operations (move, copy, delete, rename)
        """
        results = {
            "total": len(operations),
            "successful": 0,
            "failed": 0,
            "results": []
        }
        
        for op in operations:
            op_type = op.get("type")
            source = op.get("source")
            destination = op.get("destination")
            
            try:
                if op_type == "move":
                    await self._move_file_async(Path(source), Path(destination))
                    results["successful"] += 1
                    results["results"].append({
                        "operation": op,
                        "status": "success"
                    })
                    
                elif op_type == "copy":
                    await self._copy_file_async(Path(source), Path(destination))
                    results["successful"] += 1
                    results["results"].append({
                        "operation": op,
                        "status": "success"
                    })
                    
                elif op_type == "delete":
                    Path(source).unlink()
                    results["successful"] += 1
                    results["results"].append({
                        "operation": op,
                        "status": "success"
                    })
                    
                elif op_type == "rename":
                    Path(source).rename(Path(destination))
                    results["successful"] += 1
                    results["results"].append({
                        "operation": op,
                        "status": "success"
                    })
                    
                else:
                    results["failed"] += 1
                    results["results"].append({
                        "operation": op,
                        "status": "error",
                        "error": f"Unknown operation type: {op_type}"
                    })
                    
            except Exception as e:
                results["failed"] += 1
                results["results"].append({
                    "operation": op,
                    "status": "error",
                    "error": str(e)
                })
        
        return results
    
    def _categorize_file_simple(self, file_path: Path) -> str:
        """
        Simple file categorization based on file extension
        """
        extension = file_path.suffix.lower()
        
        # Image files
        if extension in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', '.tiff']:
            return 'Images'
        
        # Video files
        elif extension in ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v']:
            return 'Videos'
        
        # Audio files
        elif extension in ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a']:
            return 'Audio'
        
        # Document files
        elif extension in ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt']:
            return 'Documents'
        
        # Spreadsheet files
        elif extension in ['.xls', '.xlsx', '.csv', '.ods']:
            return 'Spreadsheets'
        
        # Presentation files
        elif extension in ['.ppt', '.pptx', '.odp']:
            return 'Presentations'
        
        # Archive files
        elif extension in ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2']:
            return 'Archives'
        
        # Code files
        elif extension in ['.py', '.js', '.html', '.css', '.java', '.cpp', '.c', '.php', '.rb', '.go']:
            return 'Code'
        
        # Executable files
        elif extension in ['.exe', '.msi', '.dmg', '.pkg', '.deb', '.rpm']:
            return 'Programs'
        
        # Default category
        else:
            return 'Other'
    
    async def create_smart_archive(
        self,
        files: List[str],
        archive_name: str,
        compression: str = "zip",
        password: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create compressed archive with optional encryption
        """
        archive_path = self.archive_path / f"{archive_name}.{compression}"
        
        if archive_path.exists():
            archive_path = self._get_unique_filename(archive_path)
        
        total_size = 0
        archived_files = []
        errors = []
        
        try:
            if compression == "zip":
                with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    if password:
                        zipf.setpassword(password.encode())
                    
                    for file_path in files:
                        try:
                            path = Path(file_path)
                            if path.exists():
                                arcname = path.name
                                zipf.write(path, arcname)
                                file_size = path.stat().st_size
                                total_size += file_size
                                archived_files.append({
                                    "path": str(path),
                                    "arcname": arcname,
                                    "size": file_size
                                })
                        except Exception as e:
                            errors.append({
                                "file": file_path,
                                "error": str(e)
                            })
            
            elif compression == "tar":
                mode = 'w:gz' if archive_name.endswith('.tar.gz') else 'w'
                with tarfile.open(archive_path, mode) as tar:
                    for file_path in files:
                        try:
                            path = Path(file_path)
                            if path.exists():
                                tar.add(path, arcname=path.name)
                                file_size = path.stat().st_size
                                total_size += file_size
                                archived_files.append({
                                    "path": str(path),
                                    "arcname": path.name,
                                    "size": file_size
                                })
                        except Exception as e:
                            errors.append({
                                "file": file_path,
                                "error": str(e)
                            })
            
            compressed_size = archive_path.stat().st_size
            compression_ratio = 1 - (compressed_size / max(total_size, 1))
            
            return {
                "archive_path": str(archive_path),
                "compression": compression,
                "total_files": len(archived_files),
                "archived_files": archived_files,
                "errors": errors,
                "original_size": total_size,
                "compressed_size": compressed_size,
                "compression_ratio": round(compression_ratio * 100, 2),
                "password_protected": bool(password)
            }
            
        except Exception as e:
            if archive_path.exists():
                archive_path.unlink()
            raise e
    
    async def analyze_storage_usage(
        self,
        user_id: int,
        directory: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze storage usage and provide insights
        """
        db = SessionLocal()
        try:
            # Get all files
            if directory:
                files = [
                    f for f in crud_file.get_by_user(db, user_id=user_id, skip=0, limit=10000)
                    if f.file_path.startswith(directory)
                ]
            else:
                files = crud_file.get_by_user(db, user_id=user_id, skip=0, limit=10000)
            
            # Analyze by category
            category_stats = defaultdict(lambda: {"count": 0, "size": 0, "files": []})
            
            # Analyze by file type
            type_stats = defaultdict(lambda: {"count": 0, "size": 0})
            
            # Find large files
            large_files = []
            old_files = []
            
            total_size = 0
            current_time = datetime.utcnow()
            
            for file_record in files:
                size = file_record.file_size or 0
                total_size += size
                
                # Category analysis
                category = file_record.ai_category or 'uncategorized'
                category_stats[category]["count"] += 1
                category_stats[category]["size"] += size
                
                # Type analysis
                ext = file_record.file_extension or 'no_extension'
                type_stats[ext]["count"] += 1
                type_stats[ext]["size"] += size
                
                # Large files (> 100MB)
                if size > 100 * 1024 * 1024:
                    large_files.append({
                        "path": file_record.file_path,
                        "size": size,
                        "size_mb": round(size / (1024 * 1024), 2),
                        "category": category
                    })
                
                # Old files (not accessed in 6 months)
                if file_record.last_accessed_at:
                    days_old = (current_time - file_record.last_accessed_at).days
                    if days_old > 180:
                        old_files.append({
                            "path": file_record.file_path,
                            "size": size,
                            "days_old": days_old,
                            "last_accessed": file_record.last_accessed_at.isoformat()
                        })
            
            # Sort and limit results
            large_files.sort(key=lambda x: x["size"], reverse=True)
            old_files.sort(key=lambda x: x["days_old"], reverse=True)
            
            # Convert defaultdicts to regular dicts for JSON serialization
            category_stats = dict(category_stats)
            type_stats = dict(type_stats)
            
            # Calculate insights
            insights = []
            
            # Large files insight
            if large_files:
                large_files_size = sum(f["size"] for f in large_files[:10])
                insights.append({
                    "type": "large_files",
                    "message": f"Top 10 large files occupy {round(large_files_size / (1024**3), 2)} GB",
                    "action": "Consider archiving or moving to external storage"
                })
            
            # Old files insight
            if old_files:
                old_files_size = sum(f["size"] for f in old_files[:50])
                insights.append({
                    "type": "old_files",
                    "message": f"{len(old_files)} files haven't been accessed in 6+ months ({round(old_files_size / (1024**3), 2)} GB)",
                    "action": "Review and archive old files"
                })
            
            # Duplicate insight (simplified)
            dup_result = await self.smart_file_deduplication(user_id, directory, delete_duplicates=False)
            if dup_result["space_wasted"] > 0:
                insights.append({
                    "type": "duplicates",
                    "message": f"Found {dup_result['total_duplicates']} duplicate files wasting {dup_result['space_wasted_mb']} MB",
                    "action": "Run deduplication to free up space"
                })
            
            return {
                "total_files": len(files),
                "total_size": total_size,
                "total_size_gb": round(total_size / (1024**3), 2),
                "category_stats": category_stats,
                "type_stats": dict(sorted(
                    type_stats.items(), 
                    key=lambda x: x[1]["size"], 
                    reverse=True
                )[:20]),  # Top 20 file types
                "large_files": large_files[:20],
                "old_files": old_files[:20],
                "insights": insights,
                "scan_directory": directory or "All files"
            }
            
        finally:
            db.close()
    
    # Helper methods
    async def _move_file_async(self, source: Path, destination: Path):
        """Async file move operation"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self.executor, shutil.move, str(source), str(destination))
    
    async def _copy_file_async(self, source: Path, destination: Path):
        """Async file copy operation"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self.executor, shutil.copy2, str(source), str(destination))
    
    async def _calculate_file_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of a file"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, self._calculate_checksum_sync, file_path)
    
    def _calculate_checksum_sync(self, file_path: Path) -> str:
        """Synchronous checksum calculation"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def _get_unique_filename(self, file_path: Path) -> Path:
        """Generate unique filename if file exists"""
        base = file_path.stem
        extension = file_path.suffix
        directory = file_path.parent
        counter = 1
        
        while file_path.exists():
            file_path = directory / f"{base}_{counter}{extension}"
            counter += 1
        
        return file_path
    
    def _is_duplicate(self, db: Session, file_record) -> bool:
        """Check if file has duplicates based on checksum"""
        if not file_record.checksum:
            return False
        
        count = db.query(crud_file.model).filter(
            crud_file.model.checksum == file_record.checksum
        ).count()
        
        return count > 1
    
    def _cleanup_empty_directories(self, root_path: Path):
        """Remove empty directories recursively"""
        for dirpath, dirnames, filenames in os.walk(root_path, topdown=False):
            if not dirnames and not filenames:
                try:
                    Path(dirpath).rmdir()
                    logger.debug(f"Removed empty directory: {dirpath}")
                except Exception as e:
                    logger.debug(f"Could not remove directory {dirpath}: {e}")


# Global file manager instance
file_manager = FileManagerService()