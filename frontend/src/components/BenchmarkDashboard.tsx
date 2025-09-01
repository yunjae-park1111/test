import React, { useEffect, useState, useCallback, useMemo } from 'react';
import { useBenchmarkData } from '../hooks/useBenchmarkData';

interface BenchmarkMetrics {
  modelName: string;
  throughput: number;
  latency: number;
  memoryUsage: number;
  timestamp: string;
  commitSha: string;
}

interface BenchmarkDashboardProps {
  refreshInterval?: number;
  maxResults?: number;
  onModelSelect?: (modelName: string) => void;
}

interface FilterState {
  modelName: string;
  sortBy: 'throughput' | 'latency' | 'timestamp';
  sortOrder: 'asc' | 'desc';
}

const BenchmarkDashboard: React.FC<BenchmarkDashboardProps> = ({
  refreshInterval = 30000,
  maxResults = 50,
  onModelSelect
}) => {
  const [filters, setFilters] = useState<FilterState>({
    modelName: '',
    sortBy: 'timestamp',
    sortOrder: 'desc'
  });

  const { 
    data: benchmarkData, 
    loading, 
    error, 
    refetch 
  } = useBenchmarkData({
    refreshInterval,
    maxResults,
    modelFilter: filters.modelName
  });

  // 메모이제이션을 통한 성능 최적화
  const sortedData = useMemo(() => {
    if (!benchmarkData) return [];
    
    return [...benchmarkData].sort((a, b) => {
      const aValue = a[filters.sortBy];
      const bValue = b[filters.sortBy];
      
      if (filters.sortOrder === 'asc') {
        return aValue > bValue ? 1 : -1;
      }
      return aValue < bValue ? 1 : -1;
    });
  }, [benchmarkData, filters.sortBy, filters.sortOrder]);

  const uniqueModels = useMemo(() => {
    return Array.from(new Set(benchmarkData?.map(item => item.modelName) || []));
  }, [benchmarkData]);

  // 콜백 함수 메모이제이션
  const handleFilterChange = useCallback((newFilters: Partial<FilterState>) => {
    setFilters(prev => ({ ...prev, ...newFilters }));
  }, []);

  const handleModelClick = useCallback((modelName: string) => {
    onModelSelect?.(modelName);
  }, [onModelSelect]);

  const handleRefresh = useCallback(() => {
    refetch();
  }, [refetch]);

  useEffect(() => {
    const interval = setInterval(refetch, refreshInterval);
    return () => clearInterval(interval);
  }, [refetch, refreshInterval]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-3 text-gray-600">Loading benchmark data...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800">Error loading data</h3>
            <p className="text-sm text-red-700 mt-1">{error}</p>
            <button 
              onClick={handleRefresh}
              className="mt-2 text-sm bg-red-100 hover:bg-red-200 text-red-800 px-3 py-1 rounded"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with controls */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <h2 className="text-xl font-semibold text-gray-900">
            vLLM Benchmark Dashboard
          </h2>
          
          <div className="flex items-center gap-3">
            <select
              value={filters.modelName}
              onChange={(e) => handleFilterChange({ modelName: e.target.value })}
              className="rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            >
              <option value="">All Models</option>
              {uniqueModels.map(model => (
                <option key={model} value={model}>{model}</option>
              ))}
            </select>
            
            <select
              value={`${filters.sortBy}-${filters.sortOrder}`}
              onChange={(e) => {
                const [sortBy, sortOrder] = e.target.value.split('-') as [typeof filters.sortBy, typeof filters.sortOrder];
                handleFilterChange({ sortBy, sortOrder });
              }}
              className="rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            >
              <option value="timestamp-desc">Latest First</option>
              <option value="timestamp-asc">Oldest First</option>
              <option value="throughput-desc">Highest Throughput</option>
              <option value="throughput-asc">Lowest Throughput</option>
              <option value="latency-asc">Lowest Latency</option>
              <option value="latency-desc">Highest Latency</option>
            </select>
            
            <button
              onClick={handleRefresh}
              className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              <svg className="-ml-0.5 mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Refresh
            </button>
          </div>
        </div>
      </div>

      {/* Results table */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Model
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Throughput (tokens/s)
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Latency (ms)
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Memory (GB)
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Timestamp
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Commit
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {sortedData.map((benchmark, index) => (
                <tr 
                  key={`${benchmark.modelName}-${benchmark.timestamp}-${index}`}
                  className="hover:bg-gray-50 cursor-pointer"
                  onClick={() => handleModelClick(benchmark.modelName)}
                >
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {benchmark.modelName}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {benchmark.throughput.toFixed(2)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {benchmark.latency.toFixed(1)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {benchmark.memoryUsage.toFixed(1)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(benchmark.timestamp).toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 font-mono">
                    {benchmark.commitSha.slice(0, 8)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        
        {sortedData.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            No benchmark data available
          </div>
        )}
      </div>
    </div>
  );
};

export default BenchmarkDashboard;
