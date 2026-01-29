# Prompt Management

YAML 기반 프롬프트를 관리하고 버전 관리하는 가이드.
버전 관리, A/B 테스트, 변수 치환, 롤백 자동화 전문.

## Core Responsibilities

1. **Version Management** - 프롬프트 버전 관리
2. **Variable Substitution** - 동적 변수 치환
3. **A/B Testing** - 프롬프트 A/B 테스트
4. **Rollback** - 안전한 롤백
5. **Config Loading** - 설정 파일 로드

---

## 프롬프트 YAML 구조

### 기본 구조

```yaml
# prompts/orchestrator/supervisor.yaml
current: v3  # 현재 활성 버전

# 최신 버전
v3: |
  당신은 AI Assistant Supervisor입니다.

  ## 역할
  - 사용자 요청 분석
  - 적절한 전문가에게 라우팅
  - 결과 종합 및 검증

  ## 연결된 전문가
  - Research Specialist: 웹 검색
  - MySQL Assistant: 데이터베이스 쿼리
  - Planning Specialist: 작업 계획

  ## 응답 스타일
  - 마크다운 형식
  - 한국어 공손한 존댓말

# 이전 버전 (롤백용)
v2: |
  당신은 AI Assistant입니다.
  ...

v1: |
  You are an AI Assistant.
  ...
```

### 변수 치환

```yaml
# prompts/agents/mysql.yaml
current: v1

v1: |
  당신은 MySQL 데이터베이스 전문가입니다.

  ## 데이터베이스 정보
  - Host: {db_host}
  - Database: {db_name}
  - 허용된 테이블: {allowed_tables}

  ## 제약 사항
  - SELECT 쿼리만 허용
  - 최대 {max_rows}개 행 반환
  - 민감한 컬럼 마스킹: {masked_columns}
```

### 모델 설정 포함

```yaml
# prompts/agents/research.yaml
current: v1

model_settings:
  model: gpt-4o
  temperature: 0.7
  max_tokens: 2000
  top_p: 0.95

v1: |
  당신은 리서치 전문가입니다.
  ...
```

---

## Prompt Loader 구현

### ConfigLoader 클래스

```python
import yaml
from pathlib import Path
from typing import Optional, Any
from functools import lru_cache

class ConfigLoader:
    """프롬프트 및 설정 로더"""

    def __init__(self, prompts_dir: str = "prompts"):
        self.prompts_dir = Path(prompts_dir)
        self._cache: dict[str, dict] = {}

    def load_prompt(
        self,
        prompt_key: str,
        version: Optional[str] = None,
        variables: Optional[dict[str, str]] = None,
    ) -> str:
        """프롬프트 로드

        Args:
            prompt_key: 프롬프트 키 (예: "orchestrator/supervisor")
            version: 특정 버전 (None이면 current 사용)
            variables: 치환할 변수들

        Returns:
            프롬프트 문자열
        """
        yaml_path = self.prompts_dir / f"{prompt_key}.yaml"
        config = self._load_yaml(yaml_path)

        if version is None:
            version = config.get("current", "v1")

        prompt = config.get(version)
        if prompt is None:
            raise ValueError(f"Version {version} not found in {prompt_key}")

        if variables:
            prompt = self._substitute_variables(prompt, variables)

        return prompt

    def load_model_settings(self, prompt_key: str) -> dict[str, Any]:
        """모델 설정 로드"""
        yaml_path = self.prompts_dir / f"{prompt_key}.yaml"
        config = self._load_yaml(yaml_path)

        return config.get("model_settings", {})

    def list_versions(self, prompt_key: str) -> list[str]:
        """사용 가능한 버전 목록"""
        yaml_path = self.prompts_dir / f"{prompt_key}.yaml"
        config = self._load_yaml(yaml_path)

        versions = [k for k in config.keys() if k.startswith("v") and k[1:].isdigit()]
        return sorted(versions, key=lambda v: int(v[1:]), reverse=True)

    def get_current_version(self, prompt_key: str) -> str:
        """현재 활성 버전"""
        yaml_path = self.prompts_dir / f"{prompt_key}.yaml"
        config = self._load_yaml(yaml_path)
        return config.get("current", "v1")

    def _load_yaml(self, path: Path) -> dict:
        """YAML 파일 로드 (캐싱)"""
        cache_key = str(path)

        if cache_key not in self._cache:
            if not path.exists():
                raise FileNotFoundError(f"Prompt file not found: {path}")

            with open(path) as f:
                self._cache[cache_key] = yaml.safe_load(f)

        return self._cache[cache_key]

    def _substitute_variables(self, prompt: str, variables: dict[str, str]) -> str:
        """변수 치환"""
        for key, value in variables.items():
            prompt = prompt.replace(f"{{{key}}}", str(value))
        return prompt

    def clear_cache(self) -> None:
        """캐시 초기화"""
        self._cache.clear()


# 싱글톤 인스턴스
_config_loader: Optional[ConfigLoader] = None

def get_config_loader(prompts_dir: str = "prompts") -> ConfigLoader:
    """ConfigLoader 싱글톤"""
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigLoader(prompts_dir)
    return _config_loader
```

