"""
Supplier API endpoints for OrdnungsHub
Provides supplier management and price comparison functionality
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from loguru import logger

from src.backend.database.database import get_db
from src.backend.models.user import User
from src.backend.dependencies.auth import get_current_active_user
from src.backend.schemas.supplier import (
    SupplierCreate, SupplierUpdate, SupplierResponse, SupplierDetailResponse,
    SupplierProductCreate, SupplierProductUpdate, SupplierProductResponse,
    PriceListCreate, PriceListUpdate, PriceListResponse,
    SupplierDocumentCreate, SupplierDocumentUpdate, SupplierDocumentResponse,
    SupplierCommunicationCreate, SupplierCommunicationUpdate, SupplierCommunicationResponse,
    SupplierSearchFilters, PriceComparisonRequest, PriceComparisonResponse,
    SupplierStatus
)
from src.backend.crud.crud_supplier import (
    supplier as crud_supplier,
    supplier_product as crud_supplier_product,
    price_list as crud_price_list,
    supplier_document as crud_supplier_document,
    supplier_communication as crud_supplier_communication
)

router = APIRouter(prefix="/suppliers", tags=["suppliers"])

# === Supplier CRUD Operations ===

@router.get("/", response_model=List[SupplierResponse])
async def get_suppliers(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    workspace_id: Optional[int] = Query(None, description="Filter by workspace ID"),
    skip: int = Query(0, ge=0, description="Number of suppliers to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of suppliers to return")
):
    """Get all suppliers for the current user"""
    try:
        suppliers = crud_supplier.get_multi_by_user(
            db=db, 
            user_id=current_user.id, 
            workspace_id=workspace_id,
            skip=skip, 
            limit=limit
        )
        logger.info(f"Retrieved {len(suppliers)} suppliers for user {current_user.id}")
        return suppliers
    except Exception as e:
        logger.error(f"Error retrieving suppliers: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving suppliers")

@router.post("/", response_model=SupplierResponse)
async def create_supplier(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    supplier_in: SupplierCreate
):
    """Create a new supplier"""
    try:
        # Check if supplier already exists in workspace
        existing_supplier = crud_supplier.get_by_name_and_workspace(
            db=db, 
            name=supplier_in.name, 
            workspace_id=supplier_in.workspace_id
        )
        if existing_supplier:
            raise HTTPException(
                status_code=400, 
                detail=f"Supplier '{supplier_in.name}' already exists in this workspace"
            )
        
        supplier = crud_supplier.create(db=db, obj_in=supplier_in)
        logger.info(f"Created supplier {supplier.id} ({supplier.name}) for user {current_user.id}")
        return supplier
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating supplier: {str(e)}")
        raise HTTPException(status_code=500, detail="Error creating supplier")

@router.get("/{supplier_id}", response_model=SupplierDetailResponse)
async def get_supplier(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    supplier_id: int
):
    """Get a specific supplier with detailed information"""
    try:
        supplier = crud_supplier.get_with_details(db=db, supplier_id=supplier_id)
        if not supplier:
            raise HTTPException(status_code=404, detail="Supplier not found")
        
        # Verify user ownership
        if supplier.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to access this supplier")
        
        # Get additional counts and recent data
        recent_communications = crud_supplier_communication.get_recent_by_supplier(
            db=db, supplier_id=supplier_id, limit=5
        )
        
        documents_count = len(supplier.documents)
        price_lists_count = len(supplier.price_lists)
        
        # Build detailed response
        response_data = SupplierDetailResponse(
            **supplier.__dict__,
            products=supplier.products,
            recent_communications=recent_communications,
            documents_count=documents_count,
            price_lists_count=price_lists_count
        )
        
        logger.info(f"Retrieved supplier {supplier_id} details for user {current_user.id}")
        return response_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving supplier {supplier_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving supplier")

@router.put("/{supplier_id}", response_model=SupplierResponse)
async def update_supplier(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    supplier_id: int,
    supplier_in: SupplierUpdate
):
    """Update a supplier"""
    try:
        supplier = crud_supplier.get(db=db, id=supplier_id)
        if not supplier:
            raise HTTPException(status_code=404, detail="Supplier not found")
        
        # Verify user ownership
        if supplier.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to update this supplier")
        
        supplier = crud_supplier.update(db=db, db_obj=supplier, obj_in=supplier_in)
        logger.info(f"Updated supplier {supplier_id} for user {current_user.id}")
        return supplier
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating supplier {supplier_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error updating supplier")

@router.delete("/{supplier_id}")
async def delete_supplier(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    supplier_id: int
):
    """Delete a supplier"""
    try:
        supplier = crud_supplier.get(db=db, id=supplier_id)
        if not supplier:
            raise HTTPException(status_code=404, detail="Supplier not found")
        
        # Verify user ownership
        if supplier.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this supplier")
        
        crud_supplier.remove(db=db, id=supplier_id)
        logger.info(f"Deleted supplier {supplier_id} for user {current_user.id}")
        return {"message": "Supplier deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting supplier {supplier_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error deleting supplier")

# === Search and Filter ===

@router.post("/search", response_model=List[SupplierResponse])
async def search_suppliers(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    filters: SupplierSearchFilters,
    workspace_id: Optional[int] = Query(None, description="Filter by workspace ID"),
    skip: int = Query(0, ge=0, description="Number of suppliers to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of suppliers to return")
):
    """Search suppliers with advanced filters"""
    try:
        suppliers = crud_supplier.search_suppliers(
            db=db,
            user_id=current_user.id,
            workspace_id=workspace_id,
            filters=filters,
            skip=skip,
            limit=limit
        )
        logger.info(f"Search returned {len(suppliers)} suppliers for user {current_user.id}")
        return suppliers
    except Exception as e:
        logger.error(f"Error searching suppliers: {str(e)}")
        raise HTTPException(status_code=500, detail="Error searching suppliers")

# === Product Management ===

@router.get("/{supplier_id}/products", response_model=List[SupplierProductResponse])
async def get_supplier_products(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    supplier_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """Get all products for a supplier"""
    try:
        # Verify supplier ownership
        supplier = crud_supplier.get(db=db, id=supplier_id)
        if not supplier or supplier.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Supplier not found")
        
        products = crud_supplier_product.get_by_supplier(
            db=db, supplier_id=supplier_id, skip=skip, limit=limit
        )
        return products
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving products for supplier {supplier_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving products")

@router.post("/{supplier_id}/products", response_model=SupplierProductResponse)
async def create_supplier_product(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    supplier_id: int,
    product_in: SupplierProductCreate
):
    """Create a new product for a supplier"""
    try:
        # Verify supplier ownership
        supplier = crud_supplier.get(db=db, id=supplier_id)
        if not supplier or supplier.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Supplier not found")
        
        # Ensure supplier_id matches
        product_in.supplier_id = supplier_id
        
        product = crud_supplier_product.create(db=db, obj_in=product_in)
        logger.info(f"Created product {product.id} for supplier {supplier_id}")
        return product
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating product for supplier {supplier_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error creating product")

# === Price Management ===

@router.get("/{supplier_id}/products/{product_id}/prices", response_model=List[PriceListResponse])
async def get_product_prices(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    supplier_id: int,
    product_id: int,
    active_only: bool = Query(True, description="Only return active prices")
):
    """Get all prices for a specific product"""
    try:
        # Verify ownership
        supplier = crud_supplier.get(db=db, id=supplier_id)
        if not supplier or supplier.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Supplier not found")
        
        prices = crud_price_list.get_by_product(
            db=db, product_id=product_id, active_only=active_only
        )
        return prices
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving prices for product {product_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving prices")

@router.post("/{supplier_id}/products/{product_id}/prices", response_model=PriceListResponse)
async def create_price_list(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    supplier_id: int,
    product_id: int,
    price_in: PriceListCreate
):
    """Create a new price entry for a product"""
    try:
        # Verify ownership
        supplier = crud_supplier.get(db=db, id=supplier_id)
        if not supplier or supplier.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Supplier not found")
        
        # Ensure IDs match
        price_in.supplier_id = supplier_id
        price_in.product_id = product_id
        
        price = crud_price_list.create(db=db, obj_in=price_in)
        logger.info(f"Created price entry {price.id} for product {product_id}")
        return price
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating price for product {product_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error creating price")

# === Price Comparison ===

@router.post("/compare-prices", response_model=PriceComparisonResponse)
async def compare_prices(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    comparison_request: PriceComparisonRequest
):
    """Compare prices for a product across multiple suppliers"""
    try:
        price_data = crud_price_list.compare_prices(
            db=db,
            product_name=comparison_request.product_name,
            supplier_ids=comparison_request.supplier_ids,
            quantity=comparison_request.quantity
        )
        
        if not price_data:
            return PriceComparisonResponse(
                product_name=comparison_request.product_name,
                total_suppliers=0,
                price_entries=[]
            )
        
        prices = [entry["price"] for entry in price_data]
        
        response = PriceComparisonResponse(
            product_name=comparison_request.product_name,
            total_suppliers=len(price_data),
            best_price=min(prices) if prices else None,
            average_price=sum(prices) / len(prices) if prices else None,
            price_entries=price_data
        )
        
        logger.info(f"Price comparison for '{comparison_request.product_name}' returned {len(price_data)} results")
        return response
    except Exception as e:
        logger.error(f"Error comparing prices: {str(e)}")
        raise HTTPException(status_code=500, detail="Error comparing prices")

# === Communications ===

@router.get("/{supplier_id}/communications", response_model=List[SupplierCommunicationResponse])
async def get_supplier_communications(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    supplier_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """Get communications for a supplier"""
    try:
        # Verify ownership
        supplier = crud_supplier.get(db=db, id=supplier_id)
        if not supplier or supplier.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Supplier not found")
        
        communications = crud_supplier_communication.get_by_supplier(
            db=db, supplier_id=supplier_id, skip=skip, limit=limit
        )
        return communications
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving communications for supplier {supplier_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving communications")

@router.post("/{supplier_id}/communications", response_model=SupplierCommunicationResponse)
async def create_supplier_communication(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    supplier_id: int,
    communication_in: SupplierCommunicationCreate
):
    """Create a new communication record for a supplier"""
    try:
        # Verify ownership
        supplier = crud_supplier.get(db=db, id=supplier_id)
        if not supplier or supplier.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Supplier not found")
        
        # Set IDs
        communication_in.supplier_id = supplier_id
        communication_in.user_id = current_user.id
        
        communication = crud_supplier_communication.create(db=db, obj_in=communication_in)
        logger.info(f"Created communication {communication.id} for supplier {supplier_id}")
        return communication
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating communication for supplier {supplier_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error creating communication")

# === Documents ===

@router.get("/{supplier_id}/documents", response_model=List[SupplierDocumentResponse])
async def get_supplier_documents(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    supplier_id: int,
    document_type: Optional[str] = Query(None, description="Filter by document type"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """Get documents for a supplier"""
    try:
        # Verify ownership
        supplier = crud_supplier.get(db=db, id=supplier_id)
        if not supplier or supplier.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Supplier not found")
        
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
        logger.error(f"Error retrieving documents for supplier {supplier_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving documents")

@router.post("/{supplier_id}/documents", response_model=SupplierDocumentResponse)
async def create_supplier_document(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    supplier_id: int,
    document_in: SupplierDocumentCreate
):
    """Create a new document record for a supplier"""
    try:
        # Verify ownership
        supplier = crud_supplier.get(db=db, id=supplier_id)
        if not supplier or supplier.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Supplier not found")
        
        # Set supplier_id
        document_in.supplier_id = supplier_id
        
        document = crud_supplier_document.create(db=db, obj_in=document_in)
        logger.info(f"Created document {document.id} for supplier {supplier_id}")
        return document
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating document for supplier {supplier_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error creating document")