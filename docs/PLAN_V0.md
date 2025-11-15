# Arandu CoReview Studio v0.2 – Execution Plan

## 1. MVP Summary

**Arandu CoReview Studio** (V1) é um serviço que ajuda na **revisão científica rápida, transparente e reusável**, com foco em **Review-first** (L0/L1) antes de "repro pesada".

**Módulo principal:** Review MVP com extração de claims, sugestões de citação (RAG), checklist metodológico, **Quality Score explicável** (0-100) com SHAP e **Score-Narrator Agent**, e artefatos padrão (relatório HTML, JSON, badges).

**Módulo secundário:** Repro Lite (L0/L1) - smoke-run CPU-only opcional para validação básica.

**Single hero flow:**
1. Usuário submete URL/DOI ou PDF (+ opcional repo GitHub)
2. Sistema extrai claims por seção (intro/method/results/discussion)
3. Sistema sugere citações por claim (RAG híbrido + rerank)
4. Sistema gera checklist metodológico (dados, seeds, métricas, ablações, comparativos, licença)
5. Sistema executa Repro Lite opcional (smoke-run em toy data/seed fixo)
6. Sistema calcula **Quality Score** (0-100) com features de paper/repo/traces/checklist/citações
7. Sistema gera explicações **SHAP** (top-k contribuições) e **Score-Narrator** (narrativa executiva + técnica)
8. Sistema gera artefatos: HTML report, JSON (claims→cites, checklist, score, SHAP), badges (Claim-mapped, Citations-augmented, Method-check, Score-tier)
9. Revisor edita/aceita/recusa sugestões via editor inline
10. Revisor publica versão e compartilha (snippet README, link público)

**Primary users:** Autores de papers científicos, revisores, editores

---

## 2. Nomes, Visão e Valor

**Nome do produto:** *Arandu CoReview Studio* (V1), com módulo *Repro Lite* (L0/L1).

**Visão:** Tornar a revisão científica **rápida, transparente e reusável**, com **artefatos padrão** (relatório, JSON, badges) e um **score de qualidade explicável**.

**Valor ao usuário (autor/revisor):**
- Mapeamento de *claims* estruturado
- Sugestões de citação contextualizadas por claim
- Checklist de método automatizado
- Verificação leve (L1) via Repro Lite
- **Score de qualidade** (0-100) com **explicação clara** (SHAP + narrativa)
- Badges integráveis ao README

---

## 3. Jornada do Usuário (Detalhada)

### Fluxo "Review MVP"

1. **Submit Review**: Usuário informa **URL/DOI** ou envia **PDF** (+ opcional repo GitHub)
2. **Parsing & Claims**: Extrair *claims* por seção (intro/method/results/discussion), com *spans*
3. **Auto-Cites (RAG)**: Sugerir referências (CrossRef/arXiv + índice local) por *claim* (top-k + score)
4. **Method Checklist**: Gerar checklist (dados, seeds, métricas, ablações, comparativos, licença)
5. **Repro Lite (opcional)**: Smoke-run CPU-only em toy data/seed fixo; coleta de traces
6. **Quality Score**: Predição 0–100 com features de paper/repo/traces; **SHAP** local
7. **Score-Narrator**: Agente explica o score (executivo + técnico), com evidências ancoradas
8. **Artefatos**: HTML report, JSON (claims→cites, checklist, score, SHAP), **badges** (Claim-mapped, Citations-augmented, Method-check, Score-tier)
9. **Editor**: Revisor aceita/edita/recusa sugestões; publica versão
10. **Share**: Snippet README, link público do review; métricas registradas

---

## 4. Arquitetura v0.2 (High-Level)

### Componentes