---

## 버전 관리

### 버전 전환 (롤백/업그레이드)

```python
import yaml

class PromptVersionManager:
    """프롬프트 버전 관리자"""

    def __init__(self, prompts_dir: str = "prompts"):
        self.prompts_dir = Path(prompts_dir)

    def set_version(self, prompt_key: str, version: str) -> None:
        """현재 버전 변경"""
        yaml_path = self.prompts_dir / f"{prompt_key}.yaml"

        with open(yaml_path) as f:
            config = yaml.safe_load(f)

        if version not in config:
            raise ValueError(f"Version {version} not found")

        config["current"] = version

        with open(yaml_path, "w") as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False)

    def rollback(self, prompt_key: str) -> str:
        """이전 버전으로 롤백"""
        yaml_path = self.prompts_dir / f"{prompt_key}.yaml"

        with open(yaml_path) as f:
            config = yaml.safe_load(f)

        current = config.get("current", "v1")
        current_num = int(current[1:])

        if current_num <= 1:
            raise ValueError("Already at oldest version")

        new_version = f"v{current_num - 1}"
        self.set_version(prompt_key, new_version)

        return new_version

    def add_version(self, prompt_key: str, content: str) -> str:
        """새 버전 추가"""
        yaml_path = self.prompts_dir / f"{prompt_key}.yaml"

        with open(yaml_path) as f:
            config = yaml.safe_load(f)

        versions = [k for k in config.keys() if k.startswith("v") and k[1:].isdigit()]
        max_version = max(int(v[1:]) for v in versions) if versions else 0
        new_version = f"v{max_version + 1}"

        config[new_version] = content

        with open(yaml_path, "w") as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False)

        return new_version

    def promote_version(self, prompt_key: str, version: str) -> None:
        """특정 버전을 current로 승격"""
        self.set_version(prompt_key, version)
```

---

## A/B 테스트

### 프롬프트 A/B 테스트 프레임워크

```python
import random
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

@dataclass
class ABTestConfig:
    """A/B 테스트 설정"""
    name: str
    prompt_key: str
    variants: dict[str, float]  # {version: weight}
    start_time: datetime
    end_time: Optional[datetime] = None
    metrics: dict[str, list[float]] = field(default_factory=dict)


class ABTestManager:
    """A/B 테스트 관리자"""

    def __init__(self, config_loader: ConfigLoader):
        self.config_loader = config_loader
        self.active_tests: dict[str, ABTestConfig] = {}

    def start_test(
        self,
        name: str,
        prompt_key: str,
        variants: dict[str, float],
    ) -> None:
        """A/B 테스트 시작

        Args:
            name: 테스트 이름
            prompt_key: 프롬프트 키
            variants: {버전: 가중치} (가중치 합 = 1.0)
        """
        if abs(sum(variants.values()) - 1.0) > 0.01:
            raise ValueError("Variant weights must sum to 1.0")

        self.active_tests[name] = ABTestConfig(
            name=name,
            prompt_key=prompt_key,
            variants=variants,
            start_time=datetime.now(),
            metrics={v: [] for v in variants.keys()},
        )

    def get_variant(self, test_name: str, user_id: str) -> str:
        """사용자에게 할당된 변형 반환

        Args:
            test_name: 테스트 이름
            user_id: 사용자 ID (일관성 유지)

        Returns:
            할당된 버전
        """
        test = self.active_tests.get(test_name)
        if not test:
            raise ValueError(f"Test {test_name} not found")

        # 사용자별 일관된 변형 할당 (해시 기반)
        hash_value = hash(f"{test_name}:{user_id}") % 1000 / 1000

        cumulative = 0.0
        for version, weight in test.variants.items():
            cumulative += weight
            if hash_value < cumulative:
                return version

        return list(test.variants.keys())[-1]

    def get_prompt(
        self,
        test_name: str,
        user_id: str,
        variables: Optional[dict[str, str]] = None,
    ) -> tuple[str, str]:
        """A/B 테스트 프롬프트 반환

        Returns:
            (프롬프트, 할당된 버전)
        """
        test = self.active_tests.get(test_name)
        if not test:
            raise ValueError(f"Test {test_name} not found")

        version = self.get_variant(test_name, user_id)
        prompt = self.config_loader.load_prompt(
            test.prompt_key,
            version=version,
            variables=variables,
        )

        return prompt, version

    def record_metric(
        self,
        test_name: str,
        version: str,
        metric_name: str,
        value: float,
    ) -> None:
        """메트릭 기록"""
        test = self.active_tests.get(test_name)
        if test and version in test.metrics:
            if metric_name not in test.metrics:
                test.metrics[metric_name] = {}
            if version not in test.metrics.get(metric_name, {}):
                test.metrics[metric_name] = test.metrics.get(metric_name, {})
                test.metrics[metric_name][version] = []
            test.metrics[metric_name][version].append(value)

    def get_results(self, test_name: str) -> dict:
        """테스트 결과 조회"""
        test = self.active_tests.get(test_name)
        if not test:
            return {}

        results = {
            "name": test.name,
            "prompt_key": test.prompt_key,
            "variants": test.variants,
            "start_time": test.start_time.isoformat(),
            "metrics": {},
        }

        for metric_name, version_values in test.metrics.items():
            results["metrics"][metric_name] = {}
            for version, values in version_values.items():
                if values:
                    results["metrics"][metric_name][version] = {
                        "count": len(values),
                        "mean": sum(values) / len(values),
                        "min": min(values),
                        "max": max(values),
                    }

        return results
```

