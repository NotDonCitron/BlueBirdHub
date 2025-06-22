import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useApi } from '../../contexts/ApiContext';
import './SupplierManager.css';

interface Supplier {
  id: number;
  name: string;
  contact_person?: string;
  email?: string;
  phone?: string;
  address?: {
    street?: string;
    city?: string;
    postal_code?: string;
    country?: string;
  };
  website?: string;
  tax_id?: string;
  payment_terms?: string;
  status: 'active' | 'inactive' | 'blocked';
  rating?: number;
  notes?: string;
  tags?: string[];
  user_id: number;
  workspace_id: number;
  created_at: string;
  updated_at?: string;
  products?: SupplierProduct[];
  recent_communications?: SupplierCommunication[];
  documents_count?: number;
  price_lists_count?: number;
}

interface SupplierProduct {
  id: number;
  supplier_id: number;
  name: string;
  description?: string;
  category?: string;
  unit?: string;
  min_order_quantity?: number;
  delivery_time_days?: number;
  specifications?: Record<string, any>;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

interface SupplierCommunication {
  id: number;
  supplier_id: number;
  user_id: number;
  type: 'email' | 'phone' | 'meeting' | 'note';
  subject?: string;
  content: string;
  attachments?: string[];
  scheduled_for?: string;
  is_completed: boolean;
  created_at: string;
}

interface PriceComparison {
  product_name: string;
  total_suppliers: number;
  best_price?: number;
  average_price?: number;
  price_entries: Array<{
    supplier_id: number;
    supplier_name: string;
    product_id: number;
    product_name: string;
    price: number;
    currency: string;
    min_quantity: number;
    delivery_time_days?: number;
    valid_until?: string;
  }>;
}

interface SupplierFilter {
  search: string;
  status: string;
  tags: string[];
  category: string;
  rating_min?: number;
  rating_max?: number;
}

const SupplierManager: React.FC = () => {
  const { makeApiRequest } = useApi();
  const [activeTab, setActiveTab] = useState<'overview' | 'suppliers' | 'products' | 'compare' | 'communications'>('overview');
  
  // State
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [selectedSupplier, setSelectedSupplier] = useState<Supplier | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filters, setFilters] = useState<SupplierFilter>({
    search: '',
    status: '',
    tags: [],
    category: '',
  });
  const [priceComparison, setPriceComparison] = useState<PriceComparison | null>(null);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [showAddModal, setShowAddModal] = useState(false);
  const [showCompareModal, setShowCompareModal] = useState(false);

  // Load suppliers on component mount
  useEffect(() => {
    loadSuppliers();
  }, []);

