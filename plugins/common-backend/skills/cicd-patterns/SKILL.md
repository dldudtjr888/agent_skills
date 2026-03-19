---
name: cicd-patterns
description: |
  CI/CD 파이프라인 전문 가이드 — GitHub Actions/GitLab CI 설계, 매트릭스 테스트, 시크릿 관리, 캐싱 최적화.
  Rust 크레이트의 cargo test/clippy/fmt CI 통합이 핵심 차별점.
  MUST USE when: (1) GitHub Actions 워크플로우 YAML 작성/수정 시, (2) CI 파이프라인 스테이지 설계 시,
  (3) 매트릭스 빌드(다중 OS/버전) 구성 시, (4) Docker 빌드 + 레지스트리 푸시 자동화 시,
  (5) staging→production 자동 배포 파이프라인 설계 시, (6) Rust 프로젝트의 cargo 캐시 최적화 시.
  CI가 느리면 개발 속도가 느려진다 — 캐싱/병렬화 패턴을 이 스킬에서 반드시 확인하라.
version: 1.1.0
category: devops
user-invocable: true
triggers:
  keywords:
    - cicd
    - ci/cd
    - pipeline
    - 파이프라인
    - github actions
    - gitlab ci
    - jenkins
    - continuous integration
    - continuous deployment
  intentPatterns:
    - "(설계|구성).*(파이프라인|CI/CD)"
    - "(자동화).*(테스트|배포)"
---

# CI/CD Patterns Guide

파이프라인 설계와 자동화 배포 패턴.

## Pipeline Stages

```
┌──────┐   ┌──────┐   ┌──────┐   ┌──────┐   ┌──────┐
│ Lint │ → │ Test │ → │Build │ → │Deploy│ → │ E2E  │
│      │   │      │   │      │   │Staging│   │      │
└──────┘   └──────┘   └──────┘   └──────┘   └──────┘
                                      │
                                      ▼
                               ┌──────────┐
                               │  Deploy  │
                               │   Prod   │
                               └──────────┘
```

## GitHub Actions Template

```yaml
name: CI/CD

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Lint
        run: make lint

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Test
        run: make test

  build:
    needs: [lint, test]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build
        run: docker build -t app:${{ github.sha }} .
      - name: Push
        run: docker push app:${{ github.sha }}

  deploy-staging:
    needs: build
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - name: Deploy to staging
        run: kubectl set image deployment/app app=app:${{ github.sha }}

  deploy-prod:
    needs: deploy-staging
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: production
    steps:
      - name: Deploy to production
        run: kubectl set image deployment/app app=app:${{ github.sha }}
```

## Best Practices

### Secrets Management
```yaml
env:
  API_KEY: ${{ secrets.API_KEY }}  # GitHub Secrets
```

### Caching
```yaml
- uses: actions/cache@v3
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}
```

### Matrix Testing
```yaml
strategy:
  matrix:
    python-version: ['3.10', '3.11', '3.12']
    os: [ubuntu-latest, macos-latest]
```

## When NOT to Use

- **로컬 빌드/테스트만** → Makefile이나 스크립트로 충분
- **Kubernetes 배포 설정 심화** → `deployment-patterns` 스킬 사용
- **Docker 이미지 최적화** → `deployment-patterns` 스킬 사용
- **인프라 프로비저닝(Terraform/Pulumi)** → IaC 전용 가이드 참조

## 관련 에이전트
- `@deployment-advisor` - CI/CD 파이프라인 리뷰
