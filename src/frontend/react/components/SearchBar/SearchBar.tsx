import React from 'react';
import './SearchBar.css';

interface SearchBarProps {
  onSearch: (query: string) => void;
  isLoading: boolean;
}

const SearchBar: React.FC<SearchBarProps> = ({ onSearch, isLoading }) => {
  return (
    <div className="search-bar-container">
      <input
        type="text"
        className="search-input"
        placeholder="Search tasks, files, workspaces..."
        onChange={(e) => onSearch(e.target.value)}
        disabled={isLoading}
      />
      {isLoading && <div className="search-spinner"></div>}
    </div>
  );
};

export default SearchBar; 