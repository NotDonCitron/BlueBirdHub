from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_, func

from src.backend.crud.base import CRUDBase
from src.backend.models.supplier import (
    Supplier, SupplierProduct, PriceList, 
    SupplierDocument, SupplierCommunication
)
from src.backend.schemas.supplier import (
    SupplierCreate, SupplierUpdate, SupplierStatus,
    SupplierProductCreate, SupplierProductUpdate,
    PriceListCreate, PriceListUpdate,
    SupplierDocumentCreate, SupplierDocumentUpdate,
    SupplierCommunicationCreate, SupplierCommunicationUpdate,
    SupplierSearchFilters
)

class CRUDSupplier(CRUDBase[Supplier, SupplierCreate, SupplierUpdate]):
    """CRUD operations for Supplier"""
    
    def get_multi_by_user(
        self, 
        db: Session, 
        *, 
        user_id: int, 
        workspace_id: Optional[int] = None,
        skip: int = 0, 
        limit: int = 100
    ) -> List[Supplier]:
        """Get all suppliers for a specific user"""
        query = db.query(self.model).filter(Supplier.user_id == user_id)
        
        if workspace_id:
            query = query.filter(Supplier.workspace_id == workspace_id)
            
        return (
            query.order_by(Supplier.name)
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_by_workspace(
        self, 
        db: Session, 
        *, 
        workspace_id: int,
        skip: int = 0, 
        limit: int = 100
    ) -> List[Supplier]:
        """Get all suppliers for a specific workspace"""
        return (
            db.query(self.model)
            .filter(Supplier.workspace_id == workspace_id)
            .order_by(Supplier.name)
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def search_suppliers(
        self,
        db: Session,
        *,
        user_id: int,
        workspace_id: Optional[int] = None,
        filters: SupplierSearchFilters,
        skip: int = 0,
        limit: int = 100
    ) -> List[Supplier]:
        """Search suppliers with various filters"""
        query = db.query(self.model).filter(Supplier.user_id == user_id)
        
        if workspace_id:
            query = query.filter(Supplier.workspace_id == workspace_id)
        
        if filters.name:
            query = query.filter(
                or_(
                    Supplier.name.ilike(f"%{filters.name}%"),
                    Supplier.contact_person.ilike(f"%{filters.name}%")
                )
            )
        
        if filters.status:
            query = query.filter(Supplier.status == filters.status)
        
        if filters.tags and len(filters.tags) > 0:
            for tag in filters.tags:
                query = query.filter(Supplier.tags.contains(tag))
        
        if filters.rating_min:
            query = query.filter(Supplier.rating >= filters.rating_min)
            
        if filters.rating_max:
            query = query.filter(Supplier.rating <= filters.rating_max)
        
        return (
            query.order_by(Supplier.name)
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_with_details(self, db: Session, *, supplier_id: int) -> Optional[Supplier]:
        """Get supplier with all related data loaded"""
        return (
            db.query(self.model)
            .options(
                joinedload(Supplier.products),
                joinedload(Supplier.communications),
                joinedload(Supplier.documents),
                joinedload(Supplier.price_lists)
            )
            .filter(Supplier.id == supplier_id)
            .first()
        )
    
    def get_by_name_and_workspace(
        self, 
        db: Session, 
        *, 
        name: str, 
        workspace_id: int
    ) -> Optional[Supplier]:
        """Get supplier by name within a workspace"""
        return (
            db.query(self.model)
            .filter(Supplier.name == name)
            .filter(Supplier.workspace_id == workspace_id)
            .first()
        )

class CRUDSupplierProduct(CRUDBase[SupplierProduct, SupplierProductCreate, SupplierProductUpdate]):
    """CRUD operations for SupplierProduct"""
    
    def get_by_supplier(
        self, 
        db: Session, 
        *, 
        supplier_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[SupplierProduct]:
        """Get all products for a specific supplier"""
        return (
            db.query(self.model)
            .filter(SupplierProduct.supplier_id == supplier_id)
            .filter(SupplierProduct.is_active == True)
            .order_by(SupplierProduct.name)
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def search_products(
        self,
        db: Session,
        *,
        supplier_ids: Optional[List[int]] = None,
        name: Optional[str] = None,
        category: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[SupplierProduct]:
        """Search products across suppliers"""
        query = db.query(self.model).filter(SupplierProduct.is_active == True)
        
        if supplier_ids:
            query = query.filter(SupplierProduct.supplier_id.in_(supplier_ids))
        
        if name:
            query = query.filter(SupplierProduct.name.ilike(f"%{name}%"))
        
        if category:
            query = query.filter(SupplierProduct.category.ilike(f"%{category}%"))
        
        return (
            query.order_by(SupplierProduct.name)
            .offset(skip)
            .limit(limit)
            .all()
        )

class CRUDPriceList(CRUDBase[PriceList, PriceListCreate, PriceListUpdate]):
    """CRUD operations for PriceList"""
    
    def get_by_product(
        self, 
        db: Session, 
        *, 
        product_id: int,
        active_only: bool = True
    ) -> List[PriceList]:
        """Get all price lists for a specific product"""
        query = db.query(self.model).filter(PriceList.product_id == product_id)
        
        if active_only:
            query = query.filter(PriceList.is_active == True)
        
        return query.order_by(PriceList.valid_from.desc()).all()
    
    def get_current_price(
        self, 
        db: Session, 
        *, 
        product_id: int,
        quantity: int = 1
    ) -> Optional[PriceList]:
        """Get current active price for a product with specific quantity"""
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        
        return (
            db.query(self.model)
            .filter(PriceList.product_id == product_id)
            .filter(PriceList.is_active == True)
            .filter(PriceList.valid_from <= now)
            .filter(
                or_(
                    PriceList.valid_until.is_(None),
                    PriceList.valid_until > now
                )
            )
            .filter(PriceList.min_quantity <= quantity)
            .order_by(PriceList.min_quantity.desc())
            .first()
        )
    
    def compare_prices(
        self,
        db: Session,
        *,
        product_name: str,
        supplier_ids: Optional[List[int]] = None,
        quantity: int = 1
    ) -> List[Dict[str, Any]]:
        """Compare prices for similar products across suppliers"""
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        
        query = (
            db.query(
                PriceList,
                SupplierProduct,
                Supplier
            )
            .join(SupplierProduct, PriceList.product_id == SupplierProduct.id)
            .join(Supplier, SupplierProduct.supplier_id == Supplier.id)
            .filter(SupplierProduct.name.ilike(f"%{product_name}%"))
            .filter(PriceList.is_active == True)
            .filter(SupplierProduct.is_active == True)
            .filter(Supplier.status == SupplierStatus.ACTIVE)
            .filter(PriceList.valid_from <= now)
            .filter(
                or_(
                    PriceList.valid_until.is_(None),
                    PriceList.valid_until > now
                )
            )
            .filter(PriceList.min_quantity <= quantity)
        )
        
        if supplier_ids:
            query = query.filter(Supplier.id.in_(supplier_ids))
        
        results = query.all()
        
        price_comparison = []
        for price_list, product, supplier in results:
            price_comparison.append({
                "supplier_id": supplier.id,
                "supplier_name": supplier.name,
                "product_id": product.id,
                "product_name": product.name,
                "price": float(price_list.price),
                "currency": price_list.currency,
                "min_quantity": price_list.min_quantity,
                "delivery_time_days": product.delivery_time_days,
                "valid_until": price_list.valid_until
            })
        
        return sorted(price_comparison, key=lambda x: x["price"])

class CRUDSupplierDocument(CRUDBase[SupplierDocument, SupplierDocumentCreate, SupplierDocumentUpdate]):
    """CRUD operations for SupplierDocument"""
    
    def get_by_supplier(
        self, 
        db: Session, 
        *, 
        supplier_id: int,
        document_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[SupplierDocument]:
        """Get all documents for a specific supplier"""
        query = db.query(self.model).filter(SupplierDocument.supplier_id == supplier_id)
        
        if document_type:
            query = query.filter(SupplierDocument.document_type == document_type)
        
        return (
            query.order_by(SupplierDocument.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

class CRUDSupplierCommunication(CRUDBase[SupplierCommunication, SupplierCommunicationCreate, SupplierCommunicationUpdate]):
    """CRUD operations for SupplierCommunication"""
    
    def get_by_supplier(
        self, 
        db: Session, 
        *, 
        supplier_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[SupplierCommunication]:
        """Get all communications for a specific supplier"""
        return (
            db.query(self.model)
            .filter(SupplierCommunication.supplier_id == supplier_id)
            .order_by(SupplierCommunication.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_recent_by_supplier(
        self, 
        db: Session, 
        *, 
        supplier_id: int,
        limit: int = 5
    ) -> List[SupplierCommunication]:
        """Get recent communications for a supplier"""
        return (
            db.query(self.model)
            .filter(SupplierCommunication.supplier_id == supplier_id)
            .order_by(SupplierCommunication.created_at.desc())
            .limit(limit)
            .all()
        )

# Create instances
supplier = CRUDSupplier(Supplier)
supplier_product = CRUDSupplierProduct(SupplierProduct)
price_list = CRUDPriceList(PriceList)
supplier_document = CRUDSupplierDocument(SupplierDocument)
supplier_communication = CRUDSupplierCommunication(SupplierCommunication)