import React, { useState, useEffect } from 'react';
import { 
  FolderIcon, 
  DocumentIcon, 
  PhotoIcon, 
  FilmIcon,
  MusicalNoteIcon,
  CodeBracketIcon,
  ArchiveBoxIcon,
  ChartBarIcon,
  PresentationChartLineIcon,
  SparklesIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ClockIcon
} from '@heroicons/react/24/outline';

const SmartOrganizer = () => {
  const [selectedDirectory, setSelectedDirectory] = useState('');
  const [organizationPlan, setOrganizationPlan] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [capabilities, setCapabilities] = useState(null);
  const [isDryRun, setIsDryRun] = useState(true);
  const [showResults, setShowResults] = useState(false);

  // Category icons mapping
  const categoryIcons = {
    documents: DocumentIcon,
    images: PhotoIcon,
    videos: FilmIcon,
    audio: MusicalNoteIcon,
    code: CodeBracketIcon,
    archives: ArchiveBoxIcon,
    spreadsheets: ChartBarIcon,
    presentations: PresentationChartLineIcon,
    other: FolderIcon
  };

  useEffect(() => {
    fetchCapabilities();
  }, []);

  const fetchCapabilities = async () => {
    try {
      const response = await window.electronAPI.apiRequest('/api/smart-organize/capabilities');
      setCapabilities(response);
    } catch (error) {
      console.error('Failed to fetch capabilities:', error);
    }
  };

  const handleDirectorySelect = async () => {
    try {
      const result = await window.electronAPI.selectDirectory();
      if (result && !result.canceled) {
        setSelectedDirectory(result.filePaths[0]);
        setOrganizationPlan(null);
        setShowResults(false);
      }
    } catch (error) {
      console.error('Failed to select directory:', error);
    }
  };

  const analyzeDirectory = async () => {
    if (!selectedDirectory) return;

    setIsAnalyzing(true);
    try {
      const response = await window.electronAPI.apiRequest('/api/smart-organize/organize-directory', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          directory_path: selectedDirectory,
          dry_run: isDryRun
        })
      });

      setOrganizationPlan(response);
      setShowResults(true);
    } catch (error) {
      console.error('Failed to analyze directory:', error);
      alert('Failed to analyze directory. Please try again.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const getCategoryColor = (category) => {
    const colors = {
      documents: 'bg-blue-100 text-blue-800',
      images: 'bg-green-100 text-green-800',
      videos: 'bg-purple-100 text-purple-800',
      audio: 'bg-yellow-100 text-yellow-800',
      code: 'bg-gray-100 text-gray-800',
      archives: 'bg-orange-100 text-orange-800',
      spreadsheets: 'bg-emerald-100 text-emerald-800',
      presentations: 'bg-red-100 text-red-800',
      other: 'bg-slate-100 text-slate-800'
    };
    return colors[category] || colors.other;
  };

  const renderCategoryCard = (category, files) => {
    const IconComponent = categoryIcons[category] || FolderIcon;
    const colorClass = getCategoryColor(category);

    return (
      <div key={category} className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-shadow">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-3">
            <div className={`p-2 rounded-lg ${colorClass}`}>
              <IconComponent className="h-5 w-5" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 capitalize">{category}</h3>
              <p className="text-sm text-gray-500">{files.length} files</p>
            </div>
          </div>
        </div>
        
        <div className="space-y-1 max-h-32 overflow-y-auto">
          {files.slice(0, 5).map((file, index) => (
            <div key={index} className="text-sm text-gray-600 truncate">
              {file.path}
            </div>
          ))}
          {files.length > 5 && (
            <div className="text-sm text-gray-400 italic">
              ... and {files.length - 5} more files
            </div>
          )}
        </div>
      </div>
    );
  };

  const renderSuggestions = (suggestions) => {
    if (!suggestions || suggestions.length === 0) return null;

    return (
      <div className="bg-blue-50 rounded-lg p-4 mt-6">
        <h3 className="font-semibold text-blue-900 mb-3 flex items-center">
          <SparklesIcon className="h-5 w-5 mr-2" />
          Smart Organization Suggestions
        </h3>
        <div className="space-y-2">
          {suggestions.map((suggestion, index) => (
            <div key={index} className="bg-white rounded p-3 border border-blue-200">
              <p className="text-sm text-gray-800">{suggestion.description}</p>
              {suggestion.folder_name && (
                <p className="text-xs text-blue-600 mt-1">
                  Suggested folder: {suggestion.folder_name}
                </p>
              )}
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2 flex items-center">
          <SparklesIcon className="h-8 w-8 mr-3 text-blue-600" />
          Smart File Organizer
        </h1>
        <p className="text-gray-600">
          AI-powered file organization that understands your content and suggests intelligent folder structures.
        </p>
        
        {capabilities && (
          <div className="mt-4 flex items-center space-x-4 text-sm">
            <div className={`flex items-center ${capabilities.ai_available ? 'text-green-600' : 'text-yellow-600'}`}>
              {capabilities.ai_available ? (
                <CheckCircleIcon className="h-4 w-4 mr-1" />
              ) : (
                <ExclamationTriangleIcon className="h-4 w-4 mr-1" />
              )}
              AI Analysis: {capabilities.ai_available ? 'Available' : 'Using rule-based fallback'}
            </div>
            <div className="text-gray-500">
              {capabilities.supported_categories?.length || 0} categories supported
            </div>
          </div>
        )}
      </div>

      {/* Directory Selection */}
      <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Select Directory to Organize</h2>
        
        <div className="space-y-4">
          <div className="flex items-center space-x-4">
            <button
              onClick={handleDirectorySelect}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Choose Directory
            </button>
            
            {selectedDirectory && (
              <div className="flex-1">
                <p className="text-sm text-gray-600">Selected:</p>
                <p className="font-mono text-sm bg-gray-100 p-2 rounded">{selectedDirectory}</p>
              </div>
            )}
          </div>
          
          <div className="flex items-center space-x-4">
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={isDryRun}
                onChange={(e) => setIsDryRun(e.target.checked)}
                className="rounded border-gray-300"
              />
              <span className="text-sm text-gray-700">Dry run (preview only, don't move files)</span>
            </label>
          </div>
          
          <button
            onClick={analyzeDirectory}
            disabled={!selectedDirectory || isAnalyzing}
            className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors flex items-center"
          >
            {isAnalyzing ? (
              <>
                <ClockIcon className="h-4 w-4 mr-2 animate-spin" />
                Analyzing...
              </>
            ) : (
              <>
                <SparklesIcon className="h-4 w-4 mr-2" />
                {isDryRun ? 'Preview Organization' : 'Organize Files'}
              </>
            )}
          </button>
        </div>
      </div>

      {/* Results */}
      {showResults && organizationPlan && (
        <div className="space-y-6">
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Analysis Results</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              <div className="bg-blue-50 rounded-lg p-4">
                <h3 className="font-semibold text-blue-900">Total Files</h3>
                <p className="text-2xl font-bold text-blue-700">{organizationPlan.total_files}</p>
              </div>
              <div className="bg-green-50 rounded-lg p-4">
                <h3 className="font-semibold text-green-900">Categories Found</h3>
                <p className="text-2xl font-bold text-green-700">
                  {Object.keys(organizationPlan.categories).length}
                </p>
              </div>
              <div className="bg-purple-50 rounded-lg p-4">
                <h3 className="font-semibold text-purple-900">Mode</h3>
                <p className="text-lg font-semibold text-purple-700">
                  {organizationPlan.dry_run ? 'Preview' : 'Executed'}
                </p>
              </div>
            </div>

            {organizationPlan.move_results && (
              <div className="bg-green-50 rounded-lg p-4 mb-6">
                <h3 className="font-semibold text-green-900 mb-2">Organization Results</h3>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>Files moved: <span className="font-semibold">{organizationPlan.move_results.moved_files}</span></div>
                  <div>Folders created: <span className="font-semibold">{organizationPlan.move_results.created_folders}</span></div>
                </div>
                {organizationPlan.move_results.errors?.length > 0 && (
                  <div className="mt-2">
                    <p className="text-red-600 font-semibold">Errors:</p>
                    <ul className="text-red-600 text-sm list-disc list-inside">
                      {organizationPlan.move_results.errors.map((error, index) => (
                        <li key={index}>{error}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {Object.entries(organizationPlan.categories).map(([category, files]) =>
                renderCategoryCard(category, files)
              )}
            </div>
            
            {renderSuggestions(organizationPlan.suggestions)}
          </div>
        </div>
      )}
    </div>
  );
};

export default SmartOrganizer;