---

## 에이전트 통합

### MessageBuilder 패턴

```python
from dataclasses import dataclass
from typing import Optional, Any

@dataclass
class MessageEnvelope:
    """메시지 봉투"""
    system_prompt: str
    user_message: str
    chat_history: list[dict]
    context: Optional[str] = None
    metadata: Optional[dict] = None

    def to_openai_messages(self) -> list[dict]:
        """OpenAI API 형식으로 변환"""
        messages = [{"role": "system", "content": self.system_prompt}]

        if self.context:
            messages.append({
                "role": "system",
                "content": f"Context:\n{self.context}",
            })

        messages.extend(self.chat_history)
        messages.append({"role": "user", "content": self.user_message})

        return messages


class MessageBuilder:
    """메시지 빌더"""

    def __init__(
        self,
        config_loader: ConfigLoader,
        context_assembler=None,
    ):
        self.config_loader = config_loader
        self.context_assembler = context_assembler

    async def build(
        self,
        prompt_key: str,
        user_input: str,
        user_id: str,
        session_id: str,
        variables: Optional[dict[str, str]] = None,
        include_history: bool = True,
        include_context: bool = True,
        prompt_version: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> MessageEnvelope:
        """메시지 봉투 빌드"""

        system_prompt = self.config_loader.load_prompt(
            prompt_key,
            version=prompt_version,
            variables=variables,
        )

        history = []
        context = None

        if self.context_assembler:
            assembled = await self.context_assembler.assemble(
                user_id=user_id,
                session_id=session_id,
                current_input=user_input,
                include_history=include_history,
                include_longterm=include_context,
            )

            history = assembled.get("history", [])

            if assembled.get("relevant_memories"):
                context = "\n".join(
                    m["content"] for m in assembled["relevant_memories"]
                )

        return MessageEnvelope(
            system_prompt=system_prompt,
            user_message=user_input,
            chat_history=history,
            context=context,
            metadata=metadata,
        )
```

---

## 디렉토리 구조

```
prompts/
├── orchestrator/
│   ├── supervisor.yaml
│   ├── plan.yaml
│   └── research.yaml
├── agents/
│   ├── mysql.yaml
│   ├── notechat.yaml
│   └── rag.yaml
├── notechat/
│   └── system.yaml
└── rag/
    └── system.yaml
```

---

## 검증 체크리스트

| 항목 | 확인 |
|------|------|
| 버전 관리 | current + v1, v2, v3... |
| 변수 치환 | {variable} 형식 |
| 캐싱 | YAML 파일 캐싱 |
| 롤백 | 이전 버전 복원 |
| A/B 테스트 | 가중치 기반 분배 |
| 일관성 | user_id 기반 변형 고정 |

**Remember**: `current` 필드로 활성 버전을 지정하고, 이전 버전은 롤백을 위해 보관합니다.
