"""
Enhanced AI Service for OrdnungsHub
Combines rule-based methods with lightweight ML models for better accuracy
"""

import os
import json
import asyncio
import hashlib
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
        
        # Initialize models
        self._initialize_ml_models()
        
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


# Global enhanced AI service instance
enhanced_ai_service = EnhancedAIService()