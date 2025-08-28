from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import asyncio
import logging
from kubernetes import client, config
from prometheus_client import Counter, Histogram

router = APIRouter()

# Prometheus 메트릭
pipeline_runs_total = Counter('kubeflow_pipeline_runs_total', 'Total pipeline runs')
pipeline_duration = Histogram('kubeflow_pipeline_duration_seconds', 'Pipeline execution time')

class PipelineRequest(BaseModel):
    pipeline_name: str
    parameters: dict
    namespace: str = "kubeflow"

class PipelineResponse(BaseModel):
    pipeline_id: str
    status: str
    message: str

async def get_k8s_client():
    try:
        config.load_incluster_config()
    except:
        config.load_kube_config()
    return client.CustomObjectsApi()

@router.post("/pipelines/run", response_model=PipelineResponse)
async def run_pipeline(
    request: PipelineRequest,
    k8s_client = Depends(get_k8s_client)
):
    """
    Kubeflow 파이프라인을 실행합니다.
    
    Args:
        request: 파이프라인 실행 요청 정보
        k8s_client: Kubernetes API 클라이언트
        
    Returns:
        PipelineResponse: 파이프라인 실행 결과
        
    Raises:
        HTTPException: Kubernetes API 호출 실패 시
    """
    try:
        # Prometheus 메트릭 증가
        pipeline_runs_total.inc()
        
        # Kubeflow 파이프라인 실행 (실제로는 KFP SDK 사용)
        pipeline_manifest = {
            "apiVersion": "argoproj.io/v1alpha1",
            "kind": "Workflow", 
            "metadata": {
                "name": f"{request.pipeline_name}-{asyncio.get_event_loop().time()}",
                "namespace": request.namespace
            },
            "spec": {
                "entrypoint": request.pipeline_name,
                "arguments": {
                    "parameters": [
                        {"name": k, "value": str(v)} 
                        for k, v in request.parameters.items()
                    ]
                }
            }
        }
        
        # Kubernetes API로 워크플로우 생성
        result = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: k8s_client.create_namespaced_custom_object(
                group="argoproj.io",
                version="v1alpha1", 
                namespace=request.namespace,
                plural="workflows",
                body=pipeline_manifest
            )
        )
        
        return PipelineResponse(
            pipeline_id=result["metadata"]["name"],
            status="running",
            message="Pipeline started successfully"
        )
        
    except Exception as e:
        logging.error(f"Pipeline execution failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to run pipeline: {str(e)}"
        )

@router.get("/pipelines/{pipeline_id}/status")
async def get_pipeline_status(pipeline_id: str, k8s_client = Depends(get_k8s_client)):
    # 실제로는 워크플로우 상태를 확인
    # 현재는 더미 응답
    return {"pipeline_id": pipeline_id, "status": "completed"}
