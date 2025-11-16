# Sprint 2 - Review MVP - Planejamento de PRs

## Estratégia de PRs

**Princípios:**
1. **Incremental**: Cada PR adiciona valor e pode ser testado isoladamente
2. **Testável**: Cada PR inclui testes unitários e/ou de integração
3. **Revisável**: PRs de tamanho razoável (<500 linhas quando possível)
4. **Lógico**: Agrupar funcionalidades relacionadas

## PRs Planejados

### PR #1: Review API Foundation ✅ (JÁ FEITO)
**Branch:** `feat/review-mvp-sprint2` (base)

**Conteúdo:**
- Review model + migration
- Review API routes (POST/GET/Artifacts/Score)
- Review processor skeleton
- Config settings

**Testes:**
- [ ] Unit: Review model creation/validation
- [ ] Unit: API routes (POST/GET/status/artifacts)
- [ ] Integration: Create review via API, verify DB state

**Status:** ✅ Completo (commits já feitos)

---

### PR #2: PDF/HTML Ingestion & Claim Extraction
**Branch:** `feat/review-ingestion-claims` (from `feat/review-mvp-sprint2`)

**Conteúdo:**
- PDF parser (PyMuPDF) com fallback
- HTML parser (se URL fornecida)
- Metadata extraction (title, authors, venue, year)
- Section segmentation (Abstract, Intro, Methods, Results, Conclusion)
- Claim extraction (baseline determinística + LLM assist opcional)
- Text cleaning (remove headers/footers repetidos)

**Arquivos:**
- `backend/app/worker/review_ingestion.py`
- `backend/app/worker/claim_extractor.py`
- `backend/app/worker/section_segmenter.py`
- `backend/tests/test_review_ingestion.py`
- `backend/tests/test_claim_extractor.py`

**Testes:**
- [ ] Unit: PDF parsing (sample PDFs)
- [ ] Unit: HTML parsing (sample URLs)
- [ ] Unit: Section segmentation (heurísticas)
- [ ] Unit: Claim extraction (baseline patterns)
- [ ] Integration: End-to-end ingestion → claims JSON

**Acceptance:**
- ≥5 claims extraídos em papers padrão
- Tempo < 30s em CPU
- Ruído baixo (claims relevantes)

**Issues:** #40 (parcial), #41

---

### PR #3: RAG Pipeline - Citation Suggester
**Branch:** `feat/review-rag-citations` (from `feat/review-mvp-sprint2`)

**Conteúdo:**
- Embeddings service (sentence-transformers: all-MiniLM-L6-v2)
- BM25 index (Whoosh)
- Hybrid search (α·BM25 + (1-α)·cosine)
- Re-ranking (cross-encoder: cross-encoder/ms-marco-MiniLM-L-6-v2)
- Deduplication & diversification
- Citation suggester agent (integração por claim)

**Arquivos:**
- `backend/app/worker/rag/embeddings.py`
- `backend/app/worker/rag/bm25_index.py`
- `backend/app/worker/rag/hybrid_search.py`
- `backend/app/worker/rag/reranker.py`
- `backend/app/worker/citation_suggester.py`
- `backend/tests/test_rag_pipeline.py`
- `backend/tests/test_citation_suggester.py`

**Testes:**
- [ ] Unit: Embeddings generation
- [ ] Unit: BM25 search
- [ ] Unit: Hybrid fusion
- [ ] Unit: Re-ranking
- [ ] Unit: Deduplication
- [ ] Integration: Citation suggester end-to-end (mock corpus)

**Acceptance:**
- Cobertura ≥70% das claims com ≥1 sugestão
- Latência < 2s/claim CPU
- Top-k relevante (avaliação manual em sample)

**Issues:** #42, #43 (parcial)

---

### PR #4: Method Checklist Generator
**Branch:** `feat/review-checklist` (from `feat/review-mvp-sprint2`)

**Conteúdo:**
- Checklist heurísticas (dados, seeds, ambiente, comandos, métricas, comparativos, licenças)
- Evidence extractor (paper text + repo analysis)
- Status determination (ok/partial/missing)
- Rationale generation (LLM assist opcional)

**Arquivos:**
- `backend/app/worker/checklist_generator.py`
- `backend/app/worker/evidence_extractor.py`
- `backend/tests/test_checklist_generator.py`

