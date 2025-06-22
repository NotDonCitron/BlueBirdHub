import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import './SearchResults.css';

interface SearchResultItem {
  id: string | number;
  title: string;
  type: 'task' | 'workspace' | 'file';
}

interface SearchResultsProps {
  results: SearchResultItem[];
  isLoading: boolean;
  onClose: () => void;
}

const getIconForType = (type: string) => {
  switch (type) {
    case 'task': return '✅';
    case 'workspace': return '🏠';
    case 'file': return '📁';
    default: return '🔍';
  }
};

const SearchResults: React.FC<SearchResultsProps> = ({ results, isLoading, onClose }) => {
  const navigate = useNavigate();
  const [activeIndex, setActiveIndex] = useState(-1);
  const flatResults = useMemo(() => results, [results]);

  const handleNavigation = (item: SearchResultItem) => {
    // In a real app, you would have dedicated routes
    onClose();
    switch(item.type) {
      case 'task':
        navigate(`/tasks?highlight=${item.id}`);
        break;
      case 'workspace':
        navigate(`/workspaces?highlight=${item.id}`);
        break;
      default:
        navigate('/');
    }
  };

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setActiveIndex(prev => (prev < flatResults.length - 1 ? prev + 1 : prev));
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setActiveIndex(prev => (prev > 0 ? prev - 1 : 0));
      } else if (e.key === 'Enter') {
        if (activeIndex >= 0 && activeIndex < flatResults.length) {
          handleNavigation(flatResults[activeIndex]);
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [activeIndex, flatResults, navigate]);

  useEffect(() => {
    setActiveIndex(-1);
  }, [results]);

  if (isLoading) {
    return <div className="search-results-container"><div className="loading-text">Loading...</div></div>;
  }

  if (results.length === 0) {
    return <div className="search-results-container"><div className="no-results-text">No results found.</div></div>;
  }

  const groupedResults = results.reduce((acc, item) => {
    (acc[item.type] = acc[item.type] || []).push(item);
    return acc;
  }, {} as Record<string, SearchResultItem[]>);

  const groupOrder: ('task' | 'workspace' | 'file')[] = ['task', 'workspace', 'file'];

  return (
    <div className="search-results-container">
      {groupOrder.map(groupName => (
        groupedResults[groupName] && (
          <div key={groupName} className="result-group">
            <h4 className="result-group-title">{groupName.charAt(0).toUpperCase() + groupName.slice(1)}s</h4>
            <ul className="result-group-list">
              {groupedResults[groupName].map(item => {
                const itemIndex = flatResults.findIndex(fr => fr.id === item.id);
                return (
                  <li 
                    key={item.id} 
                    className={`search-result-item ${itemIndex === activeIndex ? 'active' : ''}`}
                    onClick={() => handleNavigation(item)}
                    onMouseEnter={() => setActiveIndex(itemIndex)}
                  >
                    <span className="result-icon">{getIconForType(item.type)}</span>
                    <span className="result-title">{item.title}</span>
                  </li>
                );
              })}
            </ul>
          </div>
        )
      ))}
    </div>
  );
};

export default SearchResults; 