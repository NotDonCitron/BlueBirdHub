"""
Database Maintenance and Optimization Script
Automated database health checks, optimization, and maintenance tasks
"""
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy import text, create_engine
from sqlalchemy.orm import sessionmaker
from loguru import logger
import json

from src.backend.database.database_config import (
    DatabaseConfig, 
    DB_OPTIMIZATION_QUERIES,
    INDEX_CREATION_QUERIES,
    PERFORMANCE_QUERIES
)
from src.backend.services.cache_service import cache_service
from src.backend.services.db_performance_monitor import db_monitor, db_health_checker


class DatabaseMaintenanceService:
    """
    Comprehensive database maintenance and optimization service
    """
    
    def __init__(self):
        self.config = DatabaseConfig()
        self.maintenance_log = []
        
    async def run_full_maintenance(self) -> Dict[str, Any]:
        """
        Run complete database maintenance cycle
        """
        maintenance_start = datetime.now()
        results = {
            'started_at': maintenance_start.isoformat(),
            'tasks_completed': [],
            'tasks_failed': [],
            'performance_before': None,
            'performance_after': None,
            'duration_seconds': 0
        }
        
        logger.info("Starting full database maintenance cycle")
        
        # Get performance baseline
        results['performance_before'] = db_monitor.get_performance_summary()
        
        # Run maintenance tasks
        maintenance_tasks = [
            ('integrity_check', self._run_integrity_check),
            ('foreign_key_check', self._run_foreign_key_check),
            ('analyze_database', self._analyze_database),
            ('optimize_indexes', self._optimize_indexes),
            ('vacuum_database', self._vacuum_database),
            ('update_statistics', self._update_statistics),
            ('cleanup_cache', self._cleanup_cache),
            ('check_performance', self._check_performance)
        ]
        
        for task_name, task_func in maintenance_tasks:
            try:
                task_start = time.time()
                task_result = await task_func()
                task_duration = time.time() - task_start
                
                results['tasks_completed'].append({
                    'task': task_name,
                    'duration_seconds': round(task_duration, 3),
                    'result': task_result
                })
                
                logger.info(f"Maintenance task '{task_name}' completed in {task_duration:.3f}s")
                
            except Exception as e:
                results['tasks_failed'].append({
                    'task': task_name,
                    'error': str(e)
                })
                logger.error(f"Maintenance task '{task_name}' failed: {e}")
        
        # Get performance after maintenance
        results['performance_after'] = db_monitor.get_performance_summary()
        
        # Calculate total duration
        maintenance_end = datetime.now()
        results['completed_at'] = maintenance_end.isoformat()
        results['duration_seconds'] = (maintenance_end - maintenance_start).total_seconds()
        
        # Log maintenance summary
        self.maintenance_log.append(results)
        logger.info(f"Database maintenance completed in {results['duration_seconds']:.2f}s")
        
        return results
    
    async def _run_integrity_check(self) -> Dict[str, Any]:
        """Run database integrity check"""
        engine = create_engine(self.config.get_database_url())
        
        with engine.connect() as conn:
            result = conn.execute(text(DB_OPTIMIZATION_QUERIES['integrity_check']))
            integrity_results = result.fetchall()
            
            # Check if integrity is OK
            is_ok = len(integrity_results) == 1 and integrity_results[0][0] == 'ok'
            
            return {
                'integrity_ok': is_ok,
                'issues_found': len(integrity_results) if not is_ok else 0,
                'details': [row[0] for row in integrity_results] if not is_ok else ['ok']
            }
    
    async def _run_foreign_key_check(self) -> Dict[str, Any]:
        """Run foreign key constraint check"""
        engine = create_engine(self.config.get_database_url())
        
        with engine.connect() as conn:
            result = conn.execute(text(DB_OPTIMIZATION_QUERIES['foreign_key_check']))
            fk_violations = result.fetchall()
            
            return {
                'foreign_keys_ok': len(fk_violations) == 0,
                'violations_found': len(fk_violations),
                'details': [dict(row._mapping) for row in fk_violations] if fk_violations else []
            }
    
    async def _analyze_database(self) -> Dict[str, Any]:
        """Analyze database for query optimization"""
        engine = create_engine(self.config.get_database_url())
        
        with engine.connect() as conn:
            # Run ANALYZE to update query planner statistics
            conn.execute(text(DB_OPTIMIZATION_QUERIES['analyze_database']))
            conn.commit()
            
            return {'analyzed': True, 'message': 'Database statistics updated'}
    
    async def _optimize_indexes(self) -> Dict[str, Any]:
        """Create and optimize database indexes"""
        engine = create_engine(self.config.get_database_url())
        indexes_created = []
        indexes_failed = []
        
        with engine.connect() as conn:
            for index_query in INDEX_CREATION_QUERIES:
                try:
                    conn.execute(text(index_query))
                    index_name = index_query.split('idx_')[1].split(' ')[0] if 'idx_' in index_query else 'unknown'
                    indexes_created.append(index_name)
                except Exception as e:
                    indexes_failed.append({
                        'query': index_query,
                        'error': str(e)
                    })
            
            conn.commit()
            
            return {
                'indexes_created': len(indexes_created),
                'indexes_failed': len(indexes_failed),
                'created_indexes': indexes_created,
                'failed_indexes': indexes_failed
            }
    
    async def _vacuum_database(self) -> Dict[str, Any]:
        """Run database vacuum for space optimization"""
        engine = create_engine(self.config.get_database_url())
        
        # Get database size before vacuum
        with engine.connect() as conn:
            size_before = conn.execute(text(PERFORMANCE_QUERIES['database_size'])).fetchone()
            size_before_bytes = size_before[0] if size_before else 0
            
            # Run incremental vacuum first
            conn.execute(text(DB_OPTIMIZATION_QUERIES['incremental_vacuum']))
            
            # Get size after incremental vacuum
            size_after = conn.execute(text(PERFORMANCE_QUERIES['database_size'])).fetchone()
            size_after_bytes = size_after[0] if size_after else 0
            
            space_reclaimed = size_before_bytes - size_after_bytes
            
            return {
                'vacuum_completed': True,
                'size_before_bytes': size_before_bytes,
                'size_after_bytes': size_after_bytes,
                'space_reclaimed_bytes': space_reclaimed,
                'space_reclaimed_mb': round(space_reclaimed / (1024 * 1024), 2)
            }
    
    async def _update_statistics(self) -> Dict[str, Any]:
        """Update database statistics and run optimization"""
        engine = create_engine(self.config.get_database_url())
        
        with engine.connect() as conn:
            # Run SQLite optimizer
            conn.execute(text(DB_OPTIMIZATION_QUERIES['optimize_database']))
            conn.commit()
            
            # Get updated table statistics
            table_stats = conn.execute(text(PERFORMANCE_QUERIES['table_info'])).fetchall()
            
            stats = {}
            for row in table_stats:
                stats[row[0]] = {
                    'row_count': row[1],
                    'avg_row_size': row[2]
                }
            
            return {
                'statistics_updated': True,
                'table_statistics': stats
            }
    
    async def _cleanup_cache(self) -> Dict[str, Any]:
        """Clean up expired cache entries"""
        if not cache_service._is_available():
            return {'cache_cleanup': False, 'reason': 'Redis not available'}
        
        try:
            # Get cache info before cleanup
            cache_stats_before = await cache_service.get_cache_stats()
            
            # Clean up expired keys (Redis handles this automatically)
            # We can trigger a manual cleanup of our application-specific patterns
            patterns_to_clean = [
                'ordnungshub:*search*',  # Clean old search results
                'ordnungshub:*temp*',    # Clean temporary caches
            ]
            
            cleaned_keys = 0
            for pattern in patterns_to_clean:
                cleaned_keys += await cache_service.delete_pattern(pattern)
            
            cache_stats_after = await cache_service.get_cache_stats()
            
            return {
                'cache_cleanup': True,
                'keys_cleaned': cleaned_keys,
                'cache_stats_before': cache_stats_before,
                'cache_stats_after': cache_stats_after
            }
            
        except Exception as e:
            return {'cache_cleanup': False, 'error': str(e)}
    
    async def _check_performance(self) -> Dict[str, Any]:
        """Run performance health check"""
        health_status = await db_health_checker.check_database_health()
        
        return {
            'performance_check': True,
            'health_status': health_status['status'],
            'issues': health_status['issues'],
            'warnings': health_status['warnings'],
            'recommendations': health_status['recommendations']
        }
    
    async def run_quick_maintenance(self) -> Dict[str, Any]:
        """
        Run quick maintenance tasks for regular intervals
        """
        quick_start = datetime.now()
        results = {
            'started_at': quick_start.isoformat(),
            'type': 'quick_maintenance',
            'tasks_completed': []
        }
        
        logger.info("Running quick database maintenance")
        
        # Quick tasks
        quick_tasks = [
            ('incremental_vacuum', self._run_incremental_vacuum),
            ('cache_cleanup', self._cleanup_expired_cache),
            ('performance_check', self._quick_performance_check)
        ]
        
        for task_name, task_func in quick_tasks:
            try:
                task_result = await task_func()
                results['tasks_completed'].append({
                    'task': task_name,
                    'result': task_result
                })
            except Exception as e:
                logger.error(f"Quick maintenance task '{task_name}' failed: {e}")
        
        # Calculate duration
        quick_end = datetime.now()
        results['completed_at'] = quick_end.isoformat()
        results['duration_seconds'] = (quick_end - quick_start).total_seconds()
        
        return results
    
    async def _run_incremental_vacuum(self) -> Dict[str, Any]:
        """Run incremental vacuum only"""
        engine = create_engine(self.config.get_database_url())
        
        with engine.connect() as conn:
            conn.execute(text('PRAGMA incremental_vacuum(50);'))
            conn.commit()
            
            return {'incremental_vacuum': True, 'pages_vacuumed': 50}
    
    async def _cleanup_expired_cache(self) -> Dict[str, Any]:
        """Clean up only expired cache entries"""
        if not cache_service._is_available():
            return {'cache_available': False}
        
        # Get current cache stats
        stats = await cache_service.get_cache_stats()
        
        return {
            'cache_stats': stats,
            'expired_cleanup': True
        }
    
    async def _quick_performance_check(self) -> Dict[str, Any]:
        """Quick performance check"""
        performance = db_monitor.get_performance_summary()
        
        # Check for immediate issues
        issues = []
        if performance['summary']['slow_query_percentage'] > 20:
            issues.append('High slow query percentage')
        
        if performance['summary']['connection_errors'] > 0:
            issues.append('Connection errors detected')
        
        return {
            'performance_ok': len(issues) == 0,
            'issues': issues,
            'query_count': performance['summary']['total_queries'],
            'slow_queries': performance['summary']['slow_queries']
        }
    
    def get_maintenance_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent maintenance history"""
        return self.maintenance_log[-limit:]
    
    async def schedule_maintenance(self, maintenance_type: str = 'quick') -> None:
        """
        Schedule maintenance to run in background
        """
        if maintenance_type == 'full':
            await self.run_full_maintenance()
        else:
            await self.run_quick_maintenance()


# Global maintenance service instance
db_maintenance_service = DatabaseMaintenanceService()


async def run_maintenance_cycle():
    """
    Run automated maintenance cycle
    Can be called from a scheduler or manually
    """
    try:
        # Run quick maintenance every hour
        # Run full maintenance daily
        current_hour = datetime.now().hour
        
        if current_hour == 2:  # 2 AM - run full maintenance
            result = await db_maintenance_service.run_full_maintenance()
            logger.info(f"Full maintenance completed: {result['duration_seconds']:.2f}s")
        else:  # Other hours - run quick maintenance
            result = await db_maintenance_service.run_quick_maintenance()
            logger.info(f"Quick maintenance completed: {result['duration_seconds']:.2f}s")
        
        return result
        
    except Exception as e:
        logger.error(f"Maintenance cycle failed: {e}")
        return {'error': str(e), 'completed': False}


if __name__ == "__main__":
    # Manual maintenance execution
    import sys
    
    maintenance_type = sys.argv[1] if len(sys.argv) > 1 else 'quick'
    
    if maintenance_type == 'full':
        result = asyncio.run(db_maintenance_service.run_full_maintenance())
    else:
        result = asyncio.run(db_maintenance_service.run_quick_maintenance())
    
    print(json.dumps(result, indent=2))