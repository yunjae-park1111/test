import { useState, useEffect, useCallback, useRef } from 'react';

interface BenchmarkMetrics {
  modelName: string;
  throughput: number;
  latency: number;
  memoryUsage: number;
  timestamp: string;
  commitSha: string;
}

interface UseBenchmarkDataOptions {
  refreshInterval?: number;
  maxResults?: number;
  modelFilter?: string;
  autoRefresh?: boolean;
}

interface UseBenchmarkDataReturn {
  data: BenchmarkMetrics[] | null;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
  lastUpdated: Date | null;
}

/**
 * vLLM 벤치마크 데이터를 관리하는 커스텀 훅
 * 
 * @param options - 데이터 페칭 옵션
 * @param options.refreshInterval - 자동 새로고침 간격 (ms)
 * @param options.maxResults - 최대 결과 수
 * @param options.modelFilter - 모델명 필터
 * @param options.autoRefresh - 자동 새로고침 활성화 여부
 * 
 * @returns 벤치마크 데이터와 상태 관리 함수들
 * 
 * @example
 * ```typescript
 * const { data, loading, error, refetch } = useBenchmarkData({
 *   refreshInterval: 30000,
 *   maxResults: 100,
 *   modelFilter: 'llama-7b'
 * });
 * ```
 */
export const useBenchmarkData = ({
  refreshInterval = 30000,
  maxResults = 50,
  modelFilter = '',
  autoRefresh = true
}: UseBenchmarkDataOptions = {}): UseBenchmarkDataReturn => {
  const [data, setData] = useState<BenchmarkMetrics[] | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  
  // AbortController를 사용한 요청 취소 관리
  const abortControllerRef = useRef<AbortController | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  // API 호출 함수
  const fetchBenchmarkData = useCallback(async (): Promise<BenchmarkMetrics[]> => {
    // 이전 요청 취소
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    
    abortControllerRef.current = new AbortController();
    
    const params = new URLSearchParams({
      limit: maxResults.toString(),
      ...(modelFilter && { model: modelFilter })
    });
    
    const response = await fetch(`/api/benchmarks?${params}`, {
      signal: abortControllerRef.current.signal,
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const result = await response.json();
    return result.data || [];
  }, [maxResults, modelFilter]);

  // 데이터 새로고침 함수
  const refetch = useCallback(async (): Promise<void> => {
    setLoading(true);
    setError(null);
    
    try {
      const newData = await fetchBenchmarkData();
      setData(newData);
      setLastUpdated(new Date());
    } catch (err) {
      // AbortError는 무시 (정상적인 취소)
      if (err instanceof Error && err.name !== 'AbortError') {
        setError(err.message);
      }
    } finally {
      setLoading(false);
    }
  }, [fetchBenchmarkData]);

  // 컴포넌트 마운트 시 초기 데이터 로드
  useEffect(() => {
    refetch();
  }, [refetch]);

  // 자동 새로고침 설정
  useEffect(() => {
    if (!autoRefresh || refreshInterval <= 0) {
      return;
    }

    intervalRef.current = setInterval(() => {
      refetch();
    }, refreshInterval);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [autoRefresh, refreshInterval, refetch]);

  // 필터 변경 시 데이터 새로고침
  useEffect(() => {
    if (data !== null) { // 초기 로드가 아닌 경우에만
      refetch();
    }
  }, [modelFilter]); // refetch는 dependency에서 제외 (무한 루프 방지)

  // 컴포넌트 언마운트 시 정리
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);

  return {
    data,
    loading,
    error,
    refetch,
    lastUpdated
  };
};

/**
 * 특정 모델의 성능 트렌드를 조회하는 커스텀 훅
 * 
 * @param modelName - 모델명
 * @param days - 조회 기간 (일)
 * 
 * @returns 성능 트렌드 데이터
 */
export const useModelPerformanceTrend = (modelName: string, days: number = 7) => {
  const [trendData, setTrendData] = useState<BenchmarkMetrics[] | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchTrendData = useCallback(async () => {
    if (!modelName) return;

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`/api/benchmarks/${modelName}/trend?days=${days}`);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch trend data: ${response.status}`);
      }

      const result = await response.json();
      setTrendData(result.data || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error occurred');
    } finally {
      setLoading(false);
    }
  }, [modelName, days]);

  useEffect(() => {
    fetchTrendData();
  }, [fetchTrendData]);

  return {
    trendData,
    loading,
    error,
    refetch: fetchTrendData
  };
};
