# Sprint 2: Hosted Papers + QualityScore v0 + Claims&Refs v0

## Contexto

**Mudança estratégica**: Reduzir ambição de "reprodutibilidade universal" no v0; focar em:
- **Hosted Paper + Review automático**
- **Quality Score v0** baseado em README/REPL (não logs de CI)
- **Claims & References v0** com reasoning (não só embeddings)
- **Badge interno** na página hospedada (não copiável externo)

## Objetivos

### 1. Frontend
- Páginas mínimas: `/`, `/jobs`, `/jobs/[id]`
- **Nova página**: `/papers/[paperId]` com:
  - PDF viewer (pdf.js)
  - Badge interno de status
  - Blocos: "Review summary", "QualityScore v0", "Claims & References"
  - Botão "Approve public review"

### 2. Backend
- APIs para upload/link de PDF
- Linkage job⇄paper
- Serving de dados para página hospedada
- Persistência de outputs (score, claims, refs)

### 3. Pipelines de IA (LangGraph)
- **QualityScoreV0**: sinais de reprodutibilidade via README/REPL
- **Claims&RefsV0**: extração → retrieval semântico → reasoning para rotular relação

## Entregáveis

### UI Next.js
- `/` (submit), `/jobs`, `/jobs/[id]`, `/papers/[paperId]` (hosted)
- Componente PDF viewer (pdf.js)
- Badge interno de status
- Blocos: Review summary, QualityScore v0, Claims & References
- Botão "Approve public review"

### APIs FastAPI
- `POST /papers` (metadata + upload/link PDF)
- `GET /papers/{id}` (tudo para render do hosted)
- `PATCH /papers/{id}/visibility` (aprovação)
- Extensão de `/jobs/{id}` para retornar `paper_id` se houver vínculo

### Esquemas/DB (Alembic)
- Tabela `papers` (id, title?, arxiv_id?, repo_url?, pdf_path, approved_public:boolean, created_at)
- Tabela `quality_scores` (paper_id FK, score:int 0–100, signals JSON, rationale JSON, created_at)
- Tabela `claims` (id, paper_id, text, span?, section?, created_at)
- Tabela `claim_links` (claim_id, source_paper_id? ou source_doc_id, source_citation, relation:{equivalent,complementary,contradictory,unclear}, confidence:0–1, context_excerpt, created_at)

### Pipelines (LangGraph)
- **QualityScoreV0**: entrada (repo_url, optional pdf), saída `QualityScoreV0.json` (score, signals[], rationale)
- **Claims&RefsV0**: entrada (pdf ou repo text), saída `ClaimsV0.json` (claims[]) e `ClaimLinksV0.json` (links[] com relação+confiança)

### Testes
- E2E: submissão → execução → hosted page renderizando score e ≥3 claims com classificações
- Unit para parsers e normalizadores de signals/claims

### Docs
- `docs/hosted-papers.md` (como funciona, privacidade, aprovação)
- `docs/quality-score-v0.md` (sinais, escala, limitações)
- `docs/claims-and-refs-v0.md` (pipeline, garantias, limitações)

## Plano de Implementação

### Fase 1: DB & Models (primeiro)
1. Criar migrations para `papers`, `quality_scores`, `claims`, `claim_links`
2. Adicionar relações em modelos SQLAlchemy
3. Schemas Pydantic definidos antes das rotas

### Fase 2: Storage/Config
1. `ARTIFACTS_BASE=/var/arandu/artifacts`, `PAPERS_BASE=/var/arandu/papers`
2. Endpoint para upload de PDF (armazenar em `PAPERS_BASE/{paper_id}/paper.pdf`)
3. Atualizar `docker-compose` com volumes para `papers`

### Fase 3: APIs
1. `POST /papers`: aceita (title?, arxiv_id?, repo_url?, pdf upload|url). Retorna `paper_id`
2. `GET /papers/{id}`: retorna metadata + score + claims + links + approval flag
3. `PATCH /papers/{id}/visibility`: `approved_public: bool`
4. Extender pipeline de job para: se `arxiv_id`/pdf_url vier em `POST /jobs`, criar/associar `paper`

### Fase 4: Pipelines LangGraph
1. **QualityScoreV0**:
   - Sinais: README com run steps; mapeamento script↔paper; exemplo de input; caminho CPU/sintético; seeds; env file
   - Produzir `score:int` e `rationale JSON`
   - Persistir em `quality_scores`

2. **Claims&RefsV0**:
   - Extrair claims (LLM)
   - Indexar corpus mínimo (título/abstract/seções de repositório interno)
   - Retrieval via embeddings → expandir contexto → LLM classifica relação
   - Persistir em `claims` e `claim_links`

### Fase 5: Frontend Next.js
1. Implementar `/papers/[paperId]` consumindo `GET /papers/{id}`
2. PDF viewer (pdf.js)
3. Blocos: Review summary, QualityScore, Claims&Refs
4. "Approve public review" → `PATCH /papers/{id}/visibility`
5. Remover fluxo de "copiar badge externo"; renderizar badge interno

### Fase 6: Testes & E2E
1. Adicionar cenários: criar paper (upload pdf) → rodar pipelines → endpoint retorna dados → página renderiza
2. Smoke com "Hello Paper" público

### Fase 7: Docs & Operação
1. Escrever 3 docs acima
2. Atualizar README com "Sprint 2 Usage"

## Issues

- **S2-FE-01**: Hosted paper page `/papers/[paperId]` com PDF viewer + blocos
- **S2-BE-01**: APIs `POST/GET/PATCH /papers` + vínculo job⇄paper + storage PDF
- **S2-AGENTS-01**: LangGraph **QualityScoreV0** → persistir em `quality_scores`
- **S2-AGENTS-02**: LangGraph **Claims&RefsV0** → persistir em `claims` e `claim_links`
- **S2-TEST-01**: E2E hosted page (PDF+score+≥3 claims classificados)
- **S2-DOCS-01**: Docs de hosted papers, score v0, claims&refs v0
- **S2-SEC-VERIFY**: Verificar enforcement de #31–#33 no código atual

## Critérios de Aceite

- [ ] Criar Paper (upload PDF) ⇒ `paper_id` retornado
- [ ] Após execução, `GET /papers/{id}` retorna: `approved_public`, `score`, `signals`, `rationale`, `claims[]`, `claim_links[]`
- [ ] Página `/papers/[paperId]` renderiza PDF + review + score + **≥3 claims** com relação e confiança
- [ ] Badge interno visível; **não existe** feature de copiar badge externo
- [ ] Logs de sistema e logs de experimento separados; limites e non-root ativos
- [ ] Testes E2E passam em CI

## Recursos & Config

### Variáveis de Ambiente
- `DB_URL`, `REDIS_URL`
- `ARTIFACTS_BASE=/var/arandu/artifacts`
- `PAPERS_BASE=/var/arandu/papers`
- `EMBED_MODEL`, `LLM_MODEL`, `LLM_API_KEY`

### Docker Compose
- Volumes para `papers`, `artifacts`
- Healthchecks

### Dados de Referência
- 1–2 PDFs públicos pequenos para teste
- 10–20 entradas para mini-corpus interno de referência (YAML/JSON provisório)

## Fora de Escopo (P2)

- Auth/contas
- S3/GCS
- WebSockets/SSE
- Priorização de jobs
- Multi-línguas
- Ledger epistemic completo

