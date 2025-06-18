"""
AI-Powered File Scanner for OrdnungsHub
Automatically scans and categorizes files using the enhanced AI service
"""

import os
import hashlib
import mimetypes
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime, timedelta
from pathlib import Path
import asyncio
from concurrent.futures import ThreadPoolExecutor
import json
from dataclasses import dataclass
import time

from sqlalchemy.orm import Session
from loguru import logger

from database.database import SessionLocal
from crud.crud_file import file_metadata as crud_file
from schemas.file_metadata import FileMetadataCreate
from .enhanced_ai_service import enhanced_ai_service


@dataclass
class ScanProgress:
    """Data class for scan progress tracking"""
    total_files: int = 0
    processed_files: int = 0
    current_file: str = ""
    current_batch: int = 0
    total_batches: int = 0
    progress_percent: float = 0.0
    estimated_time_remaining: float = 0.0
    files_per_second: float = 0.0


class CancellationToken:
    """Token for cancelling long-running operations"""
    
    def __init__(self):
        self._cancelled = False
    
    def cancel(self):
        """Cancel the operation"""
        self._cancelled = True
    
    def is_cancelled(self) -> bool:
        """Check if operation is cancelled"""
        return self._cancelled
    
    def check_cancelled(self):
        """Raise exception if cancelled"""
        if self._cancelled:
            raise asyncio.CancelledError("Operation was cancelled")