  const loadSuppliers = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await makeApiRequest('/suppliers/', 'GET');
      setSuppliers(response || []);
    } catch (err: any) {
      setError(err.message || 'Failed to load suppliers');
    } finally {
      setLoading(false);
    }
  };

  const filteredSuppliers = suppliers.filter(supplier => {
    if (searchTerm && !supplier.name.toLowerCase().includes(searchTerm.toLowerCase()) &&
        !supplier.contact_person?.toLowerCase().includes(searchTerm.toLowerCase())) {
      return false;
    }
    if (filters.status && supplier.status !== filters.status) {
      return false;
    }
    if (filters.rating_min && (!supplier.rating || supplier.rating < filters.rating_min)) {
      return false;
    }
    if (filters.rating_max && (!supplier.rating || supplier.rating > filters.rating_max)) {
      return false;
    }
    return true;
  });

  const handleSupplierSelect = async (supplier: Supplier) => {
    setSelectedSupplier(supplier);
    // Load detailed supplier information
    try {
      const response = await makeApiRequest(`/suppliers/${supplier.id}`, 'GET');
      setSelectedSupplier(response);
    } catch (err) {
      console.error('Failed to load supplier details:', err);
    }
  };

  const handleComparePrice = async (productName: string) => {
    setLoading(true);
    try {
      const response = await makeApiRequest('/suppliers/compare-prices', 'POST', {
        product_name: productName,
        quantity: 1
      });
      setPriceComparison(response);
      setShowCompareModal(true);
    } catch (err: any) {
      setError(err.message || 'Failed to compare prices');
    } finally {
      setLoading(false);
    }
  };

  const renderSupplierCard = (supplier: Supplier) => (
    <div 
      key={supplier.id} 
      className="supplier-card"
      onClick={() => handleSupplierSelect(supplier)}
    >
      <div className="supplier-header">
        <div className="supplier-avatar">
          <span>{supplier.name.charAt(0).toUpperCase()}</span>
        </div>
        <div className="supplier-info">
          <h3>{supplier.name}</h3>
          {supplier.contact_person && (
            <p className="contact-person">{supplier.contact_person}</p>
          )}
          <div className={`status-badge status-${supplier.status}`}>
            {supplier.status}
          </div>
        </div>
      </div>
      
      <div className="supplier-details">
        {supplier.email && (
          <div className="detail-item">
            <span className="icon">📧</span>
            <span>{supplier.email}</span>
          </div>
        )}
        {supplier.phone && (
          <div className="detail-item">
            <span className="icon">📞</span>
            <span>{supplier.phone}</span>
          </div>
        )}
        {supplier.rating && (
          <div className="detail-item">
            <span className="icon">⭐</span>
            <span>{supplier.rating}/5</span>
          </div>
        )}
      </div>

      <div className="supplier-tags">
        {supplier.tags?.map(tag => (
          <span key={tag} className="tag">{tag}</span>
        ))}
      </div>

      <div className="supplier-stats">
        <div className="stat">
          <span className="stat-value">{supplier.products?.length || 0}</span>
          <span className="stat-label">Products</span>
        </div>
        <div className="stat">
          <span className="stat-value">{supplier.documents_count || 0}</span>
          <span className="stat-label">Documents</span>
        </div>
        <div className="stat">
          <span className="stat-value">{supplier.price_lists_count || 0}</span>
          <span className="stat-label">Price Lists</span>
        </div>
      </div>
    </div>
  );

  const renderSupplierList = (supplier: Supplier) => (
    <div 
      key={supplier.id} 
      className="supplier-list-item"
      onClick={() => handleSupplierSelect(supplier)}
    >
      <div className="supplier-list-info">
        <div className="supplier-list-header">
          <h3>{supplier.name}</h3>
          <div className={`status-badge status-${supplier.status}`}>
            {supplier.status}
          </div>
        </div>
        <div className="supplier-list-details">
          <span>{supplier.contact_person}</span>
          <span>{supplier.email}</span>
          <span>{supplier.phone}</span>
          {supplier.rating && <span>⭐ {supplier.rating}/5</span>}
        </div>
      </div>
      <div className="supplier-list-stats">
        <span>{supplier.products?.length || 0} products</span>
        <span>{supplier.documents_count || 0} docs</span>
      </div>
    </div>
  );

  const renderOverview = () => (
    <div className="overview-panel">
      <div className="overview-stats">
        <div className="stat-card">
          <h3>Total Suppliers</h3>
          <div className="stat-number">{suppliers.length}</div>
        </div>
        <div className="stat-card">
          <h3>Active Suppliers</h3>
          <div className="stat-number">
            {suppliers.filter(s => s.status === 'active').length}
          </div>
        </div>
        <div className="stat-card">
          <h3>Total Products</h3>
          <div className="stat-number">
            {suppliers.reduce((total, s) => total + (s.products?.length || 0), 0)}
          </div>
        </div>
        <div className="stat-card">
          <h3>Average Rating</h3>
          <div className="stat-number">
            {suppliers.length > 0 
              ? (suppliers.reduce((sum, s) => sum + (s.rating || 0), 0) / suppliers.length).toFixed(1)
              : '0.0'
            }
          </div>
        </div>
      </div>

      <div className="recent-activity">
        <h3>Recent Activity</h3>
        <div className="activity-list">
          {suppliers.slice(0, 5).map(supplier => (
            <div key={supplier.id} className="activity-item">
              <div className="activity-icon">🏪</div>
              <div className="activity-content">
                <span className="activity-title">{supplier.name}</span>
                <span className="activity-time">
                  {new Date(supplier.created_at).toLocaleDateString()}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  const renderToolbar = () => (
    <div className="toolbar">
      <div className="toolbar-left">
        <div className="search-box">
          <input
            type="text"
            placeholder="Search suppliers..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          <span className="search-icon">🔍</span>
        </div>
        
        <select 
          value={filters.status} 
          onChange={(e) => setFilters({...filters, status: e.target.value})}
        >
          <option value="">All Status</option>
          <option value="active">Active</option>
          <option value="inactive">Inactive</option>
          <option value="blocked">Blocked</option>
        </select>
      </div>

      <div className="toolbar-right">
        <div className="view-toggle">
          <button 
            className={viewMode === 'grid' ? 'active' : ''}
            onClick={() => setViewMode('grid')}
          >
            ⊞
          </button>
          <button 
            className={viewMode === 'list' ? 'active' : ''}
            onClick={() => setViewMode('list')}
          >
            ☰
          </button>
        </div>
        
        <button 
          className="btn-primary"
          onClick={() => setShowAddModal(true)}
        >
          Add Supplier
        </button>
        
        <button 
          className="btn-secondary"
          onClick={() => handleComparePrice('')}
        >
          Compare Prices
        </button>
      </div>
    </div>
  );

  if (loading && suppliers.length === 0) {
    return (
      <div className="supplier-manager loading">
        <div className="loading-spinner">Loading suppliers...</div>
      </div>
    );
  }

  return (
    <div className="supplier-manager">
      <div className="supplier-header">
        <h1>🏪 Lieferanten-Hub</h1>
        <p>Manage your suppliers, compare prices, and track communications</p>
      </div>

      <div className="supplier-tabs">
        <button 
          className={activeTab === 'overview' ? 'active' : ''}
          onClick={() => setActiveTab('overview')}
        >
          Overview
        </button>
        <button 
          className={activeTab === 'suppliers' ? 'active' : ''}
          onClick={() => setActiveTab('suppliers')}
        >
          Suppliers
        </button>
        <button 
          className={activeTab === 'products' ? 'active' : ''}
          onClick={() => setActiveTab('products')}
        >
          Products
        </button>
        <button 
          className={activeTab === 'compare' ? 'active' : ''}
          onClick={() => setActiveTab('compare')}
        >
          Price Compare
        </button>
        <button 
          className={activeTab === 'communications' ? 'active' : ''}
          onClick={() => setActiveTab('communications')}
        >
          Communications
        </button>
      </div>

      {error && (
        <div className="error-message">
          <span>{error}</span>
          <button onClick={() => setError(null)}>×</button>
        </div>
      )}

      <div className="supplier-content">
        {activeTab === 'overview' && renderOverview()}
        
        {activeTab === 'suppliers' && (
          <>
            {renderToolbar()}
            <div className={`suppliers-container ${viewMode}`}>
              {filteredSuppliers.map(supplier => 
                viewMode === 'grid' 
                  ? renderSupplierCard(supplier)
                  : renderSupplierList(supplier)
              )}
            </div>
          </>
        )}
        
        {activeTab === 'products' && (
          <div className="products-panel">
            <h3>Product Management</h3>
            <p>Manage products across all suppliers</p>
          </div>
        )}
        
        {activeTab === 'compare' && (
          <div className="compare-panel">
            <h3>Price Comparison</h3>
            <div className="compare-form">
              <input 
                type="text" 
                placeholder="Enter product name to compare prices..."
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    handleComparePrice((e.target as HTMLInputElement).value);
                  }
                }}
              />
              <button onClick={() => handleComparePrice('')}>
                Compare
              </button>
            </div>
            
            {priceComparison && (
              <div className="comparison-results">
                <h4>{priceComparison.product_name}</h4>
                <div className="comparison-stats">
                  <span>Suppliers: {priceComparison.total_suppliers}</span>
                  <span>Best Price: €{priceComparison.best_price}</span>
                  <span>Average: €{priceComparison.average_price}</span>
                </div>
                <div className="comparison-list">
                  {priceComparison.price_entries.map((entry, index) => (
                    <div key={index} className="comparison-item">
                      <span className="supplier-name">{entry.supplier_name}</span>
                      <span className="product-name">{entry.product_name}</span>
                      <span className="price">€{entry.price}</span>
                      <span className="delivery">{entry.delivery_time_days} days</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
        
        {activeTab === 'communications' && (
          <div className="communications-panel">
            <h3>Communication History</h3>
            <p>Track all supplier communications</p>
          </div>
        )}
      </div>

      {selectedSupplier && (
        <div className="supplier-detail-modal">
          <div className="modal-content">
            <div className="modal-header">
              <h2>{selectedSupplier.name}</h2>
              <button onClick={() => setSelectedSupplier(null)}>×</button>
            </div>
            <div className="modal-body">
              <div className="supplier-detail-info">
                <p><strong>Contact:</strong> {selectedSupplier.contact_person}</p>
                <p><strong>Email:</strong> {selectedSupplier.email}</p>
                <p><strong>Phone:</strong> {selectedSupplier.phone}</p>
                <p><strong>Status:</strong> {selectedSupplier.status}</p>
                {selectedSupplier.rating && (
                  <p><strong>Rating:</strong> {selectedSupplier.rating}/5 ⭐</p>
                )}
              </div>
              
              {selectedSupplier.products && selectedSupplier.products.length > 0 && (
                <div className="supplier-products">
                  <h3>Products</h3>
                  <div className="products-list">
                    {selectedSupplier.products.map(product => (
                      <div key={product.id} className="product-item">
                        <span className="product-name">{product.name}</span>
                        <span className="product-category">{product.category}</span>
                        <span className="product-delivery">{product.delivery_time_days} days</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SupplierManager;