from sqlalchemy.orm import Session
from sqlalchemy import desc, func, and_
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from models.error_log import ErrorLog
from schemas.error_log import ErrorLogCreate, ErrorLogFilter
from crud.base import CRUDBase

class CRUDErrorLog(CRUDBase[ErrorLog, ErrorLogCreate, ErrorLogCreate]):
    
    def create_error_log(self, db: Session, *, error_data: ErrorLogCreate) -> ErrorLog:
        """Create a new error log entry"""
        db_obj = ErrorLog(
            message=error_data.message,
            stack=error_data.stack,
            source=error_data.source,
            timestamp=datetime.fromisoformat(error_data.timestamp.replace('Z', '+00:00')),
            user_agent=error_data.user_agent,
            url=error_data.url,
            error_type=error_data.error_type,
            severity=error_data.severity,
            additional_data=error_data.additional_data
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def get_errors_filtered(
        self, 
        db: Session, 
        filters: ErrorLogFilter
    ) -> List[ErrorLog]:
        """Get errors with filtering"""
        query = db.query(ErrorLog)
        
        if filters.source:
            query = query.filter(ErrorLog.source == filters.source)
        if filters.severity:
            query = query.filter(ErrorLog.severity == filters.severity)
        if filters.resolved is not None:
            query = query.filter(ErrorLog.resolved == filters.resolved)
        if filters.start_date:
            query = query.filter(ErrorLog.timestamp >= filters.start_date)
        if filters.end_date:
            query = query.filter(ErrorLog.timestamp <= filters.end_date)
            
        return query.order_by(desc(ErrorLog.timestamp))\
                   .offset(filters.offset)\
                   .limit(filters.limit)\
                   .all()
    
    def get_error_stats(self, db: Session) -> Dict[str, Any]:
        """Get error statistics"""
        total_errors = db.query(ErrorLog).count()
        unresolved_errors = db.query(ErrorLog).filter(ErrorLog.resolved == 0).count()
        
        # Recent errors (last 24 hours)
        recent_cutoff = datetime.utcnow() - timedelta(hours=24)
        recent_errors = db.query(ErrorLog).filter(ErrorLog.timestamp >= recent_cutoff).count()
        
        # Errors by severity
        severity_stats = db.query(
            ErrorLog.severity, 
            func.count(ErrorLog.id)
        ).group_by(ErrorLog.severity).all()
        
        # Errors by source
        source_stats = db.query(
            ErrorLog.source, 
            func.count(ErrorLog.id)
        ).group_by(ErrorLog.source).all()
        
        return {
            "total_errors": total_errors,
            "unresolved_errors": unresolved_errors,
            "recent_errors_count": recent_errors,
            "errors_by_severity": dict(severity_stats),
            "errors_by_source": dict(source_stats)
        }
    
    def get_recent_errors(self, db: Session, limit: int = 10) -> List[ErrorLog]:
        """Get most recent errors"""
        return db.query(ErrorLog)\
                .order_by(desc(ErrorLog.timestamp))\
                .limit(limit)\
                .all()
    
    def find_common_patterns(self, db: Session, limit: int = 5) -> List[Dict[str, Any]]:
        """Find common error patterns"""
        # Group by message and count occurrences
        patterns = db.query(
            ErrorLog.message,
            ErrorLog.source,
            func.count(ErrorLog.id).label('count'),
            func.max(ErrorLog.timestamp).label('last_seen')
        ).group_by(ErrorLog.message, ErrorLog.source)\
         .having(func.count(ErrorLog.id) > 1)\
         .order_by(desc(func.count(ErrorLog.id)))\
         .limit(limit)\
         .all()
        
        return [
            {
                "message": p.message,
                "source": p.source,
                "count": p.count,
                "last_seen": p.last_seen.isoformat() if p.last_seen else None
            }
            for p in patterns
        ]
    
    def mark_resolved(self, db: Session, error_id: int) -> Optional[ErrorLog]:
        """Mark an error as resolved"""
        error = db.query(ErrorLog).filter(ErrorLog.id == error_id).first()
        if error:
            error.resolved = 1
            db.commit()
            db.refresh(error)
        return error
    
    def delete_old_errors(self, db: Session, days: int = 30) -> int:
        """Delete errors older than specified days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        deleted_count = db.query(ErrorLog)\
                         .filter(ErrorLog.timestamp < cutoff_date)\
                         .delete()
        db.commit()
        return deleted_count

error_log = CRUDErrorLog(ErrorLog)