```
┌─────────────────────────────────────────┐
│   Web UI (Next.js + Tailwind)           │
│   - /review/submit                       │
│   - /review/[id] (editor inline)        │
│   - /review/[id]/artifacts               │
└──────┬──────────────────────────────────┘
       │ HTTP
┌──────▼──────────────────────────────────┐
│      API Service (FastAPI)               │
│  - POST /reviews                         │
│  - GET /reviews/{id}                     │
│  - GET /reviews/{id}/artifacts/{type}    │
│  - POST /reviews/{id}/editor             │
│  - GET /badges/{id}/{type}.svg           │
│  - GET /reviews/{id}/score               │
└──────┬──────────────────────────────────┘
       │
       ├──► LangGraph Agent Pipeline
       │    (Ingestion → Claims → Cites → 
       │     Checklist → Repro Lite → 
       │     Features → Score → SHAP → 
       │     Narrator → Report)
       │
       ├──► RAG Service (Híbrido)
       │    (FAISS + BM25 + Re-rank)
       │
       ├──► Quality Score Service (ML)
       │    (LightGBM + Calibração)
       │
       ├──► SHAP Explainer
       │
       └──► Database (PostgreSQL)
              │
              └──► Review, Claim, Checklist, 
                   QualityScore, Artifact tables
```

### Technologies

- **Backend:** FastAPI (Python 3.11+)
- **Agents:** LangGraph
- **RAG:** FAISS (HNSW), BM25 (tantivy/whoosh), Cross-encoder (bge-reranker-large)
- **ML:** LightGBM + Isotonic Calibration, SHAP
- **LLM:** GPT-4/Claude (via API)
- **Database:** PostgreSQL
- **Task Queue:** Redis + RQ
- **Frontend:** Next.js (TypeScript) + Tailwind CSS
- **Storage:** Local filesystem para artefatos

---

## 5. Sprints

### Sprint 0 – Foundation (COMPLETO)
**Status:** ✅ Concluído
- Project setup, basic infrastructure, core data models, minimal API
- Docker/docker-compose, database models, worker skeleton
- Container hardening, E2E tests, structured logging

### Sprint 1 – Execution Pipeline (COMPLETO)
**Status:** ✅ Concluído
- Repo cloning, environment detection, Docker execution
- Report generation, notebook templates
- Error handling, status transitions

### Sprint 1.2 – Hardening & Observability (COMPLETO)
**Status:** ✅ Concluído
- Container security (non-root, resource limits, network isolation)
- E2E integration tests
- Structured JSON logging

### Sprint 2 – Review MVP Core (v0.2) - **EM ANDAMENTO**

**Goal:** Entregar Review MVP funcional com claims, citações, checklist, Quality Score, SHAP e narrativa.

**Definition of Done:**
- [ ] Ingestion Agent (PDF/URL parsing, metadata extraction)
- [ ] Claim Extractor (LLM + heurísticas, segmentação por seção)
- [ ] Citation Suggester (RAG híbrido + rerank)
- [ ] Checklist Agent (regras + LLM)
- [ ] Feature Builder (agregação de features)
- [ ] Quality Predictor (serviço ML com modelo inicial)
- [ ] SHAP Explainer (explicações locais)
- [ ] Score-Narrator Agent (narrativa executiva + técnica)
- [ ] Report Builder (HTML + JSON + badges)
- [ ] UI básica (/review/submit, /review/[id])
- [ ] Editor inline (aceitar/editar/recusar sugestões)
- [ ] 3 reviews publicados com artefatos completos

**Issues:** Ver seção "Backlog as GitHub Issues" abaixo.

### Sprint 2.1 – Hosting Foundation (v0.2.1) - **KICKOFF**

**Goal:** Fundação para hosting nativo de papers com AID+versionamento, storage por versão, endpoints de ingest, streaming de PDF, geração de thumbnails e páginas hospedadas.

