"""
Smart File Organization Service using AI-powered categorization and semantic analysis
"""

import os
import mimetypes
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json
import hashlib

from loguru import logger

# Temporarily disable AI dependencies until they're properly installed
AI_DEPS_AVAILABLE = False
logger.info("AI dependencies disabled for now. Smart file organization will use rule-based fallback.")

# Import numpy as a fallback to prevent NameError when AI deps are disabled
try:
    import numpy as np
    from sentence_transformers import SentenceTransformer
    from sklearn.cluster import KMeans
    from sklearn.metrics.pairwise import cosine_similarity
except ImportError:
    # Create dummy np object to prevent NameError
    class DummyNp:
        ndarray = type
    np = DummyNp()

class SmartFileOrganizer:
    """
    AI-powered file organization service with fallback to rule-based categorization
    """
    
    def __init__(self):
        self.ai_available = AI_DEPS_AVAILABLE
        self.model = None
        self.file_embeddings = {}
        self.categories = {}
        
        if self.ai_available:
            try:
                # Use a lightweight model for local processing
                self.model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("Smart file organizer initialized with AI capabilities")
            except Exception as e:
                logger.warning(f"Failed to load AI model: {e}. Using rule-based fallback.")
                self.ai_available = False
        
        # Define standard categories for organization
        self.standard_categories = {
            'documents': {
                'extensions': ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt'],
                'keywords': ['document', 'text', 'report', 'letter', 'contract']
            },
            'images': {
                'extensions': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp'],
                'keywords': ['image', 'photo', 'picture', 'graphic', 'screenshot']
            },
            'videos': {
                'extensions': ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv'],
                'keywords': ['video', 'movie', 'clip', 'recording', 'film']
            },
            'audio': {
                'extensions': ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a'],
                'keywords': ['audio', 'music', 'sound', 'podcast', 'song']
            },
            'code': {
                'extensions': ['.py', '.js', '.html', '.css', '.cpp', '.java', '.go', '.rs'],
                'keywords': ['code', 'script', 'program', 'source', 'development']
            },
            'archives': {
                'extensions': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2'],
                'keywords': ['archive', 'compressed', 'backup', 'package']
            },
            'spreadsheets': {
                'extensions': ['.xls', '.xlsx', '.csv', '.ods'],
                'keywords': ['spreadsheet', 'data', 'table', 'calculation', 'budget']
            },
            'presentations': {
                'extensions': ['.ppt', '.pptx', '.odp'],
                'keywords': ['presentation', 'slides', 'deck', 'meeting']
            }
        }
    
    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        """
        Analyze a single file and return categorization information
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            return {'error': 'File not found'}
        
        # Basic file information
        file_info = {
            'name': file_path.name,
            'stem': file_path.stem,
            'suffix': file_path.suffix.lower(),
            'size': file_path.stat().st_size,
            'modified': datetime.fromtimestamp(file_path.stat().st_mtime),
            'mime_type': mimetypes.guess_type(str(file_path))[0]
        }
        
        # Rule-based categorization
        rule_category = self._categorize_by_rules(file_info)
        
        result = {
            'file_info': file_info,
            'suggested_category': rule_category,
            'confidence': 0.8 if rule_category != 'other' else 0.3,
            'reasoning': self._get_categorization_reasoning(file_info, rule_category)
        }
        
        # AI-enhanced analysis if available
        if self.ai_available and self.model:
            try:
                ai_analysis = self._ai_analyze_file(file_path, file_info)
                result.update(ai_analysis)
            except Exception as e:
                logger.warning(f"AI analysis failed for {file_path}: {e}")
        
        return result
    
    def organize_directory(self, directory_path: str, dry_run: bool = True) -> Dict[str, Any]:
        """
        Analyze and organize all files in a directory
        """
        directory_path = Path(directory_path)
        
        if not directory_path.exists() or not directory_path.is_dir():
            return {'error': 'Directory not found'}
        
        # Get all files recursively
        files = list(directory_path.rglob('*'))
        files = [f for f in files if f.is_file()]
        
        organization_plan = {
            'total_files': len(files),
            'categories': {},
            'suggestions': [],
            'dry_run': dry_run,
            'timestamp': datetime.now().isoformat()
        }
        
        # Analyze each file
        for file_path in files:
            try:
                analysis = self.analyze_file(str(file_path))
                category = analysis.get('suggested_category', 'other')
                
                if category not in organization_plan['categories']:
                    organization_plan['categories'][category] = []
                
                organization_plan['categories'][category].append({
                    'path': str(file_path.relative_to(directory_path)),
                    'analysis': analysis
                })
                
            except Exception as e:
                logger.error(f"Failed to analyze {file_path}: {e}")
        
        # Generate organization suggestions
        organization_plan['suggestions'] = self._generate_organization_suggestions(
            organization_plan['categories']
        )
        
        # If not dry run, actually move files
        if not dry_run:
            move_results = self._execute_organization(directory_path, organization_plan)
            organization_plan['move_results'] = move_results
        
        return organization_plan
    
    def suggest_smart_folders(self, files_analysis: List[Dict]) -> List[Dict]:
        """
        Use AI clustering to suggest intelligent folder structures
        """
        if not self.ai_available or not files_analysis:
            return self._rule_based_folder_suggestions(files_analysis)
        
        try:
            # Extract file descriptions for clustering
            descriptions = []
            file_data = []
            
            for analysis in files_analysis:
                file_info = analysis.get('file_info', {})
                desc = f"{file_info.get('stem', '')} {file_info.get('suffix', '')}"
                descriptions.append(desc)
                file_data.append(analysis)
            
            # Generate embeddings
            embeddings = self.model.encode(descriptions)
            
            # Perform clustering
            n_clusters = min(8, len(descriptions) // 5 + 1)  # Dynamic cluster count
            if n_clusters > 1:
                kmeans = KMeans(n_clusters=n_clusters, random_state=42)
                cluster_labels = kmeans.fit_predict(embeddings)
                
                # Group files by cluster
                clusters = {}
                for i, label in enumerate(cluster_labels):
                    if label not in clusters:
                        clusters[label] = []
                    clusters[label].append(file_data[i])
                
                # Generate folder suggestions
                folder_suggestions = []
                for cluster_id, cluster_files in clusters.items():
                    folder_name = self._generate_cluster_name(cluster_files)
                    folder_suggestions.append({
                        'folder_name': folder_name,
                        'files': cluster_files,
                        'confidence': 0.7,
                        'method': 'ai_clustering'
                    })
                
                return folder_suggestions
                
        except Exception as e:
            logger.error(f"AI clustering failed: {e}")
            return self._rule_based_folder_suggestions(files_analysis)
        
        return self._rule_based_folder_suggestions(files_analysis)
    
    def _categorize_by_rules(self, file_info: Dict) -> str:
        """Rule-based file categorization"""
        suffix = file_info.get('suffix', '').lower()
        name = file_info.get('name', '').lower()
        
        for category, rules in self.standard_categories.items():
            # Check file extension
            if suffix in rules['extensions']:
                return category
            
            # Check keywords in filename
            if any(keyword in name for keyword in rules['keywords']):
                return category
        
        return 'other'
    
    def _ai_analyze_file(self, file_path: Path, file_info: Dict) -> Dict:
        """AI-enhanced file analysis"""
        try:
            # Create a description for the file
            description = f"File: {file_info['name']} Type: {file_info.get('mime_type', 'unknown')}"
            
            # Generate embedding
            embedding = self.model.encode([description])
            
            # Store embedding for future similarity searches
            file_hash = hashlib.md5(str(file_path).encode()).hexdigest()
            self.file_embeddings[file_hash] = embedding[0]
            
            # Enhanced categorization using semantic similarity
            category_descriptions = [
                f"This is a {cat} file used for {' '.join(rules['keywords'])}"
                for cat, rules in self.standard_categories.items()
            ]
            
            category_embeddings = self.model.encode(category_descriptions)
            similarities = cosine_similarity(embedding, category_embeddings)[0]
            
            best_match_idx = np.argmax(similarities)
            best_category = list(self.standard_categories.keys())[best_match_idx]
            confidence = float(similarities[best_match_idx])
            
            return {
                'ai_suggested_category': best_category,
                'ai_confidence': confidence,
                'embedding_hash': file_hash,
                'similar_files': self._find_similar_files(embedding[0], file_hash)
            }
            
        except Exception as e:
            logger.error(f"AI analysis error: {e}")
            return {}
    
    def _find_similar_files(self, file_embedding: np.ndarray, exclude_hash: str, top_k: int = 3) -> List[str]:
        """Find similar files using embedding similarity"""
        similarities = []
        
        for file_hash, embedding in self.file_embeddings.items():
            if file_hash != exclude_hash:
                similarity = cosine_similarity([file_embedding], [embedding])[0][0]
                similarities.append((file_hash, similarity))
        
        # Sort by similarity and return top k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return [file_hash for file_hash, _ in similarities[:top_k]]
    
    def _get_categorization_reasoning(self, file_info: Dict, category: str) -> str:
        """Generate human-readable reasoning for categorization"""
        suffix = file_info.get('suffix', '')
        
        if category == 'other':
            return f"File type {suffix} not recognized, placed in general category"
        
        rules = self.standard_categories.get(category, {})
        
        if suffix in rules.get('extensions', []):
            return f"Categorized as '{category}' based on file extension {suffix}"
        
        return f"Categorized as '{category}' based on filename analysis"
    
    def _generate_organization_suggestions(self, categories: Dict) -> List[Dict]:
        """Generate actionable organization suggestions"""
        suggestions = []
        
        for category, files in categories.items():
            if len(files) > 5:  # Only suggest folders for categories with many files
                suggestions.append({
                    'type': 'create_folder',
                    'folder_name': category.title(),
                    'file_count': len(files),
                    'description': f"Create '{category.title()}' folder for {len(files)} {category} files"
                })
        
        # Suggest cleanup for 'other' category
        if 'other' in categories and len(categories['other']) > 10:
            suggestions.append({
                'type': 'review_uncategorized',
                'file_count': len(categories['other']),
                'description': f"Review {len(categories['other'])} uncategorized files for manual organization"
            })
        
        return suggestions
    
    def _rule_based_folder_suggestions(self, files_analysis: List[Dict]) -> List[Dict]:
        """Fallback folder suggestions using rules"""
        category_groups = {}
        
        for analysis in files_analysis:
            category = analysis.get('suggested_category', 'other')
            if category not in category_groups:
                category_groups[category] = []
            category_groups[category].append(analysis)
        
        suggestions = []
        for category, files in category_groups.items():
            if len(files) > 1:
                suggestions.append({
                    'folder_name': category.title(),
                    'files': files,
                    'confidence': 0.6,
                    'method': 'rule_based'
                })
        
        return suggestions
    
    def _generate_cluster_name(self, cluster_files: List[Dict]) -> str:
        """Generate a meaningful name for a file cluster"""
        # Extract common patterns from filenames
        names = [f['file_info']['stem'].lower() for f in cluster_files if 'file_info' in f]
        
        # Find common words
        all_words = []
        for name in names:
            words = name.replace('_', ' ').replace('-', ' ').split()
            all_words.extend(words)
        
        # Count word frequency
        word_counts = {}
        for word in all_words:
            if len(word) > 2:  # Ignore very short words
                word_counts[word] = word_counts.get(word, 0) + 1
        
        if word_counts:
            most_common = max(word_counts.items(), key=lambda x: x[1])
            if most_common[1] > 1:  # Word appears multiple times
                return most_common[0].title()
        
        # Fallback to file type
        extensions = [f['file_info']['suffix'] for f in cluster_files if 'file_info' in f]
        if extensions:
            most_common_ext = max(set(extensions), key=extensions.count)
            return f"{most_common_ext[1:].upper()} Files"
        
        return "Mixed Files"
    
    def _execute_organization(self, base_path: Path, organization_plan: Dict) -> Dict:
        """Actually move files according to the organization plan"""
        results = {
            'moved_files': 0,
            'created_folders': 0,
            'errors': []
        }
        
        try:
            for category, files in organization_plan['categories'].items():
                if len(files) > 1:  # Only create folders for categories with multiple files
                    category_folder = base_path / category.title()
                    category_folder.mkdir(exist_ok=True)
                    results['created_folders'] += 1
                    
                    for file_info in files:
                        src_path = base_path / file_info['path']
                        dst_path = category_folder / src_path.name
                        
                        try:
                            src_path.rename(dst_path)
                            results['moved_files'] += 1
                        except Exception as e:
                            results['errors'].append(f"Failed to move {src_path}: {e}")
                            
        except Exception as e:
            results['errors'].append(f"Organization execution failed: {e}")
            
        return results

# Global instance
smart_organizer = SmartFileOrganizer()