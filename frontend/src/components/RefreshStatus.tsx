import React, { useEffect, useState } from 'react';
import { apiService, RefreshStatus as RefreshStatusType } from '../services/api';

const RefreshStatus: React.FC = () => {
  const [status, setStatus] = useState<RefreshStatusType | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchStatus = async () => {
    try {
      const data = await apiService.getRefreshStatus();
      setStatus(data);
    } catch (error) {
      console.error('Failed to fetch refresh status:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    // Refresh status every 30 seconds
    const interval = setInterval(fetchStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleForceRefresh = async () => {
    if (refreshing) return;
    
    setRefreshing(true);
    try {
      const result = await apiService.forceRefresh();
      setStatus(result.status);
      alert('✅ ' + result.message);
    } catch (error: any) {
      alert('❌ Refresh failed: ' + (error.response?.data?.detail || error.message));
    } finally {
      setRefreshing(false);
    }
  };

  const formatDateTime = (dateString: string | null) => {
    if (!dateString) return 'Never';
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} min${diffMins > 1 ? 's' : ''} ago`;
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
    
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
  };

  const getStatusColor = (statusStr: string) => {
    switch (statusStr) {
      case 'success':
        return 'text-green-600 bg-green-50';
      case 'refreshing':
        return 'text-blue-600 bg-blue-50';
      case 'error':
        return 'text-red-600 bg-red-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  const getStatusIcon = (statusStr: string) => {
    switch (statusStr) {
      case 'success':
        return '✓';
      case 'refreshing':
        return '↻';
      case 'error':
        return '✗';
      default:
        return '○';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center gap-2 text-sm text-gray-500">
        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-400"></div>
        <span>Loading status...</span>
      </div>
    );
  }

  if (!status) {
    return null;
  }

  return (
    <div className="flex items-center gap-4">
      {/* Status Indicator */}
      <div className="flex items-center gap-2">
        <div className={`px-3 py-1.5 rounded-full text-xs font-medium ${getStatusColor(status.status)}`}>
          <span className="mr-1">{getStatusIcon(status.status)}</span>
          {status.status === 'idle' ? 'Ready' : status.status.charAt(0).toUpperCase() + status.status.slice(1)}
        </div>
      </div>

      {/* Last Refresh */}
      <div className="flex flex-col text-xs">
        <span className="text-gray-500">Last Updated</span>
        <span className="font-medium text-gray-700">
          {formatDateTime(status.last_refresh)}
        </span>
      </div>

      {/* Models Count */}
      {status.models_updated > 0 && (
        <div className="flex flex-col text-xs">
          <span className="text-gray-500">Models</span>
          <span className="font-medium text-gray-700">{status.models_updated}</span>
        </div>
      )}

      {/* Refresh Button */}
      <button
        onClick={handleForceRefresh}
        disabled={refreshing}
        className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-all ${
          refreshing
            ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
            : 'bg-blue-600 text-white hover:bg-blue-700 hover:shadow-md'
        }`}
        title="Force refresh data from all sources"
      >
        {refreshing ? (
          <span className="flex items-center gap-1">
            <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-white"></div>
            Refreshing...
          </span>
        ) : (
          <span className="flex items-center gap-1">
            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Refresh Now
          </span>
        )}
      </button>

      {/* Error Indicator */}
      {status.errors && status.errors.length > 0 && (
        <div className="flex items-center gap-1 text-xs text-red-600" title={status.errors.join(', ')}>
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
          <span>{status.errors.length} error{status.errors.length > 1 ? 's' : ''}</span>
        </div>
      )}
    </div>
  );
};

export default RefreshStatus;

// Made with Bob