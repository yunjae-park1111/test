import asyncio
from datetime import datetime
import aiohttp
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, DESCENDING
from kubernetes import client, config
from typing import Dict, List, Optional
import logging
from dataclasses import dataclass

@dataclass
class BenchmarkResult:
    model_name: str
    throughput_tokens_per_sec: float
    latency_ms: float
    memory_usage_gb: float
    timestamp: datetime
    github_commit_sha: str

class PerformanceTracker:
    def __init__(self, mongodb_url: str, github_token: str):
        self.mongodb_client = AsyncIOMotorClient(mongodb_url)
        self.db = self.mongodb_client.vllm_benchmark
        self.collection = self.db.benchmark_results
        self.github_token = github_token
        
        # MongoDB 인덱스 최적화
        asyncio.create_task(self._ensure_indexes())
    
    async def _ensure_indexes(self):
        """MongoDB 쿼리 최적화를 위한 인덱스 생성"""
        await self.collection.create_index([
            ("model_name", ASCENDING),
            ("timestamp", DESCENDING)
        ])
        await self.collection.create_index([
            ("github_commit_sha", ASCENDING)
        ])
        await self.collection.create_index([
            ("throughput_tokens_per_sec", DESCENDING)
        ])
    
    async def get_github_commit_info(self, repo: str, commit_sha: str) -> Dict:
        """GitHub API 통합으로 커밋 정보 조회"""
        headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        url = f"https://api.github.com/repos/{repo}/commits/{commit_sha}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"GitHub API error: {response.status}")
    
    async def get_kubernetes_gpu_resources(self) -> Dict:
        """Kubernetes API 호출로 GPU 리소스 현황 확인"""
        try:
            config.load_incluster_config()
        except:
            config.load_kube_config()
        
        v1 = client.CoreV1Api()
        
        nodes = v1.list_node()
        gpu_resources = {}
        
        for node in nodes.items:
            if 'nvidia.com/gpu' in node.status.capacity:
                gpu_resources[node.metadata.name] = {
                    'total_gpus': int(node.status.capacity['nvidia.com/gpu']),
                    'allocatable_gpus': int(node.status.allocatable['nvidia.com/gpu'])
                }
        
        return gpu_resources
    
    async def run_benchmark(self, model_name: str, test_dataset: List[str]) -> BenchmarkResult:
        """
        벤치마크 실행 및 정확성 검증
        
        Args:
            model_name: 테스트할 모델명
            test_dataset: 테스트 데이터셋
            
        Returns:
            BenchmarkResult: 벤치마크 결과
        """
        start_time = datetime.now()
        
        # 더미 벤치마크 로직 (실제로는 vLLM 엔진 사용)
        total_tokens = sum(len(text.split()) for text in test_dataset)
        processing_time_ms = total_tokens * 0.1  # 더미 계산
        
        throughput = total_tokens / (processing_time_ms / 1000)
        latency = processing_time_ms / len(test_dataset)
        memory_usage = 12.5  # 더미 메모리 사용량 (GB)
        
        # 현재 GitHub 커밋 SHA 조회 (실제 환경에서는 환경변수에서)
        github_sha = "abc123def456"
        
        result = BenchmarkResult(
            model_name=model_name,
            throughput_tokens_per_sec=throughput,
            latency_ms=latency,
            memory_usage_gb=memory_usage,
            timestamp=start_time,
            github_commit_sha=github_sha
        )
        
        # MongoDB에 결과 저장 (쿼리 최적화)
        await self.store_benchmark_result(result)
        
        return result
    
    async def store_benchmark_result(self, result: BenchmarkResult):
        """벤치마크 결과를 MongoDB에 저장"""
        document = {
            "model_name": result.model_name,
            "throughput_tokens_per_sec": result.throughput_tokens_per_sec,
            "latency_ms": result.latency_ms,
            "memory_usage_gb": result.memory_usage_gb,
            "timestamp": result.timestamp,
            "github_commit_sha": result.github_commit_sha
        }
        
        await self.collection.insert_one(document)
    
    async def get_performance_history(self, model_name: str, limit: int = 100) -> List[Dict]:
        """모델별 성능 히스토리 조회 (MongoDB 쿼리 최적화)"""
        cursor = self.collection.find(
            {"model_name": model_name}
        ).sort("timestamp", DESCENDING).limit(limit)
        
        return await cursor.to_list(length=limit)

class BenchmarkQueue:
    """비동기 처리 패턴을 위한 큐 관리 로직"""
    
    def __init__(self):
        self.queue = asyncio.Queue()
        self.workers = []
        self.running = False
    
    async def add_benchmark_task(self, model_name: str, test_data: List[str]):
        """벤치마크 태스크를 큐에 추가"""
        await self.queue.put((model_name, test_data))
    
    async def worker(self, worker_id: int, tracker: PerformanceTracker):
        """워커 프로세스: 큐에서 태스크를 가져와 처리"""
        while self.running:
            try:
                model_name, test_data = await asyncio.wait_for(
                    self.queue.get(), timeout=1.0
                )
                
                logging.info(f"Worker {worker_id} processing {model_name}")
                result = await tracker.run_benchmark(model_name, test_data)
                logging.info(f"Worker {worker_id} completed {model_name}: {result.throughput_tokens_per_sec:.2f} tokens/sec")
                
                self.queue.task_done()
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logging.error(f"Worker {worker_id} error: {e}")
    
    async def start_workers(self, num_workers: int, tracker: PerformanceTracker):
        """워커들을 시작"""
        self.running = True
        self.workers = [
            asyncio.create_task(self.worker(i, tracker)) 
            for i in range(num_workers)
        ]
    
    async def stop_workers(self):
        """워커들을 정지"""
        self.running = False
        await asyncio.gather(*self.workers, return_exceptions=True)