class FileScannerService:
    """
    AI-powered file scanner that automatically discovers and categorizes files
    """
    
    def __init__(self, max_workers: int = 4, chunk_size: int = 100):
        self.max_workers = max_workers
        self.chunk_size = chunk_size
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.scanning = False
        self.scan_progress = ScanProgress()
        self.scan_stats = {}
        self.current_cancellation_token: Optional[CancellationToken] = None
        
        # File type handlers
        self.text_extensions = {'.txt', '.md', '.py', '.js', '.html', '.css', '.json', '.xml'}
        self.image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp'}
        self.document_extensions = {'.pdf', '.doc', '.docx', '.odt', '.rtf'}
        self.code_extensions = {'.py', '.js', '.html', '.css', '.cpp', '.java', '.go', '.rs'}
        
        # Ignore patterns
        self.ignore_patterns = {
            '.git', '.svn', '.hg', 'node_modules', '__pycache__', '.pytest_cache',
            '.DS_Store', 'Thumbs.db', '.tmp', '.temp', '.vscode', '.idea'
        }
        
        # Size limits for content extraction
        self.max_text_file_size = 1 * 1024 * 1024  # 1MB for text files
        self.max_preview_length = 1000  # Max characters for preview
        
        # Performance settings
        self.discovery_chunk_size = 1000  # Files to discover per chunk
        self.batch_size = 50  # Files to process per batch
        self.max_files_per_scan = 10000  # Maximum files to process in one scan
    
    async def scan_directory(
        self, 
        directory_path: str, 
        user_id: int,
        recursive: bool = True,
        progress_callback: Optional[Callable[[ScanProgress, Dict[str, Any]], None]] = None,
        cancellation_token: Optional[CancellationToken] = None
    ) -> Dict[str, Any]:
        """
        Scan a directory and add files to the database with AI categorization
        Enhanced with chunked processing, progress updates, and cancellation support
        """
        directory_path = Path(directory_path)
        
        if not directory_path.exists() or not directory_path.is_dir():
            raise ValueError(f"Directory does not exist: {directory_path}")
        
        # Set up cancellation token
        if cancellation_token is None:
            cancellation_token = CancellationToken()
        self.current_cancellation_token = cancellation_token
        
        self.scanning = True
        start_time = time.time()
        
        # Reset scan progress
        self.scan_progress = ScanProgress()
        self.scan_stats = {
            'total_files': 0,
            'processed_files': 0,
            'skipped_files': 0,
            'new_files': 0,
            'updated_files': 0,
            'errors': 0,
            'permission_errors': 0,
            'start_time': datetime.utcnow(),
            'categories': {},
            'performance': {
                'discovery_time': 0,
                'processing_time': 0,
                'avg_files_per_second': 0
            }
        }
        
        try:
            # Check cancellation before starting
            cancellation_token.check_cancelled()
            
            # Discover files with chunked processing
            logger.info(f"Starting chunked discovery of directory: {directory_path}")
            discovery_start = time.time()
            
            async for file_chunk in self._discover_files_chunked(directory_path, recursive, cancellation_token):
                # Update progress during discovery
                self.scan_progress.total_files += len(file_chunk)
                if progress_callback:
                    await progress_callback(self.scan_progress, self.scan_stats)
                
                # Check if we've hit the limit
                if self.scan_progress.total_files > self.max_files_per_scan:
                    logger.warning(f"Reached maximum file limit ({self.max_files_per_scan}), stopping discovery")
                    break
            
            discovery_time = time.time() - discovery_start
            self.scan_stats['performance']['discovery_time'] = discovery_time
            self.scan_stats['total_files'] = self.scan_progress.total_files
            
            if self.scan_progress.total_files == 0:
                logger.info("No files found to process")
                return self.scan_stats
            
            logger.info(f"Discovered {self.scan_progress.total_files} files in {discovery_time:.2f}s")
            
            # Process files with optimized batching
            processing_start = time.time()
            await self._process_files_optimized(directory_path, recursive, user_id, progress_callback, cancellation_token)
            
            processing_time = time.time() - processing_start
            self.scan_stats['performance']['processing_time'] = processing_time
            
            # Calculate final statistics
            total_time = time.time() - start_time
            if total_time > 0:
                self.scan_stats['performance']['avg_files_per_second'] = self.scan_progress.processed_files / total_time
            
            self.scan_stats['end_time'] = datetime.utcnow()
            self.scan_stats['duration'] = total_time
            
            logger.info(f"Scan completed successfully: {self.scan_stats}")
            return self.scan_stats
            
        except asyncio.CancelledError:
            logger.info("Scan was cancelled by user")
            self.scan_stats['cancelled'] = True
            self.scan_stats['end_time'] = datetime.utcnow()
            self.scan_stats['duration'] = time.time() - start_time
            return self.scan_stats
            
        except Exception as e:
            logger.error(f"Scan failed: {e}")
            self.scan_stats['error'] = str(e)
            self.scan_stats['end_time'] = datetime.utcnow()
            self.scan_stats['duration'] = time.time() - start_time
            raise
        finally:
            self.scanning = False
            self.current_cancellation_token = None
    
    async def _discover_files_chunked(
        self, 
        directory: Path, 
        recursive: bool, 
        cancellation_token: CancellationToken
    ):
        """
        Discover files in chunks for better memory management and progress updates
        """
        current_chunk = []
        
        try:
            if recursive:
                async for file_path in self._walk_directory_async(directory, cancellation_token):
                    if not self._should_ignore_file(file_path.name):
                        current_chunk.append(file_path)
                        
                        # Yield chunk when it reaches the desired size
                        if len(current_chunk) >= self.discovery_chunk_size:
                            yield current_chunk
                            current_chunk = []
                            
                            # Allow for cancellation and other async operations
                            await asyncio.sleep(0.001)
            else:
                try:
                    for item in directory.iterdir():
                        cancellation_token.check_cancelled()
                        
                        if item.is_file() and not self._should_ignore_file(item.name):
                            current_chunk.append(item)
                            
                            if len(current_chunk) >= self.discovery_chunk_size:
                                yield current_chunk
                                current_chunk = []
                                await asyncio.sleep(0.001)
                                
                except PermissionError:
                    logger.warning(f"Permission denied accessing: {directory}")
                    self.scan_stats['permission_errors'] += 1
                except Exception as e:
                    logger.error(f"Error accessing directory {directory}: {e}")
            
            # Yield remaining files in the last chunk
            if current_chunk:
                yield current_chunk
                
        except asyncio.CancelledError:
            logger.info("File discovery was cancelled")
            raise
        except Exception as e:
            logger.error(f"Error in chunked file discovery: {e}")
            self.scan_stats['errors'] += 1
    
    async def _walk_directory_async(
        self, 
        directory: Path, 
        cancellation_token: CancellationToken
    ):
        """
        Async generator that walks through directory tree with cancellation support
        """
        loop = asyncio.get_event_loop()
        
        def walk_sync():
            """Synchronous directory walk that respects cancellation"""
            for root, dirs, filenames in os.walk(directory):
                # Check for cancellation
                if cancellation_token.is_cancelled():
                    break
                
                # Filter out ignored directories in-place
                dirs[:] = [d for d in dirs if d not in self.ignore_patterns and not d.startswith('.')]
                
                # Yield file paths
                for filename in filenames:
                    if cancellation_token.is_cancelled():
                        break
                    yield Path(root) / filename
        
        try:
            # Run directory walk in executor to avoid blocking
            for file_path in await loop.run_in_executor(self.executor, lambda: list(walk_sync())):
                cancellation_token.check_cancelled()
                yield file_path
                
                # Periodically yield control
                if self.scan_progress.total_files % 100 == 0:
                    await asyncio.sleep(0.001)
                    
        except PermissionError as e:
            logger.warning(f"Permission denied during directory walk: {e}")
            self.scan_stats['permission_errors'] += 1
        except asyncio.CancelledError:
            logger.info("Directory walk was cancelled")
            raise
        except Exception as e:
            logger.error(f"Error during async directory walk: {e}")
            self.scan_stats['errors'] += 1
    
    def _should_ignore_file(self, filename: str) -> bool:
        """Check if file should be ignored"""
        filename_lower = filename.lower()
        
        # Ignore hidden files
        if filename.startswith('.'):
            return True
            
        # Ignore temp files
        if filename_lower.endswith(('.tmp', '.temp', '.swp', '.bak', '.lock')):
            return True
            
        # Ignore system files
        if filename_lower in {'thumbs.db', 'desktop.ini', '.ds_store'}:
            return True
            
        # Ignore log files that are typically large and not useful for categorization
        if filename_lower.endswith(('.log', '.out')):
            return True
            
        return False
    
    async def _process_files_optimized(
        self,
        directory: Path,
        recursive: bool,
        user_id: int,
        progress_callback: Optional[Callable[[ScanProgress, Dict[str, Any]], None]],
        cancellation_token: CancellationToken
    ):
        """
        Optimized file processing with improved batching and progress tracking
        """
        start_time = time.time()
        processed_count = 0
        
        # Calculate total batches for progress tracking
        self.scan_progress.total_batches = max(1, (self.scan_progress.total_files + self.batch_size - 1) // self.batch_size)
        
        async for file_chunk in self._discover_files_chunked(directory, recursive, cancellation_token):
            # Process files in smaller batches within each chunk
            for i in range(0, len(file_chunk), self.batch_size):
                cancellation_token.check_cancelled()
                
                batch = file_chunk[i:i + self.batch_size]
                self.scan_progress.current_batch += 1
                
                # Update current file being processed
                if batch:
                    self.scan_progress.current_file = str(batch[0])
                
                # Process the batch
                await self._process_file_batch_optimized(batch, user_id, cancellation_token)
                
                processed_count += len(batch)
                self.scan_progress.processed_files = processed_count
                
                # Calculate progress percentage
                self.scan_progress.progress_percent = min(100.0, (processed_count / self.scan_progress.total_files) * 100)
                
                # Calculate performance metrics
                elapsed_time = time.time() - start_time
                if elapsed_time > 0:
                    self.scan_progress.files_per_second = processed_count / elapsed_time
                    
                    # Estimate remaining time
                    remaining_files = self.scan_progress.total_files - processed_count
                    if self.scan_progress.files_per_second > 0:
                        self.scan_progress.estimated_time_remaining = remaining_files / self.scan_progress.files_per_second
                
                # Update scan stats
                self.scan_stats['processed_files'] = processed_count
                
                # Call progress callback
                if progress_callback:
                    await progress_callback(self.scan_progress, self.scan_stats)
                
                # Brief pause to allow UI updates and check for cancellation
                await asyncio.sleep(0.01)
    
    async def _process_file_batch_optimized(
        self, 
        file_paths: List[Path], 
        user_id: int, 
        cancellation_token: CancellationToken
    ):
        """
        Process a batch of files with improved error handling and cancellation support
        """
        # Use semaphore to limit concurrent processing
        semaphore = asyncio.Semaphore(self.max_workers)
        
        async def process_with_semaphore(file_path: Path):
            async with semaphore:
                cancellation_token.check_cancelled()
                return await self._process_single_file_optimized(file_path, user_id, cancellation_token)
        
        # Create tasks for batch processing
        tasks = [asyncio.create_task(process_with_semaphore(file_path)) for file_path in file_paths]
        
        # Process with proper error handling
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle results and update statistics
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                if isinstance(result, asyncio.CancelledError):
                    raise result
                else:
                    logger.error(f"Error processing file {file_paths[i]}: {result}")
                    self.scan_stats['errors'] += 1
    
    async def _process_single_file_optimized(
        self, 
        file_path: Path, 
        user_id: int, 
        cancellation_token: CancellationToken
    ):
        """
        Process a single file with improved error handling and cancellation support
        """
        db = None
        try:
            # Check for cancellation before starting
            cancellation_token.check_cancelled()
            
            # Check if file still exists (it might have been deleted during scan)
            if not file_path.exists():
                return
            
            # Check file size limits to avoid processing huge files
            try:
                file_stat = file_path.stat()
                # Skip files larger than 100MB for performance
                if file_stat.st_size > 100 * 1024 * 1024:
                    logger.debug(f"Skipping large file: {file_path} ({file_stat.st_size} bytes)")
                    self.scan_stats['skipped_files'] += 1
                    return
            except (OSError, PermissionError):
                logger.debug(f"Cannot access file stats: {file_path}")
                self.scan_stats['permission_errors'] += 1
                return
            
            # Get database session
            db = SessionLocal()
            
            # Check if file already exists in database
            existing_file = crud_file.get_by_path(
                db, file_path=str(file_path), user_id=user_id
            )
            
            # Skip if file exists and hasn't been modified
            if existing_file and existing_file.file_modified_at:
                if existing_file.file_modified_at.timestamp() >= file_stat.st_mtime:
                    self.scan_stats['skipped_files'] += 1
                    return
            
            # Check for cancellation before expensive operations
            cancellation_token.check_cancelled()
            
            # Extract file metadata
            file_info = await self._extract_file_metadata_safe(file_path, cancellation_token)
            
            if not file_info:
                self.scan_stats['errors'] += 1
                return
            
            # Check for cancellation before AI processing
            cancellation_token.check_cancelled()
            
            # AI categorization with timeout
            try:
                ai_result = await asyncio.wait_for(
                    enhanced_ai_service.smart_categorize_file(
                        filename=file_path.name,
                        file_path=str(file_path),
                        content_preview=file_info.get('content_preview', '')
                    ),
                    timeout=30.0  # 30 second timeout for AI processing
                )
            except asyncio.TimeoutError:
                logger.warning(f"AI categorization timeout for file: {file_path}")
                # Use basic categorization as fallback
                ai_result = self._basic_categorize_file(file_path)
            
            # Create file metadata record
            file_metadata = FileMetadataCreate(
                user_id=user_id,
                file_path=str(file_path),
                file_name=file_path.name,
                file_extension=file_path.suffix.lower(),
                file_size=file_info.get('size'),
                mime_type=file_info.get('mime_type'),
                ai_category=ai_result.get('category'),
                ai_description=ai_result.get('description'),
                ai_tags=','.join(ai_result.get('tags', [])),
                importance_score=self._calculate_importance_score(ai_result),
                file_created_at=file_info.get('created_at'),
                file_modified_at=file_info.get('modified_at'),
                last_accessed_at=file_info.get('accessed_at')
            )
            
            # Check for cancellation before database operations
            cancellation_token.check_cancelled()
            
            if existing_file:
                # Update existing record
                crud_file.update(db, db_obj=existing_file, obj_in=file_metadata)
                self.scan_stats['updated_files'] += 1
            else:
                # Create new record
                crud_file.create_with_checksum(
                    db, obj_in=file_metadata, file_path=str(file_path)
                )
                self.scan_stats['new_files'] += 1
            
            # Update category stats
            category = ai_result.get('category', 'unknown')
            self.scan_stats['categories'][category] = (
                self.scan_stats['categories'].get(category, 0) + 1
            )
                
        except asyncio.CancelledError:
            logger.debug(f"File processing cancelled for: {file_path}")
            raise
        except PermissionError:
            logger.debug(f"Permission denied for file: {file_path}")
            self.scan_stats['permission_errors'] += 1
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            self.scan_stats['errors'] += 1
        finally:
            if db:
                db.close()
    
    async def _extract_file_metadata_safe(
        self, 
        file_path: Path, 
        cancellation_token: CancellationToken
    ) -> Optional[Dict[str, Any]]:
        """
        Extract metadata from file with cancellation support and improved error handling
        """
        try:
            cancellation_token.check_cancelled()
            
            loop = asyncio.get_event_loop()
            
            # Run metadata extraction in executor with timeout
            metadata = await asyncio.wait_for(
                loop.run_in_executor(
                    self.executor, 
                    self._extract_file_metadata_sync_safe, 
                    file_path
                ),
                timeout=10.0  # 10 second timeout for metadata extraction
            )
            
            return metadata
            
        except asyncio.CancelledError:
            raise
        except asyncio.TimeoutError:
            logger.warning(f"Metadata extraction timeout for file: {file_path}")
            return None
        except Exception as e:
            logger.debug(f"Error extracting metadata from {file_path}: {e}")
            return None
    
    async def _extract_file_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract metadata from file (legacy method for compatibility)"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, self._extract_file_metadata_sync, file_path
        )
    
    def _extract_file_metadata_sync_safe(self, file_path: Path) -> Dict[str, Any]:
        """
        Safe synchronous file metadata extraction with improved error handling
        """
        try:
            # Check if file still exists
            if not file_path.exists():
                return {}
            
            stat = file_path.stat()
            mime_type, _ = mimetypes.guess_type(str(file_path))
            
            metadata = {
                'size': stat.st_size,
                'mime_type': mime_type,
                'created_at': datetime.fromtimestamp(stat.st_ctime),
                'modified_at': datetime.fromtimestamp(stat.st_mtime),
                'accessed_at': datetime.fromtimestamp(stat.st_atime)
            }
            
            # Extract content preview for text files (with size and safety checks)
            if (file_path.suffix.lower() in self.text_extensions and 
                stat.st_size < self.max_text_file_size and
                stat.st_size > 0):  # Don't try to read empty files
                try:
                    # Use a more conservative timeout for file reading
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read(self.max_preview_length)
                        if content.strip():  # Only add non-empty content
                            metadata['content_preview'] = content
                except (UnicodeDecodeError, PermissionError, OSError) as e:
                    logger.debug(f"Could not read text content from {file_path}: {e}")
                except Exception as e:
                    logger.debug(f"Unexpected error reading {file_path}: {e}")
            
            return metadata
            
        except (OSError, PermissionError) as e:
            logger.debug(f"Permission or OS error extracting metadata from {file_path}: {e}")
            return {}
        except Exception as e:
            logger.debug(f"Error extracting metadata from {file_path}: {e}")
            return {}
    
    def _extract_file_metadata_sync(self, file_path: Path) -> Dict[str, Any]:
        """Synchronous file metadata extraction (legacy method)"""
        try:
            stat = file_path.stat()
            mime_type, _ = mimetypes.guess_type(str(file_path))
            
            metadata = {
                'size': stat.st_size,
                'mime_type': mime_type,
                'created_at': datetime.fromtimestamp(stat.st_ctime),
                'modified_at': datetime.fromtimestamp(stat.st_mtime),
                'accessed_at': datetime.fromtimestamp(stat.st_atime)
            }
            
            # Extract content preview for text files
            if (file_path.suffix.lower() in self.text_extensions and 
                stat.st_size < self.max_text_file_size):
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read(self.max_preview_length)
                        metadata['content_preview'] = content
                except Exception as e:
                    logger.debug(f"Could not read text content from {file_path}: {e}")
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting metadata from {file_path}: {e}")
            return {}
    
    def _basic_categorize_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Basic file categorization fallback when AI service is unavailable or times out
        """
        extension = file_path.suffix.lower()
        name = file_path.name.lower()
        
        # Basic category mapping
        if extension in self.image_extensions:
            category = 'image'
            priority = 'medium'
        elif extension in self.document_extensions:
            category = 'document'
            priority = 'high'
        elif extension in self.code_extensions:
            category = 'code'
            priority = 'high'
        elif extension in self.text_extensions:
            category = 'text'
            priority = 'medium'
        elif extension in {'.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm'}:
            category = 'video'
            priority = 'medium'
        elif extension in {'.mp3', '.wav', '.flac', '.aac', '.ogg'}:
            category = 'audio'
            priority = 'low'
        elif extension in {'.zip', '.rar', '.7z', '.tar', '.gz'}:
            category = 'archive'
            priority = 'low'
        else:
            category = 'other'
            priority = 'low'
        
        # Basic tags
        tags = [category]
        if 'test' in name:
            tags.append('test')
        if 'backup' in name or 'bak' in name:
            tags.append('backup')
        if 'config' in name or 'settings' in name:
            tags.append('configuration')
        
        return {
            'category': category,
            'description': f'Basic categorization: {category} file',
            'tags': tags,
            'priority': priority,
            'is_technical': extension in self.code_extensions,
            'is_business': extension in self.document_extensions,
            'size_category': 'normal'
        }
    
    def _calculate_importance_score(self, ai_result: Dict[str, Any]) -> int:
        """Calculate importance score based on AI analysis"""
        score = 50  # Base score
        
        # Adjust based on category
        category = ai_result.get('category', '')
        if category in ['document', 'code']:
            score += 20
        elif category in ['image', 'video']:
            score += 10
        
        # Adjust based on priority
        priority = ai_result.get('priority', 'medium')
        if priority == 'high':
            score += 20
        elif priority == 'urgent':
            score += 30
        elif priority == 'low':
            score -= 10
        
        # Adjust based on file size
        size_category = ai_result.get('size_category', 'normal')
        if size_category == 'large':
            score += 15
        elif size_category == 'tiny':
            score -= 5
        
        # Adjust based on technical content
        if ai_result.get('is_technical'):
            score += 10
        
        # Adjust based on business content
        if ai_result.get('is_business'):
            score += 15
        
        return max(0, min(100, score))
    
    async def quick_scan_updates(
        self, 
        user_id: int, 
        since_hours: int = 24,
        cancellation_token: Optional[CancellationToken] = None
    ) -> Dict[str, Any]:
        """
        Quick scan to find recently modified files with cancellation support
        """
        if cancellation_token is None:
            cancellation_token = CancellationToken()
            
        since_time = datetime.utcnow() - timedelta(hours=since_hours)
        
        db = SessionLocal()
        try:
            cancellation_token.check_cancelled()
            
            # Get files that need updating
            recent_files = crud_file.get_recent(db, user_id=user_id, days=since_hours//24 or 1)
            
            updated_count = 0
            error_count = 0
            
            for file_record in recent_files:
                try:
                    cancellation_token.check_cancelled()
                    
                    file_path = Path(file_record.file_path)
                    if file_path.exists():
                        stat = file_path.stat()
                        if stat.st_mtime > since_time.timestamp():
                            # Re-process this file with the optimized method
                            await self._process_single_file_optimized(file_path, user_id, cancellation_token)
                            updated_count += 1
                            
                except asyncio.CancelledError:
                    logger.info("Quick scan was cancelled")
                    break
                except Exception as e:
                    logger.debug(f"Error in quick scan for {file_record.file_path}: {e}")
                    error_count += 1
            
            return {
                'updated_files': updated_count,
                'error_files': error_count,
                'scan_time': datetime.utcnow(),
                'type': 'quick_scan',
                'cancelled': cancellation_token.is_cancelled()
            }
            
        except asyncio.CancelledError:
            return {
                'updated_files': 0,
                'error_files': 0,
                'scan_time': datetime.utcnow(),
                'type': 'quick_scan',
                'cancelled': True
            }
        finally:
            db.close()
    
    def get_scan_status(self) -> Dict[str, Any]:
        """Get current scan status with enhanced progress information"""
        return {
            'scanning': self.scanning,
            'progress': {
                'total_files': self.scan_progress.total_files,
                'processed_files': self.scan_progress.processed_files,
                'current_file': self.scan_progress.current_file,
                'current_batch': self.scan_progress.current_batch,
                'total_batches': self.scan_progress.total_batches,
                'progress_percent': self.scan_progress.progress_percent,
                'estimated_time_remaining': self.scan_progress.estimated_time_remaining,
                'files_per_second': self.scan_progress.files_per_second
            },
            'stats': self.scan_stats,
            'can_cancel': self.current_cancellation_token is not None
        }
    
    def cancel_scan(self) -> bool:
        """
        Cancel the current scan operation
        Returns True if cancellation was initiated, False if no scan is running
        """
        if self.current_cancellation_token and self.scanning:
            self.current_cancellation_token.cancel()
            logger.info("Scan cancellation requested")
            return True
        return False
    
    def create_cancellation_token(self) -> CancellationToken:
        """Create a new cancellation token for external use"""
        return CancellationToken()
    
    async def cleanup_missing_files(
        self, 
        user_id: int,
        cancellation_token: Optional[CancellationToken] = None
    ) -> Dict[str, Any]:
        """
        Remove database entries for files that no longer exist with cancellation support
        """
        if cancellation_token is None:
            cancellation_token = CancellationToken()
            
        db = SessionLocal()
        try:
            cancellation_token.check_cancelled()
            
            all_files = crud_file.get_by_user(db, user_id=user_id, skip=0, limit=10000)
            
            removed_count = 0
            checked_count = 0
            
            for file_record in all_files:
                try:
                    cancellation_token.check_cancelled()
                    
                    if not Path(file_record.file_path).exists():
                        crud_file.remove(db, id=file_record.id)
                        removed_count += 1
                    
                    checked_count += 1
                    
                    # Yield control periodically
                    if checked_count % 100 == 0:
                        await asyncio.sleep(0.01)
                        
                except asyncio.CancelledError:
                    logger.info("Cleanup was cancelled")
                    break
                except Exception as e:
                    logger.debug(f"Error checking file {file_record.file_path}: {e}")
            
            return {
                'removed_files': removed_count,
                'checked_files': checked_count,
                'cleanup_time': datetime.utcnow(),
                'cancelled': cancellation_token.is_cancelled()
            }
            
        except asyncio.CancelledError:
            return {
                'removed_files': 0,
                'checked_files': 0,
                'cleanup_time': datetime.utcnow(),
                'cancelled': True
            }
        finally:
            db.close()


# Global file scanner instance
file_scanner = FileScannerService()