**Definition of Done:**
- [ ] Sistema AID (Arandu ID) + versionamento implementado
- [ ] Storage por versão (`/papers/{aid}/v{version}/`)
- [ ] Endpoints de ingest (`POST /papers`, `POST /papers/{aid}/versions`)
- [ ] Streaming de PDF (`GET /papers/{aid}/v{version}/pdf`)
- [ ] Job de geração de thumbnails
- [ ] Páginas `/p/[aid]` e `/p/[aid]/viewer` com tabs e ScoreCard
- [ ] Alias `/papers/[id]` => `/p/[aid]`
- [ ] Migrações para `papers`, `quality_scores`, `claims`, `claim_links`
- [ ] Testes E2E de hosted page
- [ ] Docs curtas (hosted-papers.md, quality-score-v0.md, claims-and-refs-v0.md)

**Issues:** #34, #35, #36 (ver abaixo)

---

## 6. Backlog Overview

### Epic 1: Foundation & Infrastructure (Sprint 0) - ✅ COMPLETO
- Project setup and tooling
- Database models and migrations
- Basic API endpoints
- Worker framework
- Container hardening
- E2E tests
- Structured logging

### Epic 2: Execution Pipeline (Sprint 1) - ✅ COMPLETO
- Repo cloning
- Environment detection
- Docker execution
- Report generation

### Epic 3: Review MVP Core (Sprint 2) - **EM ANDAMENTO**

#### 3.1 Ingestion & Claims
- PDF/URL parsing
- Metadata extraction
- Claim extraction (LLM + heurísticas)
- Section segmentation

#### 3.2 RAG & Citations
- RAG híbrido (FAISS + BM25)
- Re-ranking (cross-encoder)
- Citation suggestion por claim
- Deduplication & diversification

#### 3.3 Checklist & Repro Lite
- Checklist generation (regras + LLM)
- Repro Lite runner (smoke-run opcional)
- Trace collection

#### 3.4 Quality Score & Explicabilidade
- Feature builder
- Quality predictor (ML)
- SHAP explainer
- Score-Narrator Agent

#### 3.5 Artefatos & UI
- Report HTML v2 (score/SHAP/narrativa)
- Review JSON
- Badges (Claim-mapped, Citations-augmented, Method-check, Score-tier)
- UI pages (submit, editor, artifacts)
- Editor inline (accept/edit/reject)

### Epic 4: Polish & Reliability (Post-MVP)
- Better error handling
- Performance optimization
- Monitoring/metrics dashboard
- User documentation

---

## 7. Backlog as GitHub Issues

### MUST-HAVE (Sprint 2 - Review MVP)

**Issue #40: Ingestion Agent - PDF/URL parsing e metadata extraction**
- **Labels:** `backend`, `agents`, `must-have`, `sprint-2`
- **Description:** Implementar agente que baixa PDF/HTML, faz cleaning, extrai metadados (title, authors, venue, year). Suportar URL/DOI e PDF base64.
- **Acceptance:** Pode processar PDF e URL, extrai metadados corretamente, armazena pdf_ptr.

**Issue #41: Claim Extractor Agent - Extração de claims por seção**
- **Labels:** `backend`, `agents`, `llm`, `must-have`, `sprint-2`
- **Description:** Implementar agente que segmenta claims por seção (intro/method/results/discussion) usando LLM + heurísticas. Gerar spans (posições no texto).
- **Acceptance:** Extrai claims estruturados, associa a seções corretas, gera spans válidos.

**Issue #42: RAG Pipeline - Busca híbrida e rerank**
- **Labels:** `backend`, `rag`, `must-have`, `sprint-2`
- **Description:** Implementar pipeline RAG híbrido: embeddings (e5-base), BM25 (tantivy/whoosh), late fusion, re-ranking (bge-reranker-large). Integrar com CrossRef/arXiv APIs.
- **Acceptance:** Busca retorna top-k citações relevantes por claim, scores calculados, dedup funciona.

**Issue #43: Citation Suggester Agent - Integração RAG por claim**
- **Labels:** `backend`, `agents`, `rag`, `must-have`, `sprint-2`
- **Description:** Integrar RAG pipeline com Claim Extractor. Sugerir citações por claim com scores e justificativas.
- **Acceptance:** Cada claim recebe sugestões de citação, scores e justificativas são retornados.

