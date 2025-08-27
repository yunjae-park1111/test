# 2025.08.25 **노드 네트워크 단절로 인한 kubelet 통신 장애 및 NodeNotReady 발생**

### Infrastructure Type

Kubernetes Cluster

### Issue Type

Outage/Downtime

### Severity

Critical - Service down, blocking all users

### Issue Description

노드 `tkai-oks-md-1-193cfbbbb78b-zfz7s-bkqzq`에서 **네트워크 계층 단절**이 발생하여 kubelet과 control-plane 간 통신이 완전히 차단됨. L2(ARP), L3(IP), L4(TCP) 모든 네트워크 계층에서 연결 불가 상태가 확인되었으며, 특히 ARP 테이블에서 해당 노드의 MAC 주소 조회가 실패하여 **물리적/가상 네트워크 인프라 수준의 문제**로 추정됨.

노드 단절 직전 GPU 메모리 사용량이 0%에서 45.5%로 급상승한 것이 확인되어, MIG 파드의 GPU 작업 중 네트워크 스택 또는 하드웨어 레벨 장애가 발생한 것으로 보임. 이로 인해 kubelet heartbeat가 중단되어 노드가 `NodeNotReady` 상태로 전환되었고, 해당 노드의 워크로드가 다른 노드로 재스케줄링되면서 클러스터 전체 리소스 사용률이 급증함.

### Impact Assessment

- 해당 노드에서 실행 중이던 워크로드 전부 중단
- 다른 노드들의 리소스 사용률 급증 (CPU limits 340~601%, Memory limits 149~357%)
- 서비스 지연 및 일부 요청 실패 발생
- GPU 리소스 손실로 인한 ML/AI 워크로드 처리 능력 저하

### Environment Details

- Kubernetes v1.32.6
- CNI: Kube-OVN (Geneve)
- 노드 타입: MIG 지원 GPU 노드 (OpenStack)
- OS: Ubuntu 24.04

### Resource Information

- 장애 노드:
    - tkai-oks-md-1-193cfbbbb78b-zfz7s-bkqzq (node-role: mig)
    - CPU requests: 14%, limits: 69%
    - Memory requests: 7%, limits: 22%
    - 디스크 사용량: 75.7%

- 영향받은 노드들 (리소스 급증):
    - tkai-oks-md-0-193cfbbbb78b-5gblf-85zt7: CPU 88.9%/340.6%, Memory 58.7%/149.8%
    - tkai-oks-md-0-193cfbbbb78b-5gblf-9f79t: CPU 90.5%/381.3%, Memory 57.3%/178.6%
    - tkai-oks-md-0-193cfbbbb78b-5gblf-pkmt5: CPU 93.4%/416.6%, Memory 84.2%/213.3%
    - tkai-oks-md-0-193cfbbbb78b-5gblf-wn4gb: CPU 147.9%/601.3%, Memory 84.1%/357.1%

### Symptoms

- `NodeNotReady` 상태로 전환, kubelet heartbeat 중단
- 모든 네트워크 계층에서 통신 불가 (L2/L3/L4)
- GPU 메모리 사용량 급상승 (0% → 45.5%) 직후 장애 발생
- CCM 로그에 shutoff/stopped 흔적 없음 (정상 종료 아님)

### Timeline

- **2025-08-25 12:58 KST**: 마지막 kubelet heartbeat 확인
- **2025-08-25 13:02 KST**: 노드 단절 감지
- **2025-08-25 13:08 KST**: 노드 축출 처리 (NodeNotReady)
- **2025-08-25 16:32 KST**: 리소스 백엔드 테스트 중 이상현상 발견 및 분석 시작
- **2025-08-25 19:46 KST**: 시스템 복구 완료
- **직전**: GPU 메모리 사용량 0% → 45.5% 급상승 (Grafana 확인)

### Monitoring Data

- 장애 직전 GPU 메모리: 0% → 45.5% (MIG 파드 활동)
- 노드 리소스 사용률: CPU 14%/69%, Memory 7%/22% (정상 범위)
- 디스크 사용량: 75.7%
- 다른 노드들 리소스 급증: CPU limits 340~601% 오버커밋 발생

### Logs and Error Messages

