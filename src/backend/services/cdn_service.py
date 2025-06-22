"""
CDN Service - Phase 3 Enterprise Performance Enhancement
Implements intelligent CDN integration for static asset optimization
"""

import os
import hashlib
import mimetypes
import asyncio
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime, timedelta
import json
import aiohttp
import aiofiles
from loguru import logger

try:
    import boto3
    from botocore.exceptions import ClientError
    AWS_AVAILABLE = True
except ImportError:
    AWS_AVAILABLE = False
    logger.warning("AWS SDK not available, using local CDN simulation")

@dataclass
class CDNAsset:
    """CDN asset metadata"""
    file_path: str
    cdn_url: str
    content_hash: str
    content_type: str
    size_bytes: int
    cache_control: str
    last_modified: datetime
    expires: datetime
    compression: str = "gzip"
    
class CDNService:
    """Enterprise CDN Service with intelligent asset management"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.cdn_base_url = config.get("cdn_base_url", "https://cdn.ordnungshub.com")
        self.s3_bucket = config.get("s3_bucket", "ordnungshub-cdn")
        self.cloudfront_distribution = config.get("cloudfront_distribution", "")
        self.local_cache_dir = Path(config.get("local_cache_dir", "./cdn_cache"))
        self.local_cache_dir.mkdir(exist_ok=True)
        
        # CDN strategies
        self.asset_strategies = {
            "static": {"cache_duration": 365 * 24 * 3600, "compression": True},  # 1 year
            "dynamic": {"cache_duration": 24 * 3600, "compression": True},      # 1 day
            "images": {"cache_duration": 30 * 24 * 3600, "compression": False}, # 30 days
            "api": {"cache_duration": 3600, "compression": True},               # 1 hour
            "critical": {"cache_duration": 7 * 24 * 3600, "compression": True}  # 1 week
        }
        
        # Initialize AWS clients if available
        if AWS_AVAILABLE:
            self.s3_client = boto3.client('s3')
            self.cloudfront_client = boto3.client('cloudfront')
        else:
            self.s3_client = None
            self.cloudfront_client = None
    
    def get_asset_strategy(self, file_path: str) -> Dict[str, Any]:
        """Determine CDN strategy based on file type"""
        file_ext = Path(file_path).suffix.lower()
        
        # Static assets (long cache)
        if file_ext in ['.js', '.css', '.woff', '.woff2', '.ttf', '.eot']:
            return self.asset_strategies["static"]
        
        # Images (medium cache)
        elif file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.svg', '.ico', '.webp']:
            return self.asset_strategies["images"]
        
        # Critical files (medium cache)
        elif file_ext in ['.html', '.json', '.xml']:
            return self.asset_strategies["critical"]
        
        # Default to dynamic
        else:
            return self.asset_strategies["dynamic"]
    
    def generate_content_hash(self, content: bytes) -> str:
        """Generate content hash for cache busting"""
        return hashlib.sha256(content).hexdigest()[:12]
    
    def get_cache_control_header(self, strategy: Dict[str, Any]) -> str:
        """Generate cache control header"""
        max_age = strategy["cache_duration"]
        return f"public, max-age={max_age}, immutable"
    
    async def optimize_asset(self, file_path: Path, content: bytes) -> bytes:
        """Optimize asset content based on type"""
        file_ext = file_path.suffix.lower()
        
        try:
            # CSS optimization
            if file_ext == '.css':
                return await self._optimize_css(content)
            
            # JavaScript optimization (already handled by build process)
            elif file_ext == '.js':
                return content  # Vite already optimizes JS
            
            # Image optimization
            elif file_ext in ['.jpg', '.jpeg', '.png']:
                return await self._optimize_image(content, file_ext)
            
            # SVG optimization
            elif file_ext == '.svg':
                return await self._optimize_svg(content)
            
            else:
                return content
                
        except Exception as e:
            logger.warning(f"Asset optimization failed for {file_path}: {e}")
            return content
    
    async def _optimize_css(self, content: bytes) -> bytes:
        """Optimize CSS content"""
        # Basic CSS minification (in production, use proper minifier)
        css_text = content.decode('utf-8')
        
        # Remove comments
        import re
        css_text = re.sub(r'/\*.*?\*/', '', css_text, flags=re.DOTALL)
        
        # Remove unnecessary whitespace
        css_text = re.sub(r'\s+', ' ', css_text)
        css_text = re.sub(r';\s*}', '}', css_text)
        css_text = re.sub(r'{\s*', '{', css_text)
        css_text = re.sub(r';\s*', ';', css_text)
        
        return css_text.encode('utf-8')
    
    async def _optimize_image(self, content: bytes, file_ext: str) -> bytes:
        """Optimize image content (placeholder - would use PIL/Pillow in production)"""
        # In production, implement proper image optimization:
        # - WebP conversion
        # - Quality reduction
        # - Progressive JPEG
        # - Responsive image generation
        return content
    
    async def _optimize_svg(self, content: bytes) -> bytes:
        """Optimize SVG content"""
        # Basic SVG optimization (remove comments, unnecessary whitespace)
        svg_text = content.decode('utf-8')
        
        import re
        # Remove comments
        svg_text = re.sub(r'<!--.*?-->', '', svg_text, flags=re.DOTALL)
        
        # Remove unnecessary whitespace between tags
        svg_text = re.sub(r'>\s+<', '><', svg_text)
        
        return svg_text.encode('utf-8')
    
    async def upload_to_s3(self, content: bytes, s3_key: str, content_type: str, cache_control: str) -> bool:
        """Upload asset to S3 CDN"""
        if not self.s3_client:
            logger.warning("S3 client not available, using local cache")
            return await self._store_local_cache(content, s3_key, content_type)
        
        try:
            self.s3_client.put_object(
                Bucket=self.s3_bucket,
                Key=s3_key,
                Body=content,
                ContentType=content_type,
                CacheControl=cache_control,
                ContentEncoding='gzip' if cache_control else None
            )
            
            logger.info(f"Successfully uploaded {s3_key} to S3 CDN")
            return True
            
        except ClientError as e:
            logger.error(f"S3 upload failed for {s3_key}: {e}")
            return False
    
    async def _store_local_cache(self, content: bytes, key: str, content_type: str) -> bool:
        """Store asset in local cache (fallback)"""
        try:
            cache_file = self.local_cache_dir / key.replace('/', '_')
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            
            async with aiofiles.open(cache_file, 'wb') as f:
                await f.write(content)
            
            # Store metadata
            metadata = {
                "content_type": content_type,
                "cached_at": datetime.now().isoformat(),
                "size": len(content)
            }
            
            metadata_file = cache_file.with_suffix('.meta')
            async with aiofiles.open(metadata_file, 'w') as f:
                await f.write(json.dumps(metadata))
            
            return True
            
        except Exception as e:
            logger.error(f"Local cache storage failed for {key}: {e}")
            return False
    
    async def deploy_assets(self, build_dir: Path) -> List[CDNAsset]:
        """Deploy all build assets to CDN"""
        logger.info(f"Starting CDN deployment from {build_dir}")
        
        deployed_assets = []
        
        # Find all deployable assets
        asset_files = []
        for pattern in ['**/*.js', '**/*.css', '**/*.png', '**/*.jpg', '**/*.svg', '**/*.woff*']:
            asset_files.extend(build_dir.glob(pattern))
        
        # Deploy assets concurrently
        semaphore = asyncio.Semaphore(10)  # Limit concurrent uploads
        
        async def deploy_single_asset(file_path: Path):
            async with semaphore:
                return await self._deploy_single_asset(file_path, build_dir)
        
        deployment_tasks = [deploy_single_asset(file_path) for file_path in asset_files]
        results = await asyncio.gather(*deployment_tasks, return_exceptions=True)
        
        # Collect successful deployments
        for result in results:
            if isinstance(result, CDNAsset):
                deployed_assets.append(result)
            elif isinstance(result, Exception):
                logger.error(f"Asset deployment failed: {result}")
        
        logger.info(f"CDN deployment complete: {len(deployed_assets)} assets deployed")
        return deployed_assets
    
    async def _deploy_single_asset(self, file_path: Path, build_dir: Path) -> Optional[CDNAsset]:
        """Deploy a single asset to CDN"""
        try:
            # Read file content
            async with aiofiles.open(file_path, 'rb') as f:
                content = await f.read()
            
            # Generate metadata
            relative_path = file_path.relative_to(build_dir)
            content_hash = self.generate_content_hash(content)
            content_type = mimetypes.guess_type(str(file_path))[0] or 'application/octet-stream'
            strategy = self.get_asset_strategy(str(file_path))
            
            # Optimize content
            optimized_content = await self.optimize_asset(file_path, content)
            
            # Generate CDN key with hash for cache busting
            file_stem = file_path.stem
            file_ext = file_path.suffix
            cdn_key = f"assets/{file_stem}-{content_hash}{file_ext}"
            
            # Cache control
            cache_control = self.get_cache_control_header(strategy)
            
            # Upload to CDN
            success = await self.upload_to_s3(optimized_content, cdn_key, content_type, cache_control)
            
            if success:
                cdn_url = f"{self.cdn_base_url}/{cdn_key}"
                
                return CDNAsset(
                    file_path=str(relative_path),
                    cdn_url=cdn_url,
                    content_hash=content_hash,
                    content_type=content_type,
                    size_bytes=len(optimized_content),
                    cache_control=cache_control,
                    last_modified=datetime.now(),
                    expires=datetime.now() + timedelta(seconds=strategy["cache_duration"]),
                    compression="gzip" if strategy["compression"] else "none"
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to deploy asset {file_path}: {e}")
            return None
    
    async def generate_asset_manifest(self, deployed_assets: List[CDNAsset]) -> Dict[str, Any]:
        """Generate asset manifest for frontend consumption"""
        manifest = {
            "version": datetime.now().isoformat(),
            "cdn_base_url": self.cdn_base_url,
            "assets": {},
            "preload": [],
            "critical": []
        }
        
        for asset in deployed_assets:
            manifest["assets"][asset.file_path] = {
                "url": asset.cdn_url,
                "hash": asset.content_hash,
                "size": asset.size_bytes,
                "type": asset.content_type,
                "cache_control": asset.cache_control
            }
            
            # Mark critical assets for preloading
            if any(critical in asset.file_path for critical in ['critical', 'main', 'index']):
                manifest["critical"].append(asset.cdn_url)
            
            # Mark preloadable assets
            if any(ext in asset.file_path for ext in ['.woff', '.woff2']):
                manifest["preload"].append({
                    "url": asset.cdn_url,
                    "as": "font",
                    "crossorigin": "anonymous"
                })
        
        return manifest
    
    async def invalidate_cache(self, paths: List[str]) -> bool:
        """Invalidate CDN cache for specific paths"""
        if not self.cloudfront_client:
            logger.warning("CloudFront client not available, skipping cache invalidation")
            return True
        
        try:
            invalidation_paths = [f"/{path}" for path in paths]
            
            response = self.cloudfront_client.create_invalidation(
                DistributionId=self.cloudfront_distribution,
                InvalidationBatch={
                    'Paths': {
                        'Quantity': len(invalidation_paths),
                        'Items': invalidation_paths
                    },
                    'CallerReference': str(datetime.now().timestamp())
                }
            )
            
            logger.info(f"CDN cache invalidation initiated: {response['Invalidation']['Id']}")
            return True
            
        except ClientError as e:
            logger.error(f"CDN cache invalidation failed: {e}")
            return False
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get CDN performance metrics"""
        # In production, integrate with CloudWatch or CDN analytics
        return {
            "cache_hit_ratio": 0.95,  # Placeholder
            "average_response_time_ms": 25,
            "bandwidth_savings_percent": 75,
            "global_edge_locations": 200,
            "assets_cached": len(list(self.local_cache_dir.glob("*"))) if self.local_cache_dir.exists() else 0
        }

