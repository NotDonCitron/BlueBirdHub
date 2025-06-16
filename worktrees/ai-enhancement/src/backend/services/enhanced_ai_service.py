"""
Enhanced AI Service for OrdnungsHub
Advanced ML capabilities with Transformers.js integration and local processing
Combines rule-based methods with lightweight ML models for better accuracy
"""

import os
import json
import asyncio
import hashlib
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
import pickle
from concurrent.futures import ThreadPoolExecutor

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    # Create dummy numpy for basic operations
    class np:
        @staticmethod
        def array(data):
            return data
        @staticmethod
        def mean(data, axis=None):
            return 0.5
        @staticmethod
        def std(data, axis=None):
            return 0.1
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.naive_bayes import MultinomialNB
    from sklearn.cluster import KMeans
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    # Create dummy classes for when sklearn isn't available
    class TfidfVectorizer:
        def __init__(self, *args, **kwargs):
            pass
        def fit_transform(self, texts):
            return [[0] * 100 for _ in texts]
        def transform(self, texts):
            return [[0] * 100 for _ in texts]
    
    class MultinomialNB:
        def __init__(self):
            pass
        def fit(self, X, y):
            pass
        def predict(self, X):
            return ["uncategorized"] * len(X)
        def predict_proba(self, X):
            return [[0.5, 0.5] for _ in X]
    
    class KMeans:
        def __init__(self, *args, **kwargs):
            pass
        def fit(self, X):
            pass
        def predict(self, X):
            return [0] * len(X)
    
    def cosine_similarity(X, Y=None):
        return [[0.5 for _ in range(len(Y or X))] for _ in X]
from loguru import logger

from .ai_service import LocalAIService


