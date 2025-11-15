# Arandu Roadmap

## Visão Geral

**Arandu CoReview Studio** evolui de um foco inicial em reprodutibilidade pesada (execução completa) para um modelo **Review-first** que prioriza revisão rápida e transparente antes de execução pesada.

## Fases

### ✅ v0.0 - Foundation (Sprint 0)
- Project setup, infrastructure básica
- Database models, API skeleton
- Worker framework
- Container hardening, E2E tests, structured logging

### ✅ v0.1 - Execution Pipeline (Sprint 1)
- Repo cloning, environment detection
- Docker execution, report generation
- Notebook templates, error handling

### ✅ v0.1.2 - Hardening & Observability (Sprint 1.2)
- Container security (non-root, resource limits, network isolation)
- E2E integration tests
- Structured JSON logging

### 🚧 v0.2 - Review MVP (Sprint 2) - **EM ANDAMENTO**
**Foco:** Review-first com claims, citações, checklist, Quality Score, badges

**Entregas:**
- API `/api/v1/reviews` (POST/GET/Artifacts/Badges)
- Claim extraction (PDF/HTML parsing)
- Citation suggester (RAG híbrido)
- Method checklist (heurísticas)
- Quality Score + SHAP (0-100)
- Report HTML + JSON
- UI Next.js (submit, status, editor)
- Badges (Claim-mapped, Method-check, Citations-augmented)
- Telemetria básica

**Timeline:** 2 semanas

### 🔮 v0.3 - Review Enhancement (Futuro)
- Score-Narrator Agent (narrativa executiva + técnica)
- Repro Lite opcional (smoke-run)
- Editor colaborativo multi-revisor
- Versionamento de reviews

### 🔮 v0.4 - Quality Score ML (Futuro)
- Modelo LightGBM treinado com dataset semente
- Re-treinamento automático
- Monitoramento de drift

### 🔮 v1.0 - Production Ready (Futuro)
- Autenticação de usuários
- API pública
- Dashboard de métricas
- Colaboração avançada

## Princípios

1. **Review-first**: Revisão rápida antes de execução pesada
2. **Transparência**: Artefatos padrão (HTML, JSON, badges)
3. **Explicabilidade**: Quality Score com SHAP e narrativa
4. **Reusabilidade**: Claims, citações, checklist estruturados