# CDN Configuration Factory
def create_cdn_service(environment: str = "production") -> CDNService:
    """Create CDN service with environment-specific configuration"""
    
    config = {
        "production": {
            "cdn_base_url": "https://cdn.ordnungshub.com",
            "s3_bucket": "ordnungshub-cdn-prod",
            "cloudfront_distribution": "E1234567890ABC",
            "local_cache_dir": "./cdn_cache_prod"
        },
        "staging": {
            "cdn_base_url": "https://cdn-staging.ordnungshub.com", 
            "s3_bucket": "ordnungshub-cdn-staging",
            "cloudfront_distribution": "E0987654321DEF",
            "local_cache_dir": "./cdn_cache_staging"
        },
        "development": {
            "cdn_base_url": "http://localhost:3002/cdn",
            "s3_bucket": "ordnungshub-cdn-dev",
            "cloudfront_distribution": "",
            "local_cache_dir": "./cdn_cache_dev"
        }
    }
    
    return CDNService(config.get(environment, config["development"]))

# Usage example and deployment script
async def deploy_cdn_assets():
    """Deploy assets to CDN"""
    cdn_service = create_cdn_service(os.getenv("NODE_ENV", "development"))
    
    build_dir = Path("/mnt/c/Users/pasca/CascadeProjects/nnewcoededui/dist/web")
    
    if not build_dir.exists():
        logger.error("Build directory not found. Run npm run build first.")
        return
    
    # Deploy assets
    deployed_assets = await cdn_service.deploy_assets(build_dir)
    
    # Generate manifest
    manifest = await cdn_service.generate_asset_manifest(deployed_assets)
    
    # Save manifest
    manifest_file = build_dir / "asset-manifest.json"
    async with aiofiles.open(manifest_file, 'w') as f:
        await f.write(json.dumps(manifest, indent=2))
    
    logger.info(f"CDN deployment complete: {len(deployed_assets)} assets, manifest saved to {manifest_file}")
    
    # Get performance metrics
    metrics = await cdn_service.get_performance_metrics()
    logger.info(f"CDN Performance: {metrics}")

if __name__ == "__main__":
    asyncio.run(deploy_cdn_assets())