**Testes:**
- [ ] Unit: Checklist generation (sample papers)
- [ ] Unit: Evidence extraction (paper + repo)
- [ ] Unit: Status determination logic
- [ ] Integration: Checklist completo (paper + repo)

**Acceptance:**
- Checklist gerado com itens OK/Missing/Suspect
- Rationale preenchido
- Evidências ancoradas (snippets + origem)

**Issues:** #43

---

### PR #5: Quality Score + SHAP
**Branch:** `feat/review-quality-score` (from `feat/review-mvp-sprint2`)

**Conteúdo:**
- Feature builder (agrega features de paper/repo/checklist/citations)
- Quality predictor (GradientBoosting baseline, calibrado 0-100)
- SHAP explainer (TreeExplainer → top-k features)
- Score-Narrator agent (explicação executiva + técnica)

**Arquivos:**
- `backend/app/worker/quality/feature_builder.py`
- `backend/app/worker/quality/predictor.py`
- `backend/app/worker/quality/shap_explainer.py`
- `backend/app/worker/quality/score_narrator.py`
- `backend/models/quality_score_v01.pkl` (modelo baseline)
- `backend/tests/test_quality_score.py`

**Testes:**
- [ ] Unit: Feature extraction
- [ ] Unit: Model prediction (mock features)
- [ ] Unit: SHAP computation
- [ ] Unit: Score-Narrator generation
- [ ] Integration: Quality score end-to-end (sample review)

**Acceptance:**
- Pipeline roda em CPU < 3s/review
- SHAP top-k consistente com score
- Narrativa clara e ancorada em evidências

**Issues:** (Quality Score não tem issue específica, mas é parte do MVP)

---

### PR #6: Badge Generator
**Branch:** `feat/review-badges` (from `feat/review-mvp-sprint2`)

**Conteúdo:**
- Badge SVG generator (Claim-mapped, Method-check, Citations-augmented)
- Badge logic (critérios para cada badge)
- SVG endpoint (`GET /api/v1/badges/{id}/{badge}.svg`)
- Badge status calculation

**Arquivos:**
- `backend/app/worker/badge_generator.py`
- `backend/app/api/routes/badges.py`
- `backend/tests/test_badge_generator.py`
- `backend/tests/test_badge_endpoints.py`

**Testes:**
- [ ] Unit: Badge logic (critérios)
- [ ] Unit: SVG generation
- [ ] Unit: Badge endpoint
- [ ] Integration: Badges gerados corretamente para sample reviews

**Acceptance:**
- Badges SVG válidos
- Critérios corretos (claim-mapped: ≥5 claims, etc.)
- Endpoints funcionais

**Issues:** #46

---

### PR #7: Report Generation (HTML + JSON)
**Branch:** `feat/review-reports` (from `feat/review-mvp-sprint2`)

**Conteúdo:**
- HTML report generator (com score/SHAP/narrativa)
- JSON summary generator (estrutura completa)
- Template engine (Jinja2 ou similar)
- Report builder (integra claims, citations, checklist, score)

**Arquivos:**
- `backend/app/worker/report_builder.py`
- `backend/app/worker/templates/report.html.j2`
- `backend/tests/test_report_builder.py`

**Testes:**
- [ ] Unit: HTML generation (sample data)
- [ ] Unit: JSON generation (validação de schema)
- [ ] Integration: Report completo (sample review)

**Acceptance:**
- HTML válido e acessível
- JSON schema válido
- Todas as seções presentes (badges, resumo, claims, checklist, score, recomendações)

**Issues:** #44

---

### PR #8: LangGraph Pipeline Integration
**Branch:** `feat/review-langgraph-pipeline` (from `feat/review-mvp-sprint2`)

**Conteúdo:**
- LangGraph state definition
- Pipeline nodes (Ingestion → Claims → Cites → Checklist → Score → Badges → Report)
- Edge logic (conditional flows)
- Error handling e recovery
- Integração com `review_processor.py`

**Arquivos:**
- `backend/app/worker/review_pipeline.py` (LangGraph)
- `backend/app/worker/review_state.py`
- Atualizar `backend/app/worker/review_processor.py`
- `backend/tests/test_review_pipeline.py`

**Testes:**
- [ ] Unit: Pipeline nodes individuais
- [ ] Unit: Edge logic (conditional flows)
- [ ] Integration: Pipeline end-to-end (mock data)
- [ ] Integration: Error handling

**Acceptance:**
- Pipeline executa end-to-end
- Error handling funciona (degrade graciosamente)
- State management correto

