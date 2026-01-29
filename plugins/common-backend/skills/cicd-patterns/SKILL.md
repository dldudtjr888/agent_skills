---
name: cicd-patterns
description: |
  CI/CD 패턴 가이드. 파이프라인 설계, 테스트 전략, 배포 전략, 환경 관리.
version: 1.0.0
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

## 관련 에이전트
- `@deployment-advisor` - CI/CD 파이프라인 리뷰
