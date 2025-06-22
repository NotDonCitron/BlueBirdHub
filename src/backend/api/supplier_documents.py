"""
Supplier Document Analysis API endpoints
Handles document upload, processing, and AI analysis for suppliers
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from loguru import logger
import os
import shutil
from pathlib import Path
from datetime import datetime
import json

from src.backend.database.database import get_db
from src.backend.models.user import User
from src.backend.dependencies.auth import get_current_active_user
from src.backend.models.supplier import SupplierDocument, DocumentType, VerificationStatus
from src.backend.models.file_metadata import FileMetadata
from src.backend.schemas.supplier import (
    SupplierDocumentCreate, SupplierDocumentResponse, SupplierDocumentUpdate
)
from src.backend.crud.crud_supplier import supplier as crud_supplier
from src.backend.crud.crud_supplier import supplier_document as crud_supplier_document
from src.backend.services.pdf_processor import pdf_processor
from src.backend.services.supplier_ai_service import supplier_ai_service

router = APIRouter(prefix="/suppliers/{supplier_id}/documents", tags=["supplier-documents"])

# Configure upload directory
UPLOAD_DIR = Path("data/uploads/supplier_documents")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@router.post("/upload", response_model=Dict[str, Any])
async def upload_supplier_document(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    supplier_id: int,
    file: UploadFile = File(...),
    document_type: str = Form("price_list"),
    notes: Optional[str] = Form(None)
):
    """
    Upload and analyze a supplier document
    
    Supports PDF, TXT, PNG, JPG formats
    Automatically extracts prices and product information
    """
    try:
        # Verify supplier ownership
        supplier = crud_supplier.get(db=db, id=supplier_id)
        if not supplier or supplier.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Supplier not found")
        
        # Validate file type
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in ['.pdf', '.txt', '.png', '.jpg', '.jpeg']:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type: {file_ext}. Supported: PDF, TXT, PNG, JPG"
            )
        
        # Save uploaded file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_filename = f"supplier_{supplier_id}_{timestamp}_{file.filename}"
        file_path = UPLOAD_DIR / safe_filename
        
        with open(file_path, 'wb') as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Create file metadata entry
        file_metadata = FileMetadata(
            filename=safe_filename,
            original_filename=file.filename,
            file_path=str(file_path),
            file_size=file_path.stat().st_size,
            mime_type=file.content_type,
            upload_date=datetime.now(),
            user_id=current_user.id,
            workspace_id=supplier.workspace_id,
            category='supplier_document'
        )
        db.add(file_metadata)
        db.flush()  # Get the ID without committing
        
        # Process document
        logger.info(f"Processing document: {file.filename}")
        extraction_result = pdf_processor.process_document(str(file_path))
        
        # Analyze with AI
        analysis_result = {}
        if extraction_result.get('text_content'):
            analysis_result = supplier_ai_service.analyze_document(
                extraction_result['text_content'],
                document_type
            )
        
        # Create supplier document record
        supplier_doc = SupplierDocument(
            supplier_id=supplier_id,
            file_metadata_id=file_metadata.id,
            document_type=DocumentType(document_type),
            extracted_data=json.dumps({
                'extraction': extraction_result,
                'analysis': analysis_result
            }),
            verification_status=VerificationStatus.PENDING,
            notes=notes
        )
        db.add(supplier_doc)
        db.commit()
        
        # Prepare response
        response = {
            'document_id': supplier_doc.id,
            'file_name': file.filename,
            'file_size': file_metadata.file_size,
            'document_type': document_type,
            'processing_status': 'completed',
            'extraction_summary': {
                'page_count': extraction_result.get('page_count', 0),
                'text_length': len(extraction_result.get('text_content', '')),
                'processing_time_ms': extraction_result.get('processing_time_ms', 0),
                'extraction_method': extraction_result.get('extraction_method', 'unknown')
            },
            'analysis_summary': {
                'quality_score': analysis_result.get('quality_score', 0),
                'products_found': len(analysis_result.get('products', [])),
                'prices_found': len(analysis_result.get('prices', [])),
                'categories': analysis_result.get('categories', [])
            },
            'verification_status': supplier_doc.verification_status.value,
            'created_at': supplier_doc.created_at.isoformat()
        }
        
        logger.info(f"Document uploaded and analyzed: {file.filename} (ID: {supplier_doc.id})")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        # Clean up file if database operation failed
        if 'file_path' in locals() and file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=f"Document upload failed: {str(e)}")

@router.get("/{document_id}/analysis", response_model=Dict[str, Any])
async def get_document_analysis(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    supplier_id: int,
    document_id: int
):
    """Get detailed analysis results for a document"""
    try:
        # Verify ownership
        supplier = crud_supplier.get(db=db, id=supplier_id)
        if not supplier or supplier.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Supplier not found")
        
        # Get document
        document = crud_supplier_document.get(db=db, id=document_id)
        if not document or document.supplier_id != supplier_id:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Parse extracted data
        extracted_data = json.loads(document.extracted_data) if document.extracted_data else {}
        analysis = extracted_data.get('analysis', {})
        
        # Format response
        response = {
            'document_id': document.id,
            'document_type': document.document_type.value,
            'verification_status': document.verification_status.value,
            'quality_score': analysis.get('quality_score', 0),
            'supplier_info': analysis.get('supplier_info', {}),
            'products': analysis.get('products', []),
            'prices': analysis.get('prices', []),
            'terms': analysis.get('terms', {}),
            'categories': analysis.get('categories', []),
            'validation_errors': analysis.get('validation_errors', []),
            'extracted_at': analysis.get('extracted_at'),
            'notes': document.notes
        }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving analysis: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve analysis")

@router.post("/{document_id}/verify", response_model=Dict[str, Any])
async def verify_document_analysis(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    supplier_id: int,
    document_id: int,
    verification_status: str = Form(...),
    notes: Optional[str] = Form(None)
):
    """Verify or reject document analysis results"""
    try:
        # Verify ownership
        supplier = crud_supplier.get(db=db, id=supplier_id)
        if not supplier or supplier.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Supplier not found")
        
        # Get document
        document = crud_supplier_document.get(db=db, id=document_id)
        if not document or document.supplier_id != supplier_id:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Update verification status
        document.verification_status = VerificationStatus(verification_status)
        document.verified_by_user_id = current_user.id
        document.verified_at = datetime.now()
        if notes:
            document.notes = notes
        
        db.commit()
        
        return {
            'document_id': document.id,
            'verification_status': document.verification_status.value,
            'verified_by': current_user.username,
            'verified_at': document.verified_at.isoformat(),
            'notes': document.notes
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying document: {e}")
        raise HTTPException(status_code=500, detail="Verification failed")

@router.post("/{document_id}/apply-to-products", response_model=Dict[str, Any])
async def apply_document_to_products(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    supplier_id: int,
    document_id: int
):
    """Apply extracted product and price data to supplier catalog"""
    try:
        # Verify ownership
        supplier = crud_supplier.get(db=db, id=supplier_id)
        if not supplier or supplier.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Supplier not found")
        
        # Get document
        document = crud_supplier_document.get(db=db, id=document_id)
        if not document or document.supplier_id != supplier_id:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Check if verified
        if document.verification_status != VerificationStatus.VERIFIED:
            raise HTTPException(
                status_code=400, 
                detail="Document must be verified before applying to products"
            )
        
        # Parse analysis
        extracted_data = json.loads(document.extracted_data) if document.extracted_data else {}
        analysis = extracted_data.get('analysis', {})
        
        # Create price list entries
        price_entries = supplier_ai_service.create_price_list_from_analysis(
            analysis, 
            supplier_id
        )
        
        # TODO: Implement actual database insertion of products and prices
        # This would create/update supplier_products and price_lists records
        
        created_count = len(price_entries)
        
        logger.info(f"Applied {created_count} price entries from document {document_id}")
        
        return {
            'document_id': document_id,
            'products_created': created_count,
            'price_entries': price_entries[:10],  # Return first 10 as preview
            'message': f"Successfully extracted {created_count} product prices"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error applying document data: {e}")
        raise HTTPException(status_code=500, detail="Failed to apply document data")

@router.get("/", response_model=List[SupplierDocumentResponse])
async def get_supplier_documents(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    supplier_id: int,
    document_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 20
):
    """Get all documents for a supplier"""
    try:
        # Verify ownership
        supplier = crud_supplier.get(db=db, id=supplier_id)
        if not supplier or supplier.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Supplier not found")
        
        # Get documents
        documents = crud_supplier_document.get_by_supplier(
            db=db,
            supplier_id=supplier_id,
            document_type=document_type,
            skip=skip,
            limit=limit
        )
        
        return documents
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving documents: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve documents")

@router.delete("/{document_id}")
async def delete_supplier_document(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    supplier_id: int,
    document_id: int
):
    """Delete a supplier document"""
    try:
        # Verify ownership
        supplier = crud_supplier.get(db=db, id=supplier_id)
        if not supplier or supplier.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Supplier not found")
        
        # Get document
        document = crud_supplier_document.get(db=db, id=document_id)
        if not document or document.supplier_id != supplier_id:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Delete file from disk
        if document.file_metadata and document.file_metadata.file_path:
            file_path = Path(document.file_metadata.file_path)
            if file_path.exists():
                file_path.unlink()
        
        # Delete database records
        crud_supplier_document.remove(db=db, id=document_id)
        
        logger.info(f"Deleted document {document_id} for supplier {supplier_id}")
        
        return {"message": "Document deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete document")