**Issues:** #60

---

### PR #9: Reviewer UI (Next.js)
**Branch:** `feat/review-ui` (from `feat/review-mvp-sprint2`)

**Conteúdo:**
- `/reviews/submit` page (formulário)
- `/reviews/[id]` page (tabs: Overview, Claims, Checklist, Score, Artifacts)
- Editor inline (aceitar/editar/recusar sugestões)
- ScorePanel + NarrationDrawer
- BadgeTile component
- Auto-refresh até completed

**Arquivos:**
- `frontend/app/reviews/submit/page.tsx`
- `frontend/app/reviews/[id]/page.tsx`
- `frontend/components/review/ClaimCard.tsx`
- `frontend/components/review/ChecklistPanel.tsx`
- `frontend/components/review/ScorePanel.tsx`
- `frontend/components/review/NarrationDrawer.tsx`
- `frontend/components/review/BadgeTile.tsx`
- `frontend/tests/` (component tests)

**Testes:**
- [ ] Unit: Componentes React (ClaimCard, ChecklistPanel, etc.)
- [ ] E2E: Submit → Status → Resultado (Playwright ou similar)
- [ ] A11y: Contraste, navegação por teclado

**Acceptance:**
- UI funcional end-to-end
- Editor inline persiste (PATCH `/reviews/{id}`)
- A11y AA compliant

**Issues:** #45

---

### PR #10: Telemetria & Métricas
**Branch:** `feat/review-telemetry` (from `feat/review-mvp-sprint2`)

**Conteúdo:**
- Métricas collection (tempo parsing, #claims, cobertura citações, checklist pass rate, tempo total)
- `/api/v1/metrics` endpoint (JSON simples)
- Logs estruturados (JSON-lines) para review events
- Privacidade (sem PII, hashes de PDF)

**Arquivos:**
- `backend/app/utils/metrics.py`
- `backend/app/api/routes/metrics.py`
- Atualizar `backend/app/worker/review_processor.py` (adicionar métricas)
- `backend/tests/test_metrics.py`

**Testes:**
- [ ] Unit: Métricas collection
- [ ] Unit: Metrics endpoint
- [ ] Integration: Métricas gravadas durante processamento

**Acceptance:**
- Métricas expostas via endpoint
- Logs estruturados para eventos de review
- Sem PII nos logs

**Issues:** #47

---

### PR #11: Testes End-to-End & DoD
**Branch:** `feat/review-e2e-tests` (from `feat/review-mvp-sprint2`)

**Conteúdo:**
- 2 papers públicos de teste (arXiv CS.CL, ML)
- Testes E2E completos (submissão → completed → artefatos válidos)
- Validação de artefatos (HTML válido, JSON schema válido)
- DoD checklist validation

**Arquivos:**
- `backend/tests/integration/test_review_e2e.py`
- `backend/tests/fixtures/papers/` (sample papers)
- `backend/tests/fixtures/schemas/review.json` (JSON schema)

**Testes:**
- [ ] E2E: Paper 1 (submissão → completed)
- [ ] E2E: Paper 2 (submissão → completed)
- [ ] Validação: HTML report válido
- [ ] Validação: JSON summary válido (schema)
- [ ] Validação: Badges gerados
- [ ] Validação: DoD checklist

**Acceptance:**
- 2 reviews públicos completos
- Artefatos válidos
- DoD satisfeito

**Issues:** #61

---

## Resumo

**Total de PRs:** 11 (incluindo o PR #1 já feito)

**Ordem sugerida:**
1. ✅ PR #1: Foundation (já feito)
2. PR #2: Ingestion & Claims
3. PR #3: RAG & Citations
4. PR #4: Checklist
5. PR #5: Quality Score + SHAP
6. PR #6: Badges
7. PR #7: Reports
8. PR #8: LangGraph Pipeline (integra tudo)
9. PR #9: UI
10. PR #10: Telemetria
11. PR #11: E2E Tests & DoD

**Cobertura de testes:**
- Cada PR inclui testes unitários e/ou de integração
- PR #11 valida end-to-end completo
- Meta: >80% cobertura de código

**Dependências:**
- PRs #2-7 podem ser desenvolvidos em paralelo (após PR #1)
- PR #8 depende de #2-7 (integra tudo)
- PR #9 depende de #8 (UI consome pipeline)
- PR #10 pode ser feito em paralelo
- PR #11 depende de todos (validação final)

