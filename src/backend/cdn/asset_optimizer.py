"""
CDN Asset Optimization and Management - Phase 2 Performance Enhancement
Handles static asset optimization, CDN integration, and intelligent caching
"""

import os
import hashlib
import json
import gzip
import brotli
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from loguru import logger
import aiofiles
import asyncio

class CDNAssetOptimizer:
    """
    Optimizes and manages static assets for CDN delivery
    """
    
    def __init__(self, static_dir: str = "static", cdn_base_url: Optional[str] = None):
        self.static_dir = Path(static_dir)
        self.cdn_base_url = cdn_base_url or os.getenv("CDN_BASE_URL", "")
        self.manifest_file = self.static_dir / "asset-manifest.json"
        self.optimization_config = self._load_optimization_config()
        
    def _load_optimization_config(self) -> Dict[str, Any]:
        """Load optimization configuration"""
        return {
            "compression": {
                "gzip": True,
                "brotli": True,
                "quality": 9
            },
            "cache_control": {
                "css": "public, max-age=31536000, immutable",  # 1 year
                "js": "public, max-age=31536000, immutable",   # 1 year
                "images": "public, max-age=2592000",           # 30 days
                "fonts": "public, max-age=31536000, immutable", # 1 year
                "html": "public, max-age=3600"                 # 1 hour
            },
            "optimization": {
                "enable_content_hash": True,
                "enable_compression": True,
                "enable_source_maps": False,  # Disable in production
                "min_compression_size": 1024  # 1KB minimum for compression
            }
        }
    
    async def optimize_static_assets(self) -> Dict[str, Any]:
        """
        Optimize all static assets for CDN delivery
        """
        optimization_results = {
            "started_at": datetime.now(),
            "processed_files": [],
            "compression_results": {},
            "manifest": {},
            "total_savings": 0,
            "errors": []
        }
        
        try:
            logger.info("Starting static asset optimization for CDN...")
            
            # Ensure static directory exists
            self.static_dir.mkdir(parents=True, exist_ok=True)
            
            # Find all static assets
            asset_files = await self._find_static_assets()
            
            # Process each asset file
            for asset_path in asset_files:
                try:
                    result = await self._optimize_asset(asset_path)
                    optimization_results["processed_files"].append(result)
                    optimization_results["total_savings"] += result.get("size_savings", 0)
                except Exception as e:
                    error_info = {"file": str(asset_path), "error": str(e)}
                    optimization_results["errors"].append(error_info)
                    logger.error(f"Failed to optimize {asset_path}: {e}")
            
            # Generate asset manifest
            optimization_results["manifest"] = await self._generate_asset_manifest(
                optimization_results["processed_files"]
            )
            
            # Save manifest file
            await self._save_manifest(optimization_results["manifest"])
            
            optimization_results["completed_at"] = datetime.now()
            optimization_results["status"] = "SUCCESS"
            
            logger.info(f"Asset optimization completed. Processed {len(optimization_results['processed_files'])} files.")
            logger.info(f"Total size savings: {optimization_results['total_savings'] / 1024:.2f} KB")
            
        except Exception as e:
            logger.error(f"Asset optimization failed: {e}")
            optimization_results["status"] = "FAILED"
            optimization_results["error"] = str(e)
        
        return optimization_results
    
    async def _find_static_assets(self) -> List[Path]:
        """Find all static asset files"""
        asset_extensions = {'.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', 
                          '.woff', '.woff2', '.ttf', '.eot', '.ico', '.json'}
        
        asset_files = []
        
        for root, dirs, files in os.walk(self.static_dir):
            for file in files:
                file_path = Path(root) / file
                if file_path.suffix.lower() in asset_extensions:
                    asset_files.append(file_path)
        
        return asset_files
    
    async def _optimize_asset(self, asset_path: Path) -> Dict[str, Any]:
        """
        Optimize a single asset file
        """
        result = {
            "file": str(asset_path.relative_to(self.static_dir)),
            "original_size": 0,
            "optimized_size": 0,
            "size_savings": 0,
            "compression_ratio": 0,
            "content_hash": "",
            "optimized_path": "",
            "cdn_url": "",
            "cache_control": "",
            "compressed_variants": []
        }
        
        try:
            # Get original file size
            result["original_size"] = asset_path.stat().st_size
            
            # Generate content hash
            content_hash = await self._generate_content_hash(asset_path)
            result["content_hash"] = content_hash
            
            # Create optimized filename with hash
            optimized_name = self._create_optimized_filename(asset_path, content_hash)
            optimized_path = asset_path.parent / optimized_name
            result["optimized_path"] = str(optimized_path.relative_to(self.static_dir))
            
            # Copy/rename to optimized filename
            if not optimized_path.exists() or asset_path != optimized_path:
                async with aiofiles.open(asset_path, 'rb') as src:
                    content = await src.read()
                async with aiofiles.open(optimized_path, 'wb') as dst:
                    await dst.write(content)
            
            result["optimized_size"] = optimized_path.stat().st_size
            
            # Create compressed variants
            if (result["original_size"] >= self.optimization_config["optimization"]["min_compression_size"] 
                and self.optimization_config["optimization"]["enable_compression"]):
                
                compressed_variants = await self._create_compressed_variants(optimized_path)
                result["compressed_variants"] = compressed_variants
            
            # Generate CDN URL
            result["cdn_url"] = self._generate_cdn_url(result["optimized_path"])
            
            # Set cache control headers
            result["cache_control"] = self._get_cache_control(asset_path)
            
            # Calculate savings
            result["size_savings"] = result["original_size"] - result["optimized_size"]
            if result["original_size"] > 0:
                result["compression_ratio"] = result["size_savings"] / result["original_size"]
            
        except Exception as e:
            logger.error(f"Failed to optimize asset {asset_path}: {e}")
            result["error"] = str(e)
        
        return result
    
    async def _generate_content_hash(self, file_path: Path) -> str:
        """Generate content-based hash for cache busting"""
        hash_md5 = hashlib.md5()
        
        async with aiofiles.open(file_path, 'rb') as f:
            while chunk := await f.read(8192):
                hash_md5.update(chunk)
        
        return hash_md5.hexdigest()[:8]  # Use first 8 characters
    
    def _create_optimized_filename(self, original_path: Path, content_hash: str) -> str:
        """Create optimized filename with content hash"""
        if not self.optimization_config["optimization"]["enable_content_hash"]:
            return original_path.name
        
        stem = original_path.stem
        suffix = original_path.suffix
        
        # Insert hash before file extension
        return f"{stem}.{content_hash}{suffix}"
    
    async def _create_compressed_variants(self, file_path: Path) -> List[Dict[str, Any]]:
        """Create gzipped and brotli compressed variants"""
        variants = []
        
        async with aiofiles.open(file_path, 'rb') as f:
            content = await f.read()
        
        # Create gzip variant
        if self.optimization_config["compression"]["gzip"]:
            gzip_path = file_path.with_suffix(file_path.suffix + '.gz')
            compressed_content = gzip.compress(
                content, 
                compresslevel=self.optimization_config["compression"]["quality"]
            )
            
            async with aiofiles.open(gzip_path, 'wb') as f:
                await f.write(compressed_content)
            
            variants.append({
                "type": "gzip",
                "path": str(gzip_path.relative_to(self.static_dir)),
                "size": len(compressed_content),
                "compression_ratio": (len(content) - len(compressed_content)) / len(content)
            })
        
        # Create brotli variant
        if self.optimization_config["compression"]["brotli"]:
            brotli_path = file_path.with_suffix(file_path.suffix + '.br')
            compressed_content = brotli.compress(
                content,
                quality=self.optimization_config["compression"]["quality"]
            )
            
            async with aiofiles.open(brotli_path, 'wb') as f:
                await f.write(compressed_content)
            
            variants.append({
                "type": "brotli", 
                "path": str(brotli_path.relative_to(self.static_dir)),
                "size": len(compressed_content),
                "compression_ratio": (len(content) - len(compressed_content)) / len(content)
            })
        
        return variants
    
    def _generate_cdn_url(self, asset_path: str) -> str:
        """Generate CDN URL for asset"""
        if self.cdn_base_url:
            return f"{self.cdn_base_url.rstrip('/')}/{asset_path.lstrip('/')}"
        else:
            return f"/static/{asset_path.lstrip('/')}"
    
    def _get_cache_control(self, asset_path: Path) -> str:
        """Get appropriate cache control header for asset type"""
        extension = asset_path.suffix.lower()
        
        if extension in ['.css']:
            return self.optimization_config["cache_control"]["css"]
        elif extension in ['.js']:
            return self.optimization_config["cache_control"]["js"]
        elif extension in ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.ico']:
            return self.optimization_config["cache_control"]["images"]
        elif extension in ['.woff', '.woff2', '.ttf', '.eot']:
            return self.optimization_config["cache_control"]["fonts"]
        elif extension in ['.html']:
            return self.optimization_config["cache_control"]["html"]
        else:
            return "public, max-age=86400"  # Default 1 day
    
    async def _generate_asset_manifest(self, processed_files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate asset manifest for frontend consumption"""
        manifest = {
            "version": "2.0.0",
            "generated_at": datetime.now().isoformat(),
            "cdn_base_url": self.cdn_base_url,
            "assets": {},
            "entrypoints": {},
            "stats": {
                "total_files": len(processed_files),
                "total_original_size": 0,
                "total_optimized_size": 0,
                "total_savings": 0
            }
        }
        
        for file_info in processed_files:
            if "error" not in file_info:
                original_path = file_info["file"]
                
                manifest["assets"][original_path] = {
                    "url": file_info["cdn_url"],
                    "size": file_info["optimized_size"],
                    "hash": file_info["content_hash"],
                    "cache_control": file_info["cache_control"],
                    "compressed_variants": file_info["compressed_variants"]
                }
                
                # Update stats
                manifest["stats"]["total_original_size"] += file_info["original_size"]
                manifest["stats"]["total_optimized_size"] += file_info["optimized_size"] 
                manifest["stats"]["total_savings"] += file_info["size_savings"]
        
        # Define entrypoints for critical resources
        manifest["entrypoints"] = {
            "main": {
                "css": [asset for asset in manifest["assets"] if asset.endswith('.css') and 'main' in asset],
                "js": [asset for asset in manifest["assets"] if asset.endswith('.js') and 'main' in asset]
            },
            "vendor": {
                "js": [asset for asset in manifest["assets"] if asset.endswith('.js') and 'vendor' in asset]
            }
        }
        
        return manifest
    
    async def _save_manifest(self, manifest: Dict[str, Any]) -> None:
        """Save asset manifest to file"""
        async with aiofiles.open(self.manifest_file, 'w') as f:
            await f.write(json.dumps(manifest, indent=2))
        
        logger.info(f"Asset manifest saved to {self.manifest_file}")
    
    def get_asset_url(self, asset_path: str) -> str:
        """Get optimized CDN URL for an asset"""
        try:
            if self.manifest_file.exists():
                with open(self.manifest_file, 'r') as f:
                    manifest = json.load(f)
                
                if asset_path in manifest["assets"]:
                    return manifest["assets"][asset_path]["url"]
            
            # Fallback to direct URL
            return self._generate_cdn_url(asset_path)
            
        except Exception as e:
            logger.warning(f"Failed to get asset URL for {asset_path}: {e}")
            return f"/static/{asset_path.lstrip('/')}"
    
    def get_preload_links(self, asset_types: List[str] = None) -> List[str]:
        """Generate preload link headers for critical assets"""
        preload_links = []
        asset_types = asset_types or ['css', 'js']
        
        try:
            if self.manifest_file.exists():
                with open(self.manifest_file, 'r') as f:
                    manifest = json.load(f)
                
                for asset_type in asset_types:
                    if asset_type in manifest["entrypoints"]["main"]:
                        for asset_path in manifest["entrypoints"]["main"][asset_type]:
                            asset_info = manifest["assets"][asset_path]
                            preload_type = "style" if asset_type == "css" else "script"
                            preload_links.append(
                                f"<{asset_info['url']}>; rel=preload; as={preload_type}"
                            )
            
        except Exception as e:
            logger.warning(f"Failed to generate preload links: {e}")
        
        return preload_links

class CDNMiddleware:
    """
    Middleware to handle CDN asset serving and optimization
    """
    
    def __init__(self, app, asset_optimizer: CDNAssetOptimizer):
        self.app = app
        self.optimizer = asset_optimizer
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http" and scope["path"].startswith("/static/"):
            await self._handle_static_request(scope, receive, send)
        else:
            await self.app(scope, receive, send)
    
    async def _handle_static_request(self, scope, receive, send):
        """Handle static asset requests with CDN optimization"""
        path = scope["path"]
        asset_path = path[8:]  # Remove "/static/" prefix
        
        # Check for compressed variant support
        accept_encoding = ""
        for header_name, header_value in scope.get("headers", []):
            if header_name == b"accept-encoding":
                accept_encoding = header_value.decode()
                break
        
        # Try to serve compressed variant
        if "br" in accept_encoding:
            compressed_path = self.optimizer.static_dir / (asset_path + ".br")
            if compressed_path.exists():
                await self._serve_compressed_asset(compressed_path, "br", scope, receive, send)
                return
        
        if "gzip" in accept_encoding:
            compressed_path = self.optimizer.static_dir / (asset_path + ".gz") 
            if compressed_path.exists():
                await self._serve_compressed_asset(compressed_path, "gzip", scope, receive, send)
                return
        
        # Serve original file
        original_path = self.optimizer.static_dir / asset_path
        if original_path.exists():
            await self._serve_original_asset(original_path, scope, receive, send)
        else:
            await self._send_404(scope, receive, send)
    
    async def _serve_compressed_asset(self, file_path: Path, encoding: str, scope, receive, send):
        """Serve compressed asset with appropriate headers"""
        await send({
            "type": "http.response.start",
            "status": 200,
            "headers": [
                [b"content-type", self._get_content_type(file_path).encode()],
                [b"content-encoding", encoding.encode()],
                [b"cache-control", self.optimizer._get_cache_control(file_path).encode()],
                [b"vary", b"Accept-Encoding"],
            ]
        })
        
        async with aiofiles.open(file_path, 'rb') as f:
            content = await f.read()
            await send({
                "type": "http.response.body",
                "body": content
            })
    
    async def _serve_original_asset(self, file_path: Path, scope, receive, send):
        """Serve original asset with caching headers"""
        await send({
            "type": "http.response.start", 
            "status": 200,
            "headers": [
                [b"content-type", self._get_content_type(file_path).encode()],
                [b"cache-control", self.optimizer._get_cache_control(file_path).encode()],
            ]
        })
        
        async with aiofiles.open(file_path, 'rb') as f:
            content = await f.read()
            await send({
                "type": "http.response.body",
                "body": content
            })
    
    async def _send_404(self, scope, receive, send):
        """Send 404 response for missing assets"""
        await send({
            "type": "http.response.start",
            "status": 404,
            "headers": [[b"content-type", b"text/plain"]]
        })
        await send({
            "type": "http.response.body", 
            "body": b"Asset not found"
        })
    
    def _get_content_type(self, file_path: Path) -> str:
        """Get MIME type for file"""
        extension = file_path.suffix.lower().replace('.gz', '').replace('.br', '')
        
        content_types = {
            '.css': 'text/css',
            '.js': 'application/javascript',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.svg': 'image/svg+xml',
            '.webp': 'image/webp',
            '.woff': 'font/woff',
            '.woff2': 'font/woff2',
            '.ttf': 'font/ttf',
            '.json': 'application/json'
        }
        
        return content_types.get(extension, 'application/octet-stream')

# Global CDN optimizer instance
cdn_optimizer = CDNAssetOptimizer()

async def optimize_cdn_assets() -> Dict[str, Any]:
    """Run CDN asset optimization"""
    return await cdn_optimizer.optimize_static_assets()

if __name__ == "__main__":
    # Run optimization when script is executed directly
    async def main():
        results = await optimize_cdn_assets()
        print("CDN Asset Optimization Results:")
        print(f"Status: {results['status']}")
        print(f"Processed Files: {len(results['processed_files'])}")
        print(f"Total Savings: {results['total_savings'] / 1024:.2f} KB")
    
    asyncio.run(main())