**Issue #44: Checklist Agent - Geração de checklist metodológico**
- **Labels:** `backend`, `agents`, `llm`, `must-have`, `sprint-2`
- **Description:** Implementar agente que gera checklist (dados, seeds, métricas, ablações, comparativos, licença) usando regras determinísticas + LLM para rationale.
- **Acceptance:** Checklist gerado com itens OK/Missing/Suspect, rationale preenchido.

**Issue #45: Repro Lite Runner - Smoke-run opcional**
- **Labels:** `backend`, `worker`, `docker`, `must-have`, `sprint-2`
- **Description:** Implementar smoke-run CPU-only em toy data/seed fixo. Coletar traces (exit_code, duration, logs, env_fingerprint). Reusar executor do Arandu Repro v0.
- **Acceptance:** Smoke-run executa quando repo disponível, traces coletados, fingerprint gerado.

**Issue #46: Feature Builder - Agregação de features para Quality Score**
- **Labels:** `backend`, `ml`, `must-have`, `sprint-2`
- **Description:** Implementar builder que agrega features de paper/repo/traces/checklist/citações para o modelo de qualidade.
- **Acceptance:** Features extraídas corretamente, schema versionado, validação de tipos.

**Issue #47: Quality Predictor Service - Serviço ML com modelo inicial**
- **Labels:** `backend`, `ml`, `must-have`, `sprint-2`
- **Description:** Implementar serviço que carrega modelo LightGBM treinado, retorna score (0-100) e tier (A/B/C/D). Modelo inicial pode ser heurístico calibrado.
- **Acceptance:** Serviço retorna score e tier, modelo versionado, latência <500ms.

**Issue #48: SHAP Explainer - Explicações locais**
- **Labels:** `backend`, `ml`, `shap`, `must-have`, `sprint-2`
- **Description:** Implementar adapter SHAP que computa contribuições locais (top-k) para instância. Mapear features → evidências.
- **Acceptance:** SHAP explicações geradas, top-k features identificadas, evidências ancoradas.

**Issue #49: Score-Narrator Agent - Narrativa executiva + técnica**
- **Labels:** `backend`, `agents`, `llm`, `must-have`, `sprint-2`
- **Description:** Implementar agente que lê score, SHAP, features, paper/repo e argumenta (executivo+técnico) com business sense. Ancora evidências (claim_id, linha README, item checklist).
- **Acceptance:** Narrativa gerada com seções executiva e técnica, evidências ancoradas, sem julgamentos ad hominem.

**Issue #50: Report Builder v2 - HTML com score/SHAP/narrativa**
- **Labels:** `backend`, `worker`, `must-have`, `sprint-2`
- **Description:** Atualizar report generator para incluir score, tier, SHAP barplot, narrativa do Score-Narrator. Manter compatibilidade com formato v1.
- **Acceptance:** HTML report inclui todas as novas seções, formato válido, visualmente claro.

**Issue #51: Review JSON Schema - Estrutura completa**
- **Labels:** `backend`, `api`, `must-have`, `sprint-2`
- **Description:** Definir e implementar schema JSON completo para review (claims→cites, checklist, traces, features, score, SHAP).
- **Acceptance:** JSON schema válido, inclui todos os campos, documentado.

**Issue #52: Badge Generator - Badges Claim-mapped, Citations-augmented, Method-check, Score-tier**
- **Labels:** `backend`, `worker`, `must-have`, `sprint-2`
- **Description:** Implementar gerador de badges SVG: Claim-mapped, Citations-augmented, Method-check, Score-tier (A/B/C/D).
- **Acceptance:** Badges gerados em SVG, visualmente claros, snippet markdown/HTML disponível.

**Issue #53: UI - Página /review/submit**
- **Labels:** `frontend`, `ui`, `must-have`, `sprint-2`
- **Description:** Implementar formulário para submissão de review (URL/DOI/PDF, repo opcional). Validação e feedback visual.
- **Acceptance:** Formulário funcional, validação funciona, redireciona para /review/[id].

**Issue #54: UI - Página /review/[id] com editor inline**
- **Labels:** `frontend`, `ui`, `must-have`, `sprint-2`
- **Description:** Implementar página com tabs (Claims, Checklist, Score, Artifacts). Editor inline para aceitar/editar/recusar sugestões. ScorePanel e NarrationDrawer.
- **Acceptance:** Página funcional, editor inline funciona, tabs navegáveis, ScorePanel e NarrationDrawer implementados.

**Issue #55: UI - Página /review/[id]/artifacts**
- **Labels:** `frontend`, `ui`, `must-have`, `sprint-2`
- **Description:** Implementar página de download de artefatos (report.html, review.json, badges). BadgeTile component com preview e copiar snippet.
- **Acceptance:** Downloads funcionam, BadgeTile implementado, copiar snippet funciona.

**Issue #56: API - Rotas POST /reviews, GET /reviews/{id}, GET /reviews/{id}/artifacts/{type}**
- **Labels:** `backend`, `api`, `must-have`, `sprint-2`
- **Description:** Implementar rotas principais para criação, consulta e download de artefatos de reviews.
- **Acceptance:** Rotas funcionam, validação de input, retornos corretos.

**Issue #57: API - Rota POST /reviews/{id}/editor**
- **Labels:** `backend`, `api`, `must-have`, `sprint-2`
- **Description:** Implementar rota para aceitar/editar/recusar sugestões. Incrementar versão do review.
- **Acceptance:** Operações funcionam, versão incrementa, estado persistido.

**Issue #58: API - Rotas GET /badges/{id}/{type}.svg, GET /reviews/{id}/score**
- **Labels:** `backend`, `api`, `must-have`, `sprint-2`
- **Description:** Implementar rotas para badges (image endpoint cacheable) e score (score, tier, shap_top_features, rationale).
- **Acceptance:** Badges servidos como SVG, score endpoint retorna dados completos.

**Issue #59: Database Models - Review, Claim, Checklist, QualityScore, Artifacts**
- **Labels:** `backend`, `database`, `must-have`, `sprint-2`
- **Description:** Definir modelos SQLAlchemy para novas entidades: Review, Claim, Checklist, QualityScore, Artifacts. Migrations Alembic.
- **Acceptance:** Modelos definidos, migrations criadas, relacionamentos corretos.

**Issue #60: LangGraph Pipeline - Integração de agentes**
- **Labels:** `backend`, `agents`, `langgraph`, `must-have`, `sprint-2`
- **Description:** Implementar pipeline LangGraph integrando todos os agentes (Ingestion → Claims → Cites → Checklist → Repro Lite → Features → Score → SHAP → Narrator → Report).
- **Acceptance:** Pipeline executa end-to-end, error handling funciona, state management correto.

**Issue #61: Testes de Integração - 3 "Hello Papers" end-to-end**
- **Labels:** `backend`, `testing`, `must-have`, `sprint-2`
- **Description:** Criar 3 papers de referência e testar pipeline completo: submissão → claims → citações → checklist → score → artefatos.
- **Acceptance:** 3 testes end-to-end passando, artefatos válidos, score calculado.

### Sprint 2.1 - Hosting Foundation

**Issue #34: AID+Versionamento e Storage por Versão**
- **Labels:** `backend`, `database`, `storage`, `must-have`, `sprint-2.1`
- **Description:** Implementar sistema AID (Arandu ID) único por paper, versionamento (v1, v2, ...), storage por versão em `PAPERS_BASE/{aid}/v{version}/`. Migrações para tabelas `papers` (id, aid, current_version, title, arxiv_id, repo_url, pdf_path, approved_public, created_at) e `paper_versions` (id, paper_id FK, version, pdf_path, thumbnail_path, created_at).
- **Acceptance:** AID gerado automaticamente, versões incrementam, storage organizado por versão, migrações aplicadas.

**Issue #35: APIs de Ingest e Streaming de PDF**
- **Labels:** `backend`, `api`, `must-have`, `sprint-2.1`
- **Description:** Implementar `POST /papers` (metadata + upload/link PDF), `POST /papers/{aid}/versions` (nova versão), `GET /papers/{aid}` (dados completos), `GET /papers/{aid}/v{version}/pdf` (streaming), `PATCH /papers/{aid}/visibility` (aprovação). Job de thumbnail generation via RQ.
- **Acceptance:** Upload funciona, streaming de PDF eficiente, thumbnails gerados, aprovação persiste.

**Issue #36: UI Hosted Pages e Alias**
- **Labels:** `frontend`, `ui`, `must-have`, `sprint-2.1`
- **Description:** Implementar `/p/[aid]` (página principal com ScoreCard, tabs Overview/Claims/Score/Viewer), `/p/[aid]/viewer` (PDF viewer com tabs), alias `/papers/[id]` => `/p/[aid]`. Componentes: PDFViewer (pdf.js), ScoreCard, tabs, badge interno.
- **Acceptance:** Páginas renderizam corretamente, PDF viewer funcional, tabs navegáveis, alias funciona, badge interno visível.

### NICE-TO-HAVE (Post-MVP)

**Issue #62: Dataset semente para Quality Score (50-200 papers)**
- **Labels:** `ml`, `data`, `nice-to-have`
- **Description:** Coletar e anotar dataset de 50-200 papers com avaliação manual para treinar modelo inicial de Quality Score.
- **Acceptance:** Dataset disponível, labels consistentes, documentado.

**Issue #63: Treinamento inicial do modelo Quality Score**
- **Labels:** `ml`, `nice-to-have`
- **Description:** Treinar modelo LightGBM com dataset semente, calibrar com isotonic calibration, validar com k-fold.
- **Acceptance:** Modelo treinado, métricas aceitáveis (MAE<5, Brier<0.1), versionado.

**Issue #64: Dashboard de métricas**
- **Labels:** `infrastructure`, `nice-to-have`
- **Description:** Implementar dashboard básico para visualizar KPIs (aquisição, valor, custo, qualidade).
- **Acceptance:** Dashboard funcional, métricas atualizadas, visualizações claras.

---

## 8. Risks & Simplifications

### Technical Risks

1. **LLM API costs and latency**
   - Risk: Custos altos, latência elevada
   - Mitigation: Cache de respostas, modelos menores quando possível, rate limiting

2. **RAG pipeline complexity**
   - Risk: Latência alta, qualidade de citações
   - Mitigation: Cache de embeddings, otimização de índices, fallback para busca simples

3. **Quality Score model accuracy**
   - Risk: Score não correlaciona com avaliação humana
   - Mitigation: Dataset semente cuidadoso, validação contínua, calibração

4. **SHAP explanations stability**
   - Risk: Explicações variam entre runs similares
   - Mitigation: Seed fixo, validação de estabilidade, documentação de limitações

5. **PDF parsing accuracy**
   - Risk: Extração de texto/metadados falha
   - Mitigation: Múltiplos parsers (fallback), validação manual quando necessário

### Simplifications for v0.2

1. **Modelo Quality Score inicial heurístico**: Começar com regras calibradas, evoluir para ML
2. **RAG com corpus limitado**: Começar com CrossRef/arXiv, expandir depois
3. **Repro Lite opcional**: Não bloquear review se Repro Lite falhar
4. **UI minimalista**: Focar em funcionalidade, polimento depois
5. **Badges estáticos**: SVG simples, animações depois

### Explicitly Deferred to Phase 2+

- Autenticação de usuários
- Colaboração multi-revisor
- Versionamento de reviews
- API pública para integração
- Dashboard avançado de métricas
- Re-treinamento automático do modelo

---

## 9. Cronograma v0.2 Review MVP (2 semanas)

### Semana 1: Core Pipeline

**Dia 1-2: Ingestion & Claims**
- Issue #40: Ingestion Agent
- Issue #41: Claim Extractor Agent
- Issue #59: Database Models (Review, Claim)

**Dia 3-4: RAG & Citations**
- Issue #42: RAG Pipeline
- Issue #43: Citation Suggester Agent

**Dia 5: Checklist & Repro Lite**
- Issue #44: Checklist Agent
- Issue #45: Repro Lite Runner (opcional)

### Semana 2: Quality Score & UI

**Dia 6-7: Quality Score & Explicabilidade**
- Issue #46: Feature Builder
- Issue #47: Quality Predictor Service
- Issue #48: SHAP Explainer
- Issue #49: Score-Narrator Agent

**Dia 8-9: Artefatos & API**
- Issue #50: Report Builder v2
- Issue #51: Review JSON Schema
- Issue #52: Badge Generator
- Issue #56-58: API Routes

**Dia 10: UI & Testes**
- Issue #53-55: UI Pages
- Issue #60: LangGraph Pipeline Integration
- Issue #61: Testes de Integração

### Marcos

- **Marco 1 (Dia 5)**: Pipeline básico funcionando (ingestion → claims → cites → checklist)
- **Marco 2 (Dia 7)**: Quality Score e SHAP funcionando
- **Marco 3 (Dia 10)**: Review MVP completo com 3 reviews publicados

---

## 10. Documentação Adicional

Novos documentos criados:

- `docs/RAG_ADVANCED.md`: Especificação do pipeline RAG híbrido
- `docs/QUALITY_SCORE.md`: Especificação do modelo de Quality Score
- `docs/AGENTS_LANGGRAPH.md`: Especificação dos agentes LangGraph
- `docs/UI_SPECS.md`: Especificações de UI
- `docs/TELEMETRY.md`: Métricas e KPIs

---

## 11. Tech Choices

- **Embeddings**: `intfloat/e5-base` ou `all-MiniLM-L6-v2`
- **Re-rank**: `bge-reranker-large` (ou Cohere rerank se SaaS)
- **Tabular ML**: LightGBM + Isotonic Calibration
- **SHAP**: TreeExplainer (GBMs) ou KernelSHAP (fallback)
- **Index local**: FAISS HNSW; BM25: `tantivy`/`whoosh`
- **LLM**: GPT-4/Claude via API
- **Agents**: LangGraph

---

## 12. Segurança & Limites

- Containers **não-root**, CPU/Mem limit, **no-network** por padrão (allowlist p/ CrossRef/arXiv)
- Sanitização de PDFs; paths confinados; sem segredos no runtime
- Rate-limit por IP/chave; tempos máximos
- Validação de input rigorosa (URLs, PDFs, textos)

---

## 13. Testes & DoD

### Testes

- Unit (parser, RAG, checklist, feature builder, predictor wrapper, SHAP adapter)
- Integração com 3 "Hello Papers" (fim-a-fim)
- Validação de Quality Score (correlação com avaliação humana)

### Definition of Done v0.2

- [ ] 3 reviews publicados com `report.html` + `review.json` + badges
- [ ] Editor inline funcional (aceitar/editar/recusar sugestões)
- [ ] Score + SHAP + narrativa gerados e exibidos
- [ ] Métricas gravadas (TTFR, %claims com cite aceita, etc.)
- [ ] Pipeline end-to-end testado com 3 papers de referência
- [ ] Documentação atualizada

---

## 14. Referências

- `docs/RAG_ADVANCED.md`: Pipeline RAG detalhado
- `docs/QUALITY_SCORE.md`: Modelo de Quality Score detalhado
- `docs/AGENTS_LANGGRAPH.md`: Agentes LangGraph detalhado
- `docs/UI_SPECS.md`: Especificações de UI detalhadas
- `docs/TELEMETRY.md`: Métricas e KPIs
- `docs/ARCHITECTURE_V0.md`: Arquitetura base (mantida)
- `docs/DESIGN_SYSTEM_V0.md`: Design system (mantido)