**네트워크 계층별 테스트 결과:**
- **L3 (IP 레벨)**: `ping 10.62.0.30` → `Destination Host Unreachable`
- **L4 (TCP 레벨)**: `nc -vz -w 3 10.62.0.30 10250` → `timeout`
- **L4 (HTTPS)**: `curl https://10.62.0.30:10250/healthz` → 연결 실패
- **L2 (ARP 레벨)**: `ip neigh show 10.62.0.30` → 상태: `FAILED`
- **L2 (ARP)**: `arping -c 3 10.62.0.30` → 응답 없음

**OVN 상태:**
- OVN 게이트웨이 핑: OK (네트워크 인프라 자체는 정상)

### Troubleshooting Steps Taken

1. `kubectl describe node`로 NodeNotReady 상태 확인
2. 네트워크 계층별 연결성 테스트 (L2/L3/L4)
3. ARP 테이블 조회 및 MAC 주소 확인 → FAILED
4. CCM 로그 분석 → shutoff/stopped 흔적 없음
5. GPU 메모리 사용량 변화 패턴 분석 (Grafana)
6. 다른 노드들의 리소스 급증 패턴 확인
7. 노드 축출 처리

### Root Cause Analysis

**현재 상태:**
- **원인 미확정**: 시스템이 왜 다운되고 깨졌는지 정확한 원인은 아직 미상
- **추정 시나리오**: 시스템 자체가 깨져서 네트워크 장애 등 연쇄적 문제가 발생한 것으로 추정

**관찰된 현상:**
1. **시스템 전체 손상**: 노드 시스템 자체가 깨진 상태로 전환
2. **네트워크 스택 완전 장애**: 시스템 손상으로 인해 L2/L3/L4 모든 네트워크 계층 비정상
3. **GPU 작업과의 시간적 연관성**: GPU 메모리 급상승(0% → 45.5%) 직후 시스템 다운 발생

**장애 패턴 분석:**
- **테스트 시 관찰된 네트워크 장애와 동일**: 현재 테스트에서 확인한 네트워크 연결 불가 패턴과 일치
- **시스템 레벨 손상으로 추정**: 단순 서비스 장애가 아닌 시스템 자체의 손상으로 보임
- **복구 후 정상화**: 시스템 복구 조치 후 정상 동작으로 일시적 시스템 손상 확인

**수집된 증거:**
- L2 ARP 실패 → 시스템 손상으로 인한 네트워크 스택 완전 장애
- GPU 메모리 급상승 직후 시스템 다운 → 시간적 상관관계 존재 (인과관계 미확정)
- CCM 로그에 정상 종료 흔적 없음 → 예기치 못한 시스템 손상
- 시스템 복구 후 정상 동작 → 일시적 시스템 손상으로 확인

### Proposed Resolution

**즉시 조치:**
- 장애 노드 재부팅 및 네트워크 인터페이스 재설정
- GPU 드라이버 및 네트워크 드라이버 버전 호환성 점검
- MIG 파드 리소스 제한 강화

**장기 대책:**
- GPU 노드 전용 네트워크 모니터링 강화
- MIG 워크로드에 대한 리소스 제한 및 QoS 정책 수립
- OpenStack 네트워크 인프라 상태 모니터링 추가
- GPU 작업 시 네트워크 안정성 테스트 자동화
- 노드 장애 시 자동 복구 메커니즘 구축

### Recovery Actions

**복구 조치:**
- **2025-08-25 19:46 KST**: 시스템 복구 완료
- 노드 다운으로 인한 시스템 장애로 판단하여 전체 시스템 복구 수행
- 복구 후 정상 동작 확인

### Additional Context

- 이번 장애는 **노드 완전 다운으로 인한 시스템 전반 장애**로 추정되며, 정확한 원인은 추가 조사 필요
- GPU 메모리 급상승과 노드 다운의 시간적 연관성은 확인되었으나 인과관계는 미확정
- L2 레벨 ARP 실패는 노드 자체의 네트워크 스택 완전 장애를 의미
- 노드 장애로 인한 워크로드 재분산이 다른 노드들의 심각한 오버커밋을 야기함
- GPU 리소스의 특성상 노드 손실 시 대체 리소스 확보가 어려워 서비스 영향도가 큼
- 시스템 복구 후 정상 동작으로 일시적 장애였음을 확인

### Checklist

- [x]  I have checked the system status page
- [x]  I have searched existing issues to ensure this hasn't been reported already
- [x]  I have provided accurate severity assessment
- [x]  I have included relevant logs and monitoring data
