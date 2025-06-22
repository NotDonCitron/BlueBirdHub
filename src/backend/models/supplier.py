from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, ForeignKey, Text, Enum, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.backend.database.database import Base
import enum

class SupplierStatus(enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    BLOCKED = "blocked"

class DocumentType(enum.Enum):
    CONTRACT = "contract"
    INVOICE = "invoice"
    PRICE_LIST = "price_list"
    CERTIFICATE = "certificate"
    QUOTATION = "quotation"
    OTHER = "other"

class VerificationStatus(enum.Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"

class CommunicationType(enum.Enum):
    EMAIL = "email"
    PHONE = "phone"
    MEETING = "meeting"
    NOTE = "note"

class Supplier(Base):
    __tablename__ = "suppliers"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False)
    name = Column(String(200), nullable=False, index=True)
    contact_person = Column(String(100))
    email = Column(String(100), index=True) 
    phone = Column(String(50))
    address = Column(JSON)  # {street, city, postal_code, country}
    website = Column(String(200))
    tax_id = Column(String(50))
    payment_terms = Column(String(100))  # e.g., "30 days net"
    status = Column(Enum(SupplierStatus), default=SupplierStatus.ACTIVE, index=True)
    rating = Column(Integer)  # 1-5 stars
    notes = Column(Text)
    tags = Column(JSON)  # List of tags for categorization
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="suppliers")
    workspace = relationship("Workspace", back_populates="suppliers")
    products = relationship("SupplierProduct", back_populates="supplier", cascade="all, delete-orphan")
    documents = relationship("SupplierDocument", back_populates="supplier", cascade="all, delete-orphan")
    communications = relationship("SupplierCommunication", back_populates="supplier", cascade="all, delete-orphan")
    price_lists = relationship("PriceList", back_populates="supplier", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Supplier(id={self.id}, name='{self.name}', status='{self.status.value}')>"

class SupplierProduct(Base):
    __tablename__ = "supplier_products"
    
    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text)
    category = Column(String(100), index=True)
    unit = Column(String(20))  # e.g., "kg", "liter", "piece"
    min_order_quantity = Column(Integer)
    delivery_time_days = Column(Integer)
    specifications = Column(JSON)  # Technical specs, certifications, etc.
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    supplier = relationship("Supplier", back_populates="products")
    price_lists = relationship("PriceList", back_populates="product", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<SupplierProduct(id={self.id}, name='{self.name}', category='{self.category}')>"

class PriceList(Base):
    __tablename__ = "price_lists"
    
    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("supplier_products.id"), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="EUR")
    valid_from = Column(DateTime(timezone=True), server_default=func.now())
    valid_until = Column(DateTime(timezone=True))
    min_quantity = Column(Integer, default=1)
    discount_tiers = Column(JSON)  # [{quantity: 100, discount_percent: 5}]
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    supplier = relationship("Supplier", back_populates="price_lists")
    product = relationship("SupplierProduct", back_populates="price_lists")
    
    def __repr__(self):
        return f"<PriceList(id={self.id}, price={self.price} {self.currency})>"

class SupplierDocument(Base):
    __tablename__ = "supplier_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    file_metadata_id = Column(Integer, ForeignKey("file_metadata.id"), nullable=False)
    document_type = Column(Enum(DocumentType), nullable=False, index=True)
    extracted_data = Column(JSON)  # AI-extracted information
    verification_status = Column(Enum(VerificationStatus), default=VerificationStatus.PENDING)
    verified_by_user_id = Column(Integer, ForeignKey("users.id"))
    verified_at = Column(DateTime(timezone=True))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    supplier = relationship("Supplier", back_populates="documents")
    file_metadata = relationship("FileMetadata")
    verified_by = relationship("User")
    
    def __repr__(self):
        return f"<SupplierDocument(id={self.id}, type='{self.document_type.value}', status='{self.verification_status.value}')>"

class SupplierCommunication(Base):
    __tablename__ = "supplier_communications"
    
    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    type = Column(Enum(CommunicationType), nullable=False)
    subject = Column(String(200))
    content = Column(Text, nullable=False)
    attachments = Column(JSON)  # List of file references
    scheduled_for = Column(DateTime(timezone=True))  # For follow-up reminders
    is_completed = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    supplier = relationship("Supplier", back_populates="communications")
    user = relationship("User")
    
    def __repr__(self):
        return f"<SupplierCommunication(id={self.id}, type='{self.type.value}', subject='{self.subject}')>"