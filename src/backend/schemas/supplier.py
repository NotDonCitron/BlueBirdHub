from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, EmailStr
from decimal import Decimal
from datetime import datetime
from enum import Enum

class SupplierStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    BLOCKED = "blocked"

class DocumentType(str, Enum):
    CONTRACT = "contract"
    INVOICE = "invoice"
    PRICE_LIST = "price_list"
    CERTIFICATE = "certificate"
    QUOTATION = "quotation"
    OTHER = "other"

class VerificationStatus(str, Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"

class CommunicationType(str, Enum):
    EMAIL = "email"
    PHONE = "phone"
    MEETING = "meeting"
    NOTE = "note"

class SupplierBase(BaseModel):
    name: str
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[Dict[str, Any]] = None
    website: Optional[str] = None
    tax_id: Optional[str] = None
    payment_terms: Optional[str] = None
    status: SupplierStatus = SupplierStatus.ACTIVE
    rating: Optional[int] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = []

class SupplierCreate(SupplierBase):
    user_id: int
    workspace_id: int

class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[Dict[str, Any]] = None
    website: Optional[str] = None
    tax_id: Optional[str] = None
    payment_terms: Optional[str] = None
    status: Optional[SupplierStatus] = None
    rating: Optional[int] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None

class SupplierResponse(SupplierBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    workspace_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

class SupplierProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    unit: Optional[str] = None
    min_order_quantity: Optional[int] = None
    delivery_time_days: Optional[int] = None
    specifications: Optional[Dict[str, Any]] = None
    is_active: bool = True

class SupplierProductCreate(SupplierProductBase):
    supplier_id: int

class SupplierProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    unit: Optional[str] = None
    min_order_quantity: Optional[int] = None
    delivery_time_days: Optional[int] = None
    specifications: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class SupplierProductResponse(SupplierProductBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    supplier_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

class PriceListBase(BaseModel):
    price: Decimal
    currency: str = "EUR"
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    min_quantity: int = 1
    discount_tiers: Optional[List[Dict[str, Any]]] = None
    is_active: bool = True

class PriceListCreate(PriceListBase):
    supplier_id: int
    product_id: int

class PriceListUpdate(BaseModel):
    price: Optional[Decimal] = None
    currency: Optional[str] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    min_quantity: Optional[int] = None
    discount_tiers: Optional[List[Dict[str, Any]]] = None
    is_active: Optional[bool] = None

class PriceListResponse(PriceListBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    supplier_id: int
    product_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

class SupplierDocumentBase(BaseModel):
    document_type: DocumentType
    extracted_data: Optional[Dict[str, Any]] = None
    verification_status: VerificationStatus = VerificationStatus.PENDING
    notes: Optional[str] = None

class SupplierDocumentCreate(SupplierDocumentBase):
    supplier_id: int
    file_metadata_id: int

class SupplierDocumentUpdate(BaseModel):
    document_type: Optional[DocumentType] = None
    extracted_data: Optional[Dict[str, Any]] = None
    verification_status: Optional[VerificationStatus] = None
    notes: Optional[str] = None

class SupplierDocumentResponse(SupplierDocumentBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    supplier_id: int
    file_metadata_id: int
    verified_by_user_id: Optional[int] = None
    verified_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

class SupplierCommunicationBase(BaseModel):
    type: CommunicationType
    subject: Optional[str] = None
    content: str
    attachments: Optional[List[str]] = None
    scheduled_for: Optional[datetime] = None
    is_completed: bool = True

class SupplierCommunicationCreate(SupplierCommunicationBase):
    supplier_id: int
    user_id: int

class SupplierCommunicationUpdate(BaseModel):
    type: Optional[CommunicationType] = None
    subject: Optional[str] = None
    content: Optional[str] = None
    attachments: Optional[List[str]] = None
    scheduled_for: Optional[datetime] = None
    is_completed: Optional[bool] = None

class SupplierCommunicationResponse(SupplierCommunicationBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    supplier_id: int
    user_id: int
    created_at: datetime

class SupplierDetailResponse(SupplierResponse):
    products: List[SupplierProductResponse] = []
    recent_communications: List[SupplierCommunicationResponse] = []
    documents_count: int = 0
    price_lists_count: int = 0

class SupplierSearchFilters(BaseModel):
    name: Optional[str] = None
    status: Optional[SupplierStatus] = None
    tags: Optional[List[str]] = None
    category: Optional[str] = None
    rating_min: Optional[int] = None
    rating_max: Optional[int] = None

class PriceComparisonRequest(BaseModel):
    product_name: str
    category: Optional[str] = None
    quantity: int = 1
    supplier_ids: Optional[List[int]] = None

class PriceComparisonResponse(BaseModel):
    product_name: str
    total_suppliers: int
    best_price: Optional[Decimal] = None
    average_price: Optional[Decimal] = None
    price_entries: List[Dict[str, Any]] = []