"""
FastAPI Analytics Endpoints with MCP Integration
Provides AI-powered analytics and insights for OrdnungsHub
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging

from ..services.mcp_client import get_mcp_client, MCPClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/health")
async def get_mcp_health():
    """Check MCP server connection health"""
    try:
        client = await get_mcp_client()
        health_status = await client.health_check()
        return health_status
    except Exception as e:
        logger.error(f"MCP health check failed: {e}")
        raise HTTPException(status_code=503, detail="MCP service unavailable")

@router.get("/workspace/{workspace_id}/overview")
async def get_workspace_overview(
    workspace_id: str,
    client: MCPClient = Depends(get_mcp_client)
):
    """Get comprehensive workspace analytics"""
    try:
        # Get workspace file statistics
        file_stats = await client.query_database(
            """
            SELECT 
                COUNT(*) as total_files,
                COUNT(DISTINCT category) as unique_categories,
                AVG(ai_confidence) as avg_confidence,
                SUM(CASE WHEN file_size > 1024*1024 THEN 1 ELSE 0 END) as large_files
            FROM file_metadata 
            WHERE workspace_id = ?
            """,
            [workspace_id]
        )
        
        # Get category distribution
        category_dist = await client.query_database(
            """
            SELECT category, COUNT(*) as count
            FROM file_metadata 
            WHERE workspace_id = ?
            GROUP BY category
            ORDER BY count DESC
            """,
            [workspace_id]
        )
        
        # Get recent activity
        recent_activity = await client.query_database(
            """
            SELECT action_type, COUNT(*) as count, MAX(timestamp) as last_action
            FROM user_actions 
            WHERE workspace_id = ? AND timestamp > datetime('now', '-7 days')
            GROUP BY action_type
            ORDER BY count DESC
            """,
            [workspace_id]
        )
        
        return {
            "workspace_id": workspace_id,
            "overview": file_stats[0] if file_stats else {},
            "category_distribution": category_dist,
            "recent_activity": recent_activity,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get workspace overview: {e}")
        raise HTTPException(status_code=500, detail="Analytics generation failed")

@router.get("/ai-insights/{insight_type}")
async def get_ai_insights(
    insight_type: str,
    time_range: str = Query(default="30 days", description="Time range for analysis"),
    workspace_id: Optional[str] = Query(default=None),
    client: MCPClient = Depends(get_mcp_client)
):
    """Get AI-powered insights"""
    try:
        insights = await client.get_ai_insights(insight_type, time_range)
        
        # Add workspace filter if specified
        if workspace_id:
            insights["filtered_for_workspace"] = workspace_id
        
        return insights
        
    except Exception as e:
        logger.error(f"Failed to get AI insights: {e}")
        raise HTTPException(status_code=500, detail="AI insights generation failed")

@router.get("/file-organization")
async def analyze_file_organization(
    workspace_id: Optional[str] = Query(default=None),
    category: Optional[str] = Query(default=None),
    client: MCPClient = Depends(get_mcp_client)
):
    """Analyze file organization patterns"""
    try:
        analysis = await client.analyze_file_data(workspace_id, category)
        return analysis
        
    except Exception as e:
        logger.error(f"File organization analysis failed: {e}")
        raise HTTPException(status_code=500, detail="File analysis failed")

@router.get("/performance-metrics")
async def get_performance_metrics(
    days: int = Query(default=7, description="Number of days to analyze"),
    client: MCPClient = Depends(get_mcp_client)
):
    """Get system performance metrics"""
    try:
        metrics = await client.query_database(
            """
            SELECT 
                DATE(timestamp) as date,
                AVG(memory_usage) as avg_memory,
                AVG(cpu_usage) as avg_cpu,
                AVG(response_time) as avg_response_time,
                COUNT(*) as measurement_count
            FROM performance_metrics 
            WHERE timestamp > datetime('now', '-' || ? || ' days')
            GROUP BY DATE(timestamp)
            ORDER BY date DESC
            """,
            [days]
        )
        
        return {
            "metrics": metrics,
            "period_days": days,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Performance metrics retrieval failed: {e}")
        raise HTTPException(status_code=500, detail="Performance metrics unavailable")

@router.get("/ai-confidence-trends")
async def get_ai_confidence_trends(
    workspace_id: Optional[str] = Query(default=None),
    days: int = Query(default=30),
    client: MCPClient = Depends(get_mcp_client)
):
    """Track AI model confidence trends over time"""
    try:
        query = """
        SELECT 
            DATE(created_at) as date,
            model_type,
            AVG(confidence_score) as avg_confidence,
            COUNT(*) as predictions_count
        FROM ai_analysis 
        WHERE created_at > datetime('now', '-' || ? || ' days')
        """
        
        params = [days]
        if workspace_id:
            query += " AND file_id IN (SELECT id FROM file_metadata WHERE workspace_id = ?)"
            params.append(workspace_id)
            
        query += """
        GROUP BY DATE(created_at), model_type
        ORDER BY date DESC, model_type
        """
        
        trends = await client.query_database(query, params)
        
        return {
            "confidence_trends": trends,
            "workspace_id": workspace_id,
            "period_days": days,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"AI confidence trends analysis failed: {e}")
        raise HTTPException(status_code=500, detail="Confidence trends unavailable")

@router.get("/file-clusters")
async def get_file_clusters(
    workspace_id: Optional[str] = Query(default=None),
    min_cluster_size: int = Query(default=2),
    client: MCPClient = Depends(get_mcp_client)
):
    """Get intelligent file clustering results"""
    try:
        query = """
        SELECT 
            fc.cluster_id,
            fc.cluster_name,
            fc.similarity_threshold,
            COUNT(fm.id) as file_count,
            AVG(fc.confidence_score) as avg_confidence,
            GROUP_CONCAT(DISTINCT fm.category) as categories
        FROM file_clusters fc
        JOIN file_metadata fm ON fc.file_id = fm.id
        """
        
        params = []
        if workspace_id:
            query += " WHERE fm.workspace_id = ?"
            params.append(workspace_id)
            
        query += """
        GROUP BY fc.cluster_id, fc.cluster_name, fc.similarity_threshold
        HAVING COUNT(fm.id) >= ?
        ORDER BY file_count DESC, avg_confidence DESC
        """
        
        params.append(min_cluster_size)
        
        clusters = await client.query_database(query, params)
        
        return {
            "clusters": clusters,
            "workspace_id": workspace_id,
            "min_cluster_size": min_cluster_size,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"File clusters analysis failed: {e}")
        raise HTTPException(status_code=500, detail="Clusters analysis unavailable")

@router.get("/search-analytics")
async def get_search_analytics(
    days: int = Query(default=7),
    client: MCPClient = Depends(get_mcp_client)
):
    """Analyze search patterns and effectiveness"""
    try:
        # Get popular search terms
        popular_searches = await client.query_database(
            """
            SELECT 
                action_details->>'search_term' as search_term,
                COUNT(*) as search_count,
                AVG(CAST(action_details->>'results_count' AS INTEGER)) as avg_results
            FROM user_actions 
            WHERE action_type = 'search' 
                AND timestamp > datetime('now', '-' || ? || ' days')
                AND action_details->>'search_term' IS NOT NULL
            GROUP BY action_details->>'search_term'
            ORDER BY search_count DESC
            LIMIT 20
            """,
            [days]
        )
        
        # Get search success metrics
        search_metrics = await client.query_database(
            """
            SELECT 
                COUNT(*) as total_searches,
                AVG(CAST(action_details->>'results_count' AS INTEGER)) as avg_results_per_search,
                COUNT(CASE WHEN CAST(action_details->>'results_count' AS INTEGER) = 0 THEN 1 END) as zero_result_searches
            FROM user_actions 
            WHERE action_type = 'search' 
                AND timestamp > datetime('now', '-' || ? || ' days')
            """,
            [days]
        )
        
        return {
            "popular_searches": popular_searches,
            "search_metrics": search_metrics[0] if search_metrics else {},
            "period_days": days,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Search analytics failed: {e}")
        raise HTTPException(status_code=500, detail="Search analytics unavailable")

@router.post("/backup")
async def create_analytics_backup(
    backup_name: Optional[str] = None,
    client: MCPClient = Depends(get_mcp_client)
):
    """Create a backup of the analytics database"""
    try:
        if not backup_name:
            backup_name = f"analytics_backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.db"
            
        backup_path = f"./data/backups/{backup_name}"
        success = await client.backup_database(backup_path)
        
        if success:
            return {
                "success": True,
                "backup_path": backup_path,
                "created_at": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail="Backup operation failed")
            
    except Exception as e:
        logger.error(f"Database backup failed: {e}")
        raise HTTPException(status_code=500, detail="Backup creation failed")

@router.get("/dashboard-summary")
async def get_dashboard_summary(
    workspace_id: Optional[str] = Query(default=None),
    client: MCPClient = Depends(get_mcp_client)
):
    """Get comprehensive dashboard summary for frontend"""
    try:
        # Get basic stats
        base_query = """
        SELECT
            COUNT(DISTINCT w.id) as total_workspaces,
            COUNT(DISTINCT fm.id) as total_files,
            COUNT(DISTINCT t.id) as total_tasks,
            AVG(fm.ai_confidence) as avg_ai_confidence
        FROM workspaces w
        LEFT JOIN file_metadata fm ON w.id = fm.workspace_id
        LEFT JOIN tasks t ON w.id = t.workspace_id
        """
        
        params = []
        if workspace_id:
            base_query += " WHERE w.id = ?"
            params.append(workspace_id)
            
        stats = await client.query_database(base_query, params)
        
        # Get recent AI analysis count
        ai_analysis_count = await client.query_database(
            """
            SELECT COUNT(*) as recent_ai_analysis
            FROM ai_analysis 
            WHERE created_at > datetime('now', '-7 days')
            """
        )
        
        # Get top categories
        top_categories = await client.query_database(
            """
            SELECT category, COUNT(*) as count
            FROM file_metadata
            WHERE category IS NOT NULL
            GROUP BY category
            ORDER BY count DESC
            LIMIT 5
            """
        )
        
        return {
            "summary": {
                **stats[0] if stats else {},
                "recent_ai_analysis": ai_analysis_count[0]["recent_ai_analysis"] if ai_analysis_count else 0
            },
            "top_categories": top_categories,
            "workspace_filter": workspace_id,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Dashboard summary generation failed: {e}")
        raise HTTPException(status_code=500, detail="Dashboard summary unavailable")
