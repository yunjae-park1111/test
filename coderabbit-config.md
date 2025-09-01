# CodeRabbit 설정 가이드

> **AI Platform Web UI 프로젝트용 CodeRabbit 설정 파일 상세 가이드**
>
> 📄 설정 파일: `.coderabbit.yaml`
> 🔧 대시보드: https://coderabbit.ai/dashboard
> 📚 공식 문서: https://docs.coderabbit.ai/getting-started/configure-coderabbit

---

## 📋 목차

- [전역 기본 설정](#전역-기본-설정)
- [리뷰 관련 설정](#리뷰-관련-설정)
- [자동 코드 개선](#자동-코드-개선)
- [채팅 설정](#채팅-설정)
- [지식 베이스](#지식-베이스)
- [코드 생성](#코드-생성)
- [권장 설정](#권장-설정)

---

## 🌐 전역 기본 설정

### `language`
**기본값**: `'en-US'`

CodeRabbit이 리뷰 코멘트를 작성할 언어를 설정합니다.

```yaml
language: 'ko-KR'  # 한국어로 리뷰 작성
```

**지원 언어**: `en-US`, `ko-KR`, `ja-JP`, `zh-CN` 등

### `tone_instructions`
**기본값**: `""` (빈 문자열)

AI 리뷰어의 톤과 스타일을 커스터마이징할 수 있습니다.

```yaml
tone_instructions: "간결하고 친근하게 작성해주세요. 개선 제안시 구체적인 예시를 포함해주세요."
```

**예시**:
- `"친근하고 격려하는 톤으로 작성"`
- `"전문적이고 간결하게 작성"`
- `"초보자도 이해할 수 있게 설명"`

### `early_access`
**기본값**: `false`

CodeRabbit의 베타/실험적 기능을 활성화합니다.

**⚠️ 주의**: 베타 기능은 안정성이 보장되지 않을 수 있습니다.

### `enable_free_tier`
**기본값**: `true`

무료 플랜 사용자를 위한 기능을 활성화합니다.

---

## 📝 리뷰 관련 설정

### 기본 리뷰 동작

#### `profile`
**기본값**: `'chill'` | **옵션**: `'chill'`, `'assertive'`

리뷰의 상세도와 강도를 설정합니다.

- **`'chill'`**: 일반적인 수준의 피드백
- **`'assertive'`**: 더 상세하고 엄격한 피드백 (nitpicky할 수 있음)

#### `request_changes_workflow`
**기본값**: `false`

활성화하면 CodeRabbit의 모든 코멘트가 해결될 때까지 PR 승인을 차단합니다.

**권장**: 팀 워크플로우에 따라 설정

### PR 요약 및 제목

#### `high_level_summary`
**기본값**: `true`

PR 설명에 변경사항의 고수준 요약을 자동 생성합니다.

#### `high_level_summary_placeholder`
**기본값**: `"@coderabbitai summary"`

PR 설명에서 이 플레이스홀더를 찾아 요약으로 교체합니다.

#### `auto_title_placeholder`
**기본값**: `"@coderabbitai"`

PR 제목에 이 키워드가 있으면 자동으로 제목을 생성합니다.

```yaml
auto_title_instructions: "간결하고 명확한 제목으로 생성해주세요. 형식: [타입] 간단한 설명"
```

### 워크스루 설정

#### `collapse_walkthrough`
**기본값**: `false`

워크스루 코멘트를 접힌 상태로 게시할지 설정합니다.

#### `changed_files_summary`
**기본값**: `true`

워크스루에 변경된 파일들의 요약을 포함합니다.

#### `sequence_diagrams`
**기본값**: `true`

복잡한 코드 변경에 대해 시퀀스 다이어그램을 생성합니다.

### 관련 정보 표시

#### `assess_linked_issues`
**기본값**: `true` → **현재**: `false`

연결된 이슈의 해결도를 평가하고 리뷰에 포함합니다.

**변경 이유**: 노이즈 감소를 위해 비활성화

#### `related_issues` / `related_prs`
**기본값**: `true` → **현재**: `false`

워크스루에 관련 이슈나 PR 링크를 포함합니다.

**변경 이유**: 노이즈 감소를 위해 비활성화

#### `suggested_labels` / `suggested_reviewers`
**기본값**: `true` → **현재**: `false`

PR에 라벨이나 리뷰어를 자동 제안합니다.

**변경 이유**: 팀의 수동 관리 선호

### 파일 필터링

#### `path_filters`
리뷰 대상 파일을 지정합니다.

```yaml
path_filters:
  - "**/*.{js,ts,jsx,tsx}"     # JavaScript/TypeScript
  - "**/*.{py,prisma,sql}"     # Python, 데이터베이스
  - "**/*.{yml,yaml,json,md}"  # 설정 및 문서
  - "!node_modules/**"         # 제외: 의존성
  - "!dist/**"                 # 제외: 빌드 결과물
  - "!coverage/**"             # 제외: 테스트 커버리지
  - "!*.lock"                  # 제외: 락 파일
```

#### `path_instructions`
경로별 맞춤 리뷰 가이드라인을 설정할 수 있습니다.

```yaml
path_instructions:
  - path: "ai-platform-backend/**/*.py"
    instructions: "FastAPI 모범 사례, async/await 패턴, Pydantic 모델 검증, SQLAlchemy ORM 최적화, Kubernetes API 호출 시 에러 핸들링, Kubeflow 파이프라인 통합, Prometheus 메트릭 수집을 중점적으로 검토"
  - path: "vllm-benchmark/**/*.py"
    instructions: "MongoDB 쿼리 최적화, GitHub API 통합, Kubernetes API 호출, 벤치마크 정확성, 큐 관리 로직, 비동기 처리 패턴을 중점적으로 검토"
  - path: "apps/web/**/*.{ts,tsx}"
    instructions: "React 18 모범 사례, TypeScript strict 모드, 9ui 컴포넌트 패턴, TailwindCSS 일관성, Zustand 상태 관리, 성능 최적화를 중점적으로 검토"
  - path: "packages/**/*.{ts,tsx}"
    instructions: "모노레포 패키지 구조, 공유 컴포넌트 재사용성, TypeScript 타입 안전성, API 클라이언트 일관성을 중점적으로 검토"
  - path: "helm/**/*.{yaml,yml}"
    instructions: "Helm 차트 모범 사례, 값 검증, 리소스 제한, 보안 설정, 네임스페이스 격리를 중점적으로 검토"
  - path: "**/k8s/**/*.{yaml,yml}"
    instructions: "Kubernetes 매니페스트 보안성, RBAC 설정, 리소스 요청/제한, 네트워크 정책을 중점적으로 검토"
  - path: "**/Dockerfile*"
    instructions: "Docker 보안 모범 사례, 멀티스테이지 빌드, 이미지 크기 최적화, 취약점 최소화를 중점적으로 검토"
  - path: "**/docker-compose*.{yml,yaml}"
    instructions: "서비스 간 의존성, 네트워크 설정, 볼륨 마운트 보안, 환경 변수 관리를 중점적으로 검토"
  - path: "**/compose.{yml,yaml}"
    instructions: "Compose v2 파일도 동일 기준으로 검토"
```

### 자동 리뷰

#### `auto_review.enabled`
**기본값**: `true`

새 PR이나 커밋 푸시시 자동으로 리뷰를 실행합니다.

#### `auto_review.ignore_title_keywords`
특정 키워드가 PR 제목에 있으면 자동 리뷰를 건너뜁니다.

```yaml
ignore_title_keywords:
  - "WIP"
  - "Draft"
  - "DO NOT REVIEW"
```

#### `auto_review.base_branches`
자동 리뷰 대상 브랜치를 지정합니다.

```yaml
base_branches:
  - "^main$"        # 메인 브랜치
  - "^dev$"         # 개발 브랜치
  - "^epic/#.*$"    # 에픽 브랜치 패턴
  - "^release-v.*$" # 릴리즈 브랜치 패턴
```

---

## 🔧 자동 코드 개선

### `finishing_touches`

CodeRabbit이 PR에 대해 자동으로 코드 개선을 제안하는 기능입니다.

#### `docstrings.enabled`
**기본값**: `true`

함수, 클래스에 대한 문서화 주석을 자동 생성합니다.

#### `unit_tests.enabled`
**기본값**: `true`

새로 추가된 함수에 대한 단위 테스트를 자동 생성합니다.

---

## 💬 채팅 설정

### 리뷰/채팅 톤 지침
리뷰/채팅 톤은 최상위 `tone_instructions`로 설정합니다.

```yaml
tone_instructions: "보안·성능·유지보수성을 중점으로 간결하게 리뷰"
```

### `chat.auto_reply`
**기본값**: `true` → **현재**: `false`

사용자가 `@coderabbitai`로 태그하지 않아도 자동 응답할지 설정합니다.

### 외부 서비스 통합

#### `integrations.jira` / `integrations.linear`
**기본값**: `auto`

이슈 트래킹 도구와의 통합을 설정합니다.

- **`auto`**: 공개 저장소에서는 비활성화, 비공개에서는 활성화
- **`enabled`**: 항상 활성화
- **`disabled`**: 항상 비활성화

---

## 🧠 지식 베이스

### `knowledge_base.web_search`
**기본값**: `true`

웹 검색을 통해 최신 정보나 모범 사례를 참조합니다.

### `knowledge_base.code_guidelines`
**기본값**: `true`

조직의 코딩 표준을 학습하고 적용합니다.

```yaml
code_guidelines:
  filePatterns:
    - "**/.cursorrules"
    - "**/CODING_STANDARDS.md"
    - "**/.eslintrc.*"
```

### 학습 범위 설정

#### `scope` 옵션 (`auto` | `local` | `global`)

- **`local`**: 현재 저장소의 데이터만 사용
- **`global`**: 조직의 모든 저장소 데이터 사용
- **`auto`**: 공개 저장소는 local, 비공개는 global

---

## 🎨 코드 생성

### `code_generation.docstrings`

#### `language`
**기본값**: `'en-US'`

문서화 주석을 생성할 언어를 설정합니다.

#### `path_instructions`
경로별 문서화 스타일을 지정할 수 있습니다.

```yaml
docstrings:
  path_instructions:
    - path: "ai-platform-backend/**/*.py"
      instructions: "FastAPI 엔드포인트는 OpenAPI 스키마에 맞는 상세한 독스트링 작성. 쿠버네티스 리소스 조작 함수는 에러 케이스와 권한 요구사항 명시. Kubeflow 파이프라인 함수는 워크플로우 단계와 의존성 기술. Prometheus 메트릭 함수는 수집 주기와 라벨 정보 포함"
    - path: "vllm-benchmark/**/*.py"
      instructions: "벤치마크 함수는 입력 파라미터, 측정 메트릭, 반환값 형식을 명확히 기술. MongoDB 연동 함수는 쿼리 패턴과 인덱싱 정보 포함. Kubernetes API 호출 함수는 리소스 타입과 에러 처리 방법 명시. FastAPI 엔드포인트는 요청/응답 스키마 문서화"
    - path: "apps/web/**/*.{ts,tsx}"
      instructions: "React 18 컴포넌트는 props, 상태, 이벤트 핸들러에 대한 TSDoc 작성. 커스텀 훅은 사용법과 의존성 명시. 9ui 컴포넌트는 variant와 size props 문서화. Vitest 테스트 함수는 테스트 목적과 시나리오 명시"
    - path: "packages/**/*.{ts,tsx}"
      instructions: "공유 패키지는 API 인터페이스와 사용 예시를 포함한 상세 문서화. 타입 정의는 제네릭 사용법과 제약사항 명시. UI 컴포넌트는 props와 사용법, API 클라이언트는 엔드포인트별 호출 방법과 에러 케이스 문서화"
```

### `code_generation.unit_tests`

단위 테스트 생성에 대한 경로별 지침을 설정합니다.

```yaml
unit_tests:
  path_instructions:
    - path: "ai-platform-backend/**/*.py"
      instructions: "FastAPI 엔드포인트는 pytest + httpx로 integration test 생성. 쿠버네티스 API 호출은 mock 사용하여 unit test 작성. Kubeflow 파이프라인은 mock 워크플로우로 테스트. Prometheus 메트릭은 test collector로 검증"
    - path: "vllm-benchmark/**/*.py"
      instructions: "벤치마크 함수는 입력 파라미터와 예외 상황에 대한 기본 pytest 테스트 생성. MongoDB 연동과 Kubernetes API 호출은 mock 사용. 아직 테스트 인프라가 구축되지 않았으므로 기본적인 unit test 패턴 제안"
    - path: "apps/web/**/*.{ts,tsx}"
      instructions: "React 18 컴포넌트는 Vitest + React Testing Library로 render/interaction 테스트 생성. 커스텀 훅은 renderHook 사용. API 호출은 vi.fn()으로 fetch mock, 모듈은 vi.mock() 사용"
    - path: "packages/**/*.{ts,tsx}"
      instructions: "기본적인 Vitest + React Testing Library 테스트 구조 제안. 공유 컴포넌트는 props 검증과 렌더링 테스트, API 클라이언트는 기본 호출과 에러 처리 테스트 패턴 제안"
```

---

## 🎯 권장 설정

### 팀 협업 최적화

```yaml
reviews:
  profile: 'chill'                    # 과도한 nitpicking 방지
  assess_linked_issues: false         # 노이즈 감소
  related_issues: false               # 노이즈 감소
  related_prs: false                  # 노이즈 감소
  suggested_labels: false             # 수동 라벨 관리 선호
  suggested_reviewers: false          # 수동 리뷰어 할당 선호
  poem: false                         # 업무용 PR에서 불필요
```

### 한국어 환경 최적화

```yaml
language: 'ko-KR'  # 기본값: 'en-US' — 한국어 고정 시 명시 설정
tone_instructions: "간결하고 명확하게 설명해주세요."
code_generation.docstrings.language: 'ko-KR'  # 기본값: 'en-US'
```

### 프로젝트별 맞춤 설정

```yaml
reviews:
  path_filters:
    - "**/*.{js,ts,jsx,tsx}"          # 프론트엔드
    - "**/*.{py,prisma,sql}"          # 백엔드
    - "!**/dist/**"                   # 빌드 제외
    - "!**/*.min.*"                   # 압축 파일 제외

  auto_review:
    base_branches:                    # Git Flow 지원 (정규식)
      - "^main$"
      - "^dev$"
      - "^epic/#.*$"
      - "^release-v.*$"
```

---

## 🔍 문제 해결

### 자주 묻는 질문

**Q: 리뷰가 너무 상세해요**
- `profile: 'chill'`로 설정
- `tone_instructions`로 톤 조절

**Q: 한국어 리뷰가 이상해요**
- 기본값은 en-US입니다. 한국어 리뷰를 원하면 `language: 'ko-KR'`를 명시하세요.
- `tone_instructions`에 구체적인 한국어 지침 추가

**Q: 특정 파일을 제외하고 싶어요**
- `path_filters`에 `!pattern` 추가

**Q: 자동 리뷰가 안 돼요**
- `auto_review.enabled: true` 확인
- `base_branches` 설정 확인
- `ignore_title_keywords` 확인

---

## 📞 지원

- **CodeRabbit 대시보드**: https://coderabbit.ai/dashboard
- **공식 문서**: https://docs.coderabbit.ai
- **Discord 커뮤니티**: https://discord.gg/coderabbit

---

*문서 최종 업데이트: 2025-08-28*