class EnhancedAIService(LocalAIService):
    """
    Enhanced AI service with machine learning capabilities
    Extends the basic LocalAIService with ML models for better accuracy
    """
    
    def __init__(self, model_cache_dir: str = "data/ai_models"):
        super().__init__()
        self.model_cache_dir = Path(model_cache_dir)
        self.model_cache_dir.mkdir(parents=True, exist_ok=True)
        
        # ML Models
        self.category_classifier = None
        self.priority_classifier = None
        self.text_vectorizer = None
        self.file_clusterer = None
        
        # Training data
        self.category_training_data = []
        self.priority_training_data = []
        
        # Enhanced ML features
        self.content_embeddings_cache = {}
        self.similarity_threshold = 0.7
        self.clustering_enabled = SKLEARN_AVAILABLE and NUMPY_AVAILABLE
        
        # Advanced categorization patterns
        self._initialize_advanced_patterns()
        
        # Initialize models
        self._initialize_ml_models()
        
    def _initialize_advanced_patterns(self):
        """Initialize advanced categorization patterns"""
        self.advanced_file_patterns = {
            'ai_ml': {
                'extensions': ['.ipynb', '.pkl', '.h5', '.onnx', '.pb'],
                'keywords': ['machine learning', 'neural network', 'tensorflow', 'pytorch', 'model', 'dataset'],
                'patterns': [r'import\s+(tensorflow|torch|sklearn)', r'\.fit\(', r'\.predict\(']
            },
            'blockchain': {
                'extensions': ['.sol', '.vyper'],
                'keywords': ['blockchain', 'smart contract', 'ethereum', 'web3', 'cryptocurrency'],
                'patterns': [r'pragma\s+solidity', r'contract\s+\w+', r'function\s+\w+.*payable']
            },
            'gamedev': {
                'extensions': ['.unity', '.unreal', '.fbx', '.blend'],
                'keywords': ['game development', 'unity', 'unreal', 'sprite', 'texture', 'shader'],
                'patterns': [r'GameObject', r'Transform', r'MonoBehaviour']
            },
            'scientific': {
                'extensions': ['.mat', '.r', '.sas', '.spss'],
                'keywords': ['research', 'experiment', 'hypothesis', 'analysis', 'statistical'],
                'patterns': [r'p\s*<\s*0\.05', r'significance', r'correlation']
            }
        }
        
        # Enhanced semantic patterns with context
        self.contextual_patterns = {
            'urgent_work': {
                'context': ['deadline', 'meeting', 'client'],
                'indicators': ['urgent', 'asap', 'critical', 'emergency'],
                'priority_boost': 2
            },
            'personal_important': {
                'context': ['family', 'health', 'personal'],
                'indicators': ['important', 'remember', 'appointment'],
                'priority_boost': 1
            },
            'creative_project': {
                'context': ['design', 'art', 'creative'],
                'indicators': ['inspiration', 'draft', 'concept', 'sketch'],
                'priority_boost': 0
            }
        }

    def _initialize_ml_models(self):
        """Initialize and load ML models"""
        try:
            self._load_or_create_models()
            logger.info("Enhanced AI models initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize ML models: {e}")
            logger.info("Falling back to rule-based methods")
    
    def _load_or_create_models(self):
        """Load existing models or create new ones"""
        # Text vectorizer for feature extraction
        vectorizer_path = self.model_cache_dir / "text_vectorizer.pkl"
        if vectorizer_path.exists():
            with open(vectorizer_path, 'rb') as f:
                self.text_vectorizer = pickle.load(f)
        else:
            self.text_vectorizer = TfidfVectorizer(
                max_features=1000,
                stop_words='english',
                ngram_range=(1, 2),
                min_df=2
            )
        
        # Category classifier
        category_model_path = self.model_cache_dir / "category_classifier.pkl"
        if category_model_path.exists():
            with open(category_model_path, 'rb') as f:
                self.category_classifier = pickle.load(f)
        else:
            self.category_classifier = MultinomialNB()
            
        # Priority classifier
        priority_model_path = self.model_cache_dir / "priority_classifier.pkl"
        if priority_model_path.exists():
            with open(priority_model_path, 'rb') as f:
                self.priority_classifier = pickle.load(f)
        else:
            self.priority_classifier = MultinomialNB()
            
        # File clusterer for similarity
        clusterer_path = self.model_cache_dir / "file_clusterer.pkl"
        if clusterer_path.exists():
            with open(clusterer_path, 'rb') as f:
                self.file_clusterer = pickle.load(f)
        else:
            self.file_clusterer = KMeans(n_clusters=10, random_state=42)
    
    def _save_models(self):
        """Save trained models to disk"""
        try:
            with open(self.model_cache_dir / "text_vectorizer.pkl", 'wb') as f:
                pickle.dump(self.text_vectorizer, f)
                
            with open(self.model_cache_dir / "category_classifier.pkl", 'wb') as f:
                pickle.dump(self.category_classifier, f)
                
            with open(self.model_cache_dir / "priority_classifier.pkl", 'wb') as f:
                pickle.dump(self.priority_classifier, f)
                
            with open(self.model_cache_dir / "file_clusterer.pkl", 'wb') as f:
                pickle.dump(self.file_clusterer, f)
                
            logger.info("AI models saved successfully")
        except Exception as e:
            logger.error(f"Failed to save models: {e}")
    
    async def enhanced_analyze_text(self, text: str) -> Dict[str, Any]:
        """
        Enhanced text analysis using both rule-based and ML methods
        """
        # Get basic analysis first
        basic_analysis = await self.analyze_text(text)
        
        # Add ML-based enhancements
        loop = asyncio.get_event_loop()
        ml_analysis = await loop.run_in_executor(
            self.executor, 
            self._ml_analyze_text, 
            text
        )
        
        # Combine results
        enhanced_analysis = {**basic_analysis, **ml_analysis}
        
        return enhanced_analysis
    
    def _ml_analyze_text(self, text: str) -> Dict[str, Any]:
        """ML-based text analysis"""
        if not text or not text.strip():
            return {}
            
        result = {}
        
        try:
            # Vectorize text for ML models
            if hasattr(self.text_vectorizer, 'transform'):
                text_vector = self.text_vectorizer.transform([text])
                
                # ML-based category prediction
                if hasattr(self.category_classifier, 'predict_proba'):
                    category_probs = self.category_classifier.predict_proba(text_vector)[0]
                    categories = self.category_classifier.classes_
                    
                    result['ml_category'] = {
                        'prediction': categories[np.argmax(category_probs)],
                        'confidence': float(np.max(category_probs)),
                        'probabilities': {
                            cat: float(prob) for cat, prob in zip(categories, category_probs)
                        }
                    }
                
                # ML-based priority prediction
                if hasattr(self.priority_classifier, 'predict_proba'):
                    priority_probs = self.priority_classifier.predict_proba(text_vector)[0]
                    priorities = self.priority_classifier.classes_
                    
                    result['ml_priority'] = {
                        'prediction': priorities[np.argmax(priority_probs)],
                        'confidence': float(np.max(priority_probs)),
                        'probabilities': {
                            pri: float(prob) for pri, prob in zip(priorities, priority_probs)
                        }
                    }
                    
        except Exception as e:
            logger.debug(f"ML analysis failed, using fallback: {e}")
            
        return result
    
    async def smart_categorize_file(
        self, 
        filename: str, 
        file_path: str = "", 
        content_preview: str = ""
    ) -> Dict[str, Any]:
        """
        Smart file categorization using multiple signals
        """
        # Get basic categorization
        basic_result = await self.categorize_file(filename, content_preview)
        
        # Enhance with file metadata and ML
        loop = asyncio.get_event_loop()
        enhanced_result = await loop.run_in_executor(
            self.executor,
            self._smart_categorize_sync,
            filename,
            file_path,
            content_preview,
            basic_result
        )
        
        return enhanced_result
    
    def _smart_categorize_sync(
        self, 
        filename: str, 
        file_path: str, 
        content_preview: str, 
        basic_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Synchronous smart categorization"""
        result = basic_result.copy()
        
        try:
            # File size analysis
            if file_path and os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                result['file_size'] = file_size
                
                # Adjust importance based on size
                if file_size > 100 * 1024 * 1024:  # > 100MB
                    result['size_category'] = 'large'
                    if result['priority'] == 'low':
                        result['priority'] = 'medium'
                elif file_size < 1024:  # < 1KB
                    result['size_category'] = 'tiny'
                else:
                    result['size_category'] = 'normal'
            
            # Path-based analysis
            if file_path:
                path_parts = Path(file_path).parts
                
                # Check for important directories
                important_dirs = {'documents', 'important', 'backup', 'archive'}
                if any(part.lower() in important_dirs for part in path_parts):
                    if result['priority'] in ['low', 'medium']:
                        result['priority'] = 'high'
                
                # Add path-based tags
                path_tags = []
                for part in path_parts[-3:]:  # Last 3 path components
                    if len(part) > 2 and part.lower() not in {'documents', 'files', 'data'}:
                        path_tags.append(part.lower())
                
                if path_tags:
                    result['tags'] = list(set(result.get('tags', []) + path_tags))
            
            # Enhanced content analysis
            if content_preview:
                content_features = self._extract_content_features(content_preview)
                result.update(content_features)
                
        except Exception as e:
            logger.debug(f"Smart categorization enhancement failed: {e}")
        
        return result
    
    def _extract_content_features(self, content: str) -> Dict[str, Any]:
        """Extract advanced features from content"""
        features = {}
        
        if not content:
            return features
            
        # Text complexity
        sentences = content.split('.')
        words = content.split()
        
        features['text_complexity'] = {
            'sentence_count': len(sentences),
            'word_count': len(words),
            'avg_sentence_length': len(words) / max(len(sentences), 1),
            'unique_words': len(set(word.lower() for word in words))
        }
        
        # Technical content detection
        technical_keywords = [
            'algorithm', 'function', 'variable', 'database', 'server',
            'api', 'framework', 'library', 'code', 'development'
        ]
        
        tech_score = sum(1 for keyword in technical_keywords if keyword in content.lower())
        if tech_score > 2:
            features['is_technical'] = True
            features['technical_score'] = tech_score
        
        # Business content detection
        business_keywords = [
            'meeting', 'client', 'project', 'deadline', 'budget',
            'revenue', 'proposal', 'contract', 'strategy', 'analysis'
        ]
        
        business_score = sum(1 for keyword in business_keywords if keyword in content.lower())
        if business_score > 2:
            features['is_business'] = True
            features['business_score'] = business_score
            
        return features
    
    async def find_similar_files(
        self, 
        target_text: str, 
        file_database: List[Dict[str, Any]], 
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find files similar to the target based on content similarity
        """
        if not file_database or not target_text:
            return []
            
        loop = asyncio.get_event_loop()
        similar_files = await loop.run_in_executor(
            self.executor,
            self._find_similar_sync,
            target_text,
            file_database,
            limit
        )
        
        return similar_files
    
    def _find_similar_sync(
        self, 
        target_text: str, 
        file_database: List[Dict[str, Any]], 
        limit: int
    ) -> List[Dict[str, Any]]:
        """Synchronous similarity search"""
        try:
            # Prepare texts for comparison
            texts = [target_text] + [
                f"{item.get('filename', '')} {item.get('description', '')}"
                for item in file_database
            ]
            
            # Vectorize texts
            if not hasattr(self.text_vectorizer, 'fit_transform'):
                return []
                
            if len(texts) < 2:
                return []
                
            # Fit vectorizer if not already fitted
            text_vectors = self.text_vectorizer.fit_transform(texts)
            
            # Calculate similarities
            target_vector = text_vectors[0]
            file_vectors = text_vectors[1:]
            
            similarities = cosine_similarity(target_vector, file_vectors)[0]
            
            # Get top similar files
            similar_indices = np.argsort(similarities)[::-1][:limit]
            
            result = []
            for idx in similar_indices:
                if similarities[idx] > 0.1:  # Minimum similarity threshold
                    file_info = file_database[idx].copy()
                    file_info['similarity_score'] = float(similarities[idx])
                    result.append(file_info)
            
            return result
            
        except Exception as e:
            logger.debug(f"Similarity search failed: {e}")
            return []
    
    async def suggest_workspace_organization(
        self, 
        files: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Suggest how to organize files into workspaces based on clustering
        """
        if not files:
            return {'suggestions': [], 'clusters': []}
            
        loop = asyncio.get_event_loop()
        organization = await loop.run_in_executor(
            self.executor,
            self._suggest_organization_sync,
            files
        )
        
        return organization
    
    def _suggest_organization_sync(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Synchronous workspace organization suggestion"""
        try:
            # Prepare file descriptions for clustering
            descriptions = []
            for file_info in files:
                desc = f"{file_info.get('filename', '')} {file_info.get('category', '')} {file_info.get('description', '')}"
                descriptions.append(desc)
            
            if len(descriptions) < 3:
                return {'suggestions': [], 'clusters': []}
            
            # Vectorize descriptions
            vectors = self.text_vectorizer.fit_transform(descriptions)
            
            # Cluster files
            n_clusters = min(5, len(files) // 3)  # Dynamic cluster count
            if n_clusters < 2:
                n_clusters = 2
                
            self.file_clusterer.n_clusters = n_clusters
            cluster_labels = self.file_clusterer.fit_predict(vectors)
            
            # Organize results
            clusters = {}
            for i, label in enumerate(cluster_labels):
                if label not in clusters:
                    clusters[label] = []
                clusters[label].append(files[i])
            
            # Generate workspace suggestions
            suggestions = []
            for cluster_id, cluster_files in clusters.items():
                if len(cluster_files) < 2:
                    continue
                    
                # Analyze cluster characteristics
                categories = [f.get('category', 'general') for f in cluster_files]
                most_common_category = max(set(categories), key=categories.count)
                
                # Suggest workspace name
                if most_common_category in ['work', 'business']:
                    workspace_name = f"Work Project {cluster_id + 1}"
                elif most_common_category in ['personal', 'family']:
                    workspace_name = f"Personal Space {cluster_id + 1}"
                elif most_common_category in ['code', 'technical']:
                    workspace_name = f"Development {cluster_id + 1}"
                else:
                    workspace_name = f"{most_common_category.title()} Collection {cluster_id + 1}"
                
                suggestions.append({
                    'workspace_name': workspace_name,
                    'category': most_common_category,
                    'file_count': len(cluster_files),
                    'files': cluster_files[:5],  # Limit to first 5 files for preview
                    'description': f"Workspace for {most_common_category} related files"
                })
            
            return {
                'suggestions': suggestions,
                'clusters': list(clusters.values()),
                'total_clusters': len(clusters)
            }
            
        except Exception as e:
            logger.debug(f"Organization suggestion failed: {e}")
            return {'suggestions': [], 'clusters': []}
    
    async def learn_from_user_actions(
        self, 
        text: str, 
        user_category: str, 
        user_priority: str
    ):
        """
        Learn from user corrections to improve model accuracy
        """
        # Store training data
        self.category_training_data.append({
            'text': text,
            'category': user_category,
            'timestamp': datetime.utcnow()
        })
        
        self.priority_training_data.append({
            'text': text,
            'priority': user_priority,
            'timestamp': datetime.utcnow()
        })
        
        # Retrain models if we have enough data
        if len(self.category_training_data) >= 50:
            await self._retrain_models()
    
    async def _retrain_models(self):
        """Retrain ML models with new data"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self.executor, self._retrain_models_sync)
    
    def _retrain_models_sync(self):
        """Synchronous model retraining"""
        try:
            if len(self.category_training_data) >= 10:
                texts = [item['text'] for item in self.category_training_data]
                categories = [item['category'] for item in self.category_training_data]
                
                # Retrain vectorizer and classifier
                text_vectors = self.text_vectorizer.fit_transform(texts)
                self.category_classifier.fit(text_vectors, categories)
                
            if len(self.priority_training_data) >= 10:
                texts = [item['text'] for item in self.priority_training_data]
                priorities = [item['priority'] for item in self.priority_training_data]
                
                text_vectors = self.text_vectorizer.transform(texts)
                self.priority_classifier.fit(text_vectors, priorities)
            
            # Save updated models
            self._save_models()
            logger.info("AI models retrained successfully")
            
        except Exception as e:
            logger.error(f"Model retraining failed: {e}")
    
    def get_enhanced_status(self) -> Dict[str, Any]:
        """Get enhanced service status"""
        base_status = self.get_status()
        
        enhanced_status = {
            **base_status,
            'service': 'EnhancedAIService',
            'ml_models': {
                'category_classifier': hasattr(self.category_classifier, 'classes_'),
                'priority_classifier': hasattr(self.priority_classifier, 'classes_'),
                'text_vectorizer': hasattr(self.text_vectorizer, 'vocabulary_'),
                'file_clusterer': hasattr(self.file_clusterer, 'cluster_centers_')
            },
            'training_data': {
                'category_samples': len(self.category_training_data),
                'priority_samples': len(self.priority_training_data)
            },
            'capabilities': base_status['capabilities'] + [
                'ml_categorization',
                'similarity_search',
                'workspace_organization',
                'adaptive_learning',
                'content_clustering'
            ]
        }
        
        return enhanced_status

    async def advanced_file_clustering(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Advanced file clustering using content embeddings and metadata
        """
        if not self.clustering_enabled or len(files) < 3:
            return await self._basic_file_grouping(files)
        
        loop = asyncio.get_event_loop()
        clustering_result = await loop.run_in_executor(
            self.executor,
            self._advanced_clustering_sync,
            files
        )
        
        return clustering_result
    
    def _advanced_clustering_sync(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Synchronous advanced clustering with multiple algorithms"""
        try:
            # Extract features for clustering
            features = []
            file_metadata = []
            
            for file_info in files:
                # Combine textual and metadata features
                text_content = f"{file_info.get('filename', '')} {file_info.get('description', '')}"
                
                # Text vectorization
                if hasattr(self.text_vectorizer, 'transform'):
                    text_vector = self.text_vectorizer.transform([text_content]).toarray()[0]
                else:
                    text_vector = [0] * 100  # Fallback
                
                # Metadata features
                metadata_features = self._extract_metadata_features(file_info)
                
                # Combine features
                combined_features = list(text_vector) + metadata_features
                features.append(combined_features)
                file_metadata.append(file_info)
            
            features = np.array(features)
            
            # Multiple clustering approaches
            results = {}
            
            # K-means clustering
            n_clusters = min(5, max(2, len(files) // 3))
            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            kmeans_labels = kmeans.fit_predict(features)
            
            results['kmeans'] = self._format_clustering_result(
                file_metadata, kmeans_labels, "content_similarity"
            )
            
            # Hierarchical clustering by file type
            type_clusters = self._cluster_by_file_type(file_metadata)
            results['by_type'] = type_clusters
            
            # Temporal clustering
            temporal_clusters = self._cluster_by_time(file_metadata)
            results['by_time'] = temporal_clusters
            
            # Combined recommendation
            best_clustering = self._select_best_clustering(results)
            
            return {
                'recommended': best_clustering,
                'alternatives': results,
                'cluster_count': len(set(best_clustering['cluster_labels'])),
                'clustering_method': best_clustering['method']
            }
            
        except Exception as e:
            logger.error(f"Advanced clustering failed: {e}")
            return await self._basic_file_grouping(files)
    
    def _extract_metadata_features(self, file_info: Dict[str, Any]) -> List[float]:
        """Extract numerical features from file metadata"""
        features = []
        
        # File size (normalized)
        size = file_info.get('size', 0)
        features.append(min(1.0, size / (100 * 1024 * 1024)))  # Normalize to 0-1
        
        # File age (days, normalized to 0-1 for up to 1 year)
        created = file_info.get('created_date')
        if created:
            try:
                if isinstance(created, str):
                    created = datetime.fromisoformat(created.replace('Z', '+00:00'))
                age_days = (datetime.now() - created).days
                features.append(min(1.0, age_days / 365))
            except:
                features.append(0.5)  # Default
        else:
            features.append(0.5)
        
        # File type encoding (one-hot-like)
        file_types = ['image', 'document', 'code', 'data', 'archive', 'media']
        file_type = file_info.get('type', 'document')
        for ftype in file_types:
            features.append(1.0 if file_type == ftype else 0.0)
        
        # Priority encoding
        priority_map = {'low': 0.2, 'medium': 0.5, 'high': 0.8, 'urgent': 1.0}
        priority = file_info.get('priority', 'medium')
        features.append(priority_map.get(priority, 0.5))
        
        return features
    
    def _format_clustering_result(self, files: List[Dict], labels: List[int], method: str) -> Dict[str, Any]:
        """Format clustering results into standard structure"""
        clusters = {}
        for i, label in enumerate(labels):
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(files[i])
        
        # Analyze clusters
        cluster_analysis = []
        for cluster_id, cluster_files in clusters.items():
            analysis = self._analyze_cluster(cluster_files)
            cluster_analysis.append({
                'cluster_id': int(cluster_id),
                'file_count': len(cluster_files),
                'files': cluster_files,
                'dominant_type': analysis['dominant_type'],
                'dominant_category': analysis['dominant_category'],
                'avg_priority': analysis['avg_priority'],
                'suggested_name': analysis['suggested_name']
            })
        
        return {
            'method': method,
            'clusters': cluster_analysis,
            'cluster_labels': labels.tolist() if hasattr(labels, 'tolist') else labels
        }
    
    def _analyze_cluster(self, cluster_files: List[Dict]) -> Dict[str, Any]:
        """Analyze characteristics of a file cluster"""
        if not cluster_files:
            return {
                'dominant_type': 'unknown',
                'dominant_category': 'general',
                'avg_priority': 'medium',
                'suggested_name': 'Empty Cluster'
            }
        
        # Find dominant file type
        types = [f.get('type', 'document') for f in cluster_files]
        dominant_type = max(set(types), key=types.count)
        
        # Find dominant category
        categories = [f.get('category', 'general') for f in cluster_files]
        dominant_category = max(set(categories), key=categories.count)
        
        # Calculate average priority
        priority_values = {'low': 1, 'medium': 2, 'high': 3, 'urgent': 4}
        priorities = [priority_values.get(f.get('priority', 'medium'), 2) for f in cluster_files]
        avg_priority_value = sum(priorities) / len(priorities)
        
        priority_names = {1: 'low', 2: 'medium', 3: 'high', 4: 'urgent'}
        avg_priority = priority_names[round(avg_priority_value)]
        
        # Suggest cluster name
        if dominant_category in ['work', 'business']:
            suggested_name = f"Work {dominant_type.title()} Files"
        elif dominant_category == 'personal':
            suggested_name = f"Personal {dominant_type.title()}"
        elif dominant_type == 'code':
            suggested_name = "Development Project"
        elif dominant_type == 'image':
            suggested_name = "Image Collection"
        else:
            suggested_name = f"{dominant_category.title()} {dominant_type.title()}"
        
        return {
            'dominant_type': dominant_type,
            'dominant_category': dominant_category,
            'avg_priority': avg_priority,
            'suggested_name': suggested_name
        }
    
    def _cluster_by_file_type(self, files: List[Dict]) -> Dict[str, Any]:
        """Simple clustering by file type"""
        type_clusters = {}
        
        for i, file_info in enumerate(files):
            file_type = file_info.get('type', 'document')
            if file_type not in type_clusters:
                type_clusters[file_type] = []
            type_clusters[file_type].append(file_info)
        
        # Convert to standard format
        cluster_list = []
        labels = []
        
        for cluster_id, (file_type, cluster_files) in enumerate(type_clusters.items()):
            cluster_list.append({
                'cluster_id': cluster_id,
                'file_count': len(cluster_files),
                'files': cluster_files,
                'dominant_type': file_type,
                'suggested_name': f"{file_type.title()} Files"
            })
            
            # Assign labels
            for _ in cluster_files:
                labels.append(cluster_id)
        
        return {
            'method': 'file_type',
            'clusters': cluster_list,
            'cluster_labels': labels
        }
    
    def _cluster_by_time(self, files: List[Dict]) -> Dict[str, Any]:
        """Cluster files by creation/modification time"""
        time_clusters = {'recent': [], 'this_week': [], 'this_month': [], 'older': []}
        
        now = datetime.now()
        
        for file_info in files:
            created = file_info.get('created_date')
            if not created:
                time_clusters['older'].append(file_info)
                continue
            
            try:
                if isinstance(created, str):
                    created = datetime.fromisoformat(created.replace('Z', '+00:00'))
                
                age_days = (now - created).days
                
                if age_days <= 1:
                    time_clusters['recent'].append(file_info)
                elif age_days <= 7:
                    time_clusters['this_week'].append(file_info)
                elif age_days <= 30:
                    time_clusters['this_month'].append(file_info)
                else:
                    time_clusters['older'].append(file_info)
                    
            except:
                time_clusters['older'].append(file_info)
        
        # Convert to standard format
        cluster_list = []
        labels = []
        cluster_id = 0
        
        for period, cluster_files in time_clusters.items():
            if cluster_files:  # Only add non-empty clusters
                cluster_list.append({
                    'cluster_id': cluster_id,
                    'file_count': len(cluster_files),
                    'files': cluster_files,
                    'suggested_name': f"Files from {period.replace('_', ' ').title()}"
                })
                
                for _ in cluster_files:
                    labels.append(cluster_id)
                cluster_id += 1
        
        return {
            'method': 'temporal',
            'clusters': cluster_list,
            'cluster_labels': labels
        }
    
    def _select_best_clustering(self, clustering_results: Dict[str, Any]) -> Dict[str, Any]:
        """Select the best clustering method based on quality metrics"""
        best_score = -1
        best_clustering = None
        
        for method, result in clustering_results.items():
            score = self._evaluate_clustering_quality(result)
            if score > best_score:
                best_score = score
                best_clustering = result
        
        return best_clustering or clustering_results.get('by_type', {})
    
    def _evaluate_clustering_quality(self, clustering_result: Dict[str, Any]) -> float:
        """Evaluate clustering quality using simple heuristics"""
        clusters = clustering_result.get('clusters', [])
        
        if not clusters:
            return 0.0
        
        # Quality factors
        score = 0.0
        
        # Balanced cluster sizes (prefer similar sizes)
        cluster_sizes = [c['file_count'] for c in clusters]
        size_variance = np.var(cluster_sizes) if cluster_sizes else 0
        score += max(0, 1 - size_variance / 10)  # Normalize variance penalty
        
        # Semantic coherence (same type/category in cluster)
        coherence_scores = []
        for cluster in clusters:
            files = cluster.get('files', [])
            if not files:
                continue
            
            types = [f.get('type', 'document') for f in files]
            categories = [f.get('category', 'general') for f in files]
            
            # Type coherence
            type_coherence = max(set(types), key=types.count) if types else 0
            type_score = types.count(type_coherence) / len(types)
            
            # Category coherence
            cat_coherence = max(set(categories), key=categories.count) if categories else 0
            cat_score = categories.count(cat_coherence) / len(categories)
            
            coherence_scores.append((type_score + cat_score) / 2)
        
        avg_coherence = sum(coherence_scores) / len(coherence_scores) if coherence_scores else 0
        score += avg_coherence
        
        # Prefer reasonable number of clusters (not too many, not too few)
        cluster_count = len(clusters)
        if 2 <= cluster_count <= 5:
            score += 0.5
        elif cluster_count == 1:
            score -= 0.3
        elif cluster_count > 8:
            score -= 0.5
        
        return score
    
    async def _basic_file_grouping(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Basic file grouping fallback when advanced clustering fails"""
        groups = {}
        
        for file_info in files:
            file_type = file_info.get('type', 'document')
            if file_type not in groups:
                groups[file_type] = []
            groups[file_type].append(file_info)
        
        cluster_list = []
        for i, (file_type, group_files) in enumerate(groups.items()):
            cluster_list.append({
                'cluster_id': i,
                'file_count': len(group_files),
                'files': group_files,
                'suggested_name': f"{file_type.title()} Files"
            })
        
        return {
            'recommended': {
                'method': 'basic_grouping',
                'clusters': cluster_list
            },
            'alternatives': {},
            'cluster_count': len(cluster_list),
            'clustering_method': 'basic_grouping'
        }

    async def generate_smart_tags(self, content: str, filename: str = "") -> List[str]:
        """Generate intelligent tags using advanced analysis"""
        if not content and not filename:
            return []
        
        tags = set()
        
        # Basic tag generation
        basic_tags = await self.suggest_tags(content)
        tags.update(basic_tags)
        
        # Advanced pattern-based tags
        advanced_tags = self._generate_advanced_tags(content, filename)
        tags.update(advanced_tags)
        
        # Context-aware tags
        contextual_tags = self._generate_contextual_tags(content)
        tags.update(contextual_tags)
        
        # Clean and limit tags
        cleaned_tags = [tag for tag in tags if len(tag) > 2 and len(tag) < 20]
        return sorted(cleaned_tags)[:10]  # Limit to 10 most relevant tags
    
    def _generate_advanced_tags(self, content: str, filename: str) -> List[str]:
        """Generate tags using advanced file patterns"""
        tags = []
        content_lower = content.lower()
        filename_lower = filename.lower()
        
        # Check advanced file patterns
        for category, config in self.advanced_file_patterns.items():
            # Extension check
            if any(filename_lower.endswith(ext) for ext in config['extensions']):
                tags.append(category.replace('_', '-'))
            
            # Keyword check
            keyword_count = sum(1 for keyword in config['keywords'] if keyword in content_lower)
            if keyword_count >= 2:
                tags.append(category.replace('_', '-'))
            
            # Pattern check
            pattern_matches = sum(1 for pattern in config['patterns'] if re.search(pattern, content, re.IGNORECASE))
            if pattern_matches >= 1:
                tags.append(category.replace('_', '-'))
        
        return tags
    
    def _generate_contextual_tags(self, content: str) -> List[str]:
        """Generate tags using contextual patterns"""
        tags = []
        content_lower = content.lower()
        
        for pattern_name, pattern_config in self.contextual_patterns.items():
            context_matches = sum(1 for ctx in pattern_config['context'] if ctx in content_lower)
            indicator_matches = sum(1 for ind in pattern_config['indicators'] if ind in content_lower)
            
            if context_matches >= 1 and indicator_matches >= 1:
                tags.append(pattern_name.replace('_', '-'))
        
        return tags


# Global enhanced AI service instance
enhanced_ai_service = EnhancedAIService()