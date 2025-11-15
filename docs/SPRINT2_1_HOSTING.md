# Sprint 2.1 - Hosting Foundation

## Visão Geral

Sprint 2.1 adiciona a fundação para **hosting nativo de papers** no Arandu, com sistema de identificação único (AID), versionamento, storage organizado por versão, e páginas hospedadas públicas.

## Objetivos

1. **AID + Versionamento**: Sistema de identificação único (AID) e versionamento de papers
2. **Storage por Versão**: Organização de arquivos por versão (`/papers/{aid}/v{version}/`)
3. **APIs de Ingest**: Endpoints para upload/link de PDF e criação de versões
4. **Streaming de PDF**: Servir PDFs de forma eficiente
5. **Geração de Thumbnails**: Job assíncrono para gerar thumbnails dos PDFs
6. **Páginas Hospedadas**: `/p/[aid]` e `/p/[aid]/viewer` com tabs e ScoreCard
7. **Alias**: Redirecionamento `/papers/[id]` => `/p/[aid]`

## Arquitetura

### Database Schema

#### Tabela `papers`
- `id` (UUID, PK)
- `aid` (String, unique) - Arandu ID (ex: `arandu-abc123`)
- `current_version` (Integer, default 1)
- `title` (String, nullable)
- `arxiv_id` (String, nullable)
- `repo_url` (String, nullable)
- `pdf_path` (String, nullable) - Path para PDF da versão atual
- `approved_public` (Boolean, default false)
- `created_at` (Timestamp)
- `updated_at` (Timestamp)

#### Tabela `paper_versions`
- `id` (UUID, PK)
- `paper_id` (UUID, FK -> papers.id)
- `version` (Integer)
- `pdf_path` (String)
- `thumbnail_path` (String, nullable)
- `created_at` (Timestamp)

#### Tabela `quality_scores`
- `id` (UUID, PK)
- `paper_id` (UUID, FK -> papers.id)
- `version` (Integer, nullable) - Versão do paper quando score foi calculado
- `score` (Integer, 0-100)
- `signals` (JSON) - Sinais extraídos (README, REPL, etc.)
- `rationale` (JSON) - Justificativa do score
- `created_at` (Timestamp)

#### Tabela `claims`
- `id` (UUID, PK)
- `paper_id` (UUID, FK -> papers.id)
- `version` (Integer, nullable)
- `text` (Text)
- `span` (JSON, nullable) - Posições no texto
- `section` (String, nullable) - intro/method/results/discussion
- `created_at` (Timestamp)

#### Tabela `claim_links`
- `id` (UUID, PK)
- `claim_id` (UUID, FK -> claims.id)
- `source_paper_id` (UUID, FK -> papers.id, nullable)
- `source_doc_id` (String, nullable) - ID de documento externo
- `source_citation` (String) - Citação formatada
- `relation` (Enum) - equivalent, complementary, contradictory, unclear
- `confidence` (Float, 0-1)
- `context_excerpt` (Text) - Trecho de contexto usado para classificação
- `created_at` (Timestamp)

### Storage Structure

```
PAPERS_BASE/
  {aid}/
    v1/
      paper.pdf
      thumbnail.jpg
      review.json
    v2/
      paper.pdf
      thumbnail.jpg
      review.json
    ...
```

### APIs

#### `POST /papers`
Cria novo paper com versão inicial.

**Request:**
```json
{
  "title": "Paper Title",
  "arxiv_id": "2301.12345",
  "repo_url": "https://github.com/user/repo",
  "pdf_file": <multipart/form-data> ou "pdf_url": "https://..."
}
```

**Response:**
```json
{
  "id": "uuid",
  "aid": "arandu-abc123",
  "version": 1,
  "title": "Paper Title",
  "pdf_path": "/papers/arandu-abc123/v1/paper.pdf"
}
```

#### `POST /papers/{aid}/versions`
Cria nova versão do paper.

**Request:** Mesmo formato de `POST /papers`

**Response:**
```json
{
  "id": "uuid",
  "aid": "arandu-abc123",
  "version": 2,
  "pdf_path": "/papers/arandu-abc123/v2/paper.pdf"
}
```

#### `GET /papers/{aid}`
Retorna dados completos do paper (versão atual).

**Response:**
```json
{
  "id": "uuid",
  "aid": "arandu-abc123",
  "current_version": 2,
  "title": "Paper Title",
  "arxiv_id": "2301.12345",
  "repo_url": "https://github.com/user/repo",
  "approved_public": true,
  "quality_score": {
    "score": 75,
    "signals": {...},
    "rationale": {...}
  },
  "claims": [...],
  "claim_links": [...],
  "versions": [
    {"version": 1, "created_at": "..."},
    {"version": 2, "created_at": "..."}
  ]
}
```

#### `GET /papers/{aid}/v{version}/pdf`
Streaming de PDF.

**Response:** PDF file com headers apropriados.

#### `PATCH /papers/{aid}/visibility`
Atualiza aprovação pública.

**Request:**
```json
{
  "approved_public": true
}
```

### UI Pages

#### `/p/[aid]`
Página principal do paper hospedado.

**Componentes:**
- Header com título, badge interno (verde/amarelo/vermelho)
- ScoreCard (score, tier, sinais principais)
- Tabs: Overview, Claims, Score, Viewer
- Overview: Resumo, qualidade, recomendações
- Claims: Lista de claims com links classificados
- Score: Score detalhado, SHAP, narrativa
- Viewer: Link para `/p/[aid]/viewer`

#### `/p/[aid]/viewer`
PDF viewer com tabs.

**Componentes:**
- PDFViewer (pdf.js)
- Tabs: PDF, Claims, Score
- Sidebar com navegação de claims

#### Alias `/papers/[id]`
Redireciona para `/p/[aid]` (301 redirect).

### Jobs

#### `generate_thumbnail`
Job RQ que gera thumbnail do PDF.

**Input:** `paper_id`, `version`, `pdf_path`
**Output:** `thumbnail_path` salvo em `paper_versions`

## Testes E2E

1. Criar paper (upload PDF) → `aid` retornado
2. Após processamento, `GET /papers/{aid}` retorna score, claims, links
3. Página `/p/[aid]` renderiza PDF + review + score + ≥3 claims classificados
4. Badge interno visível
5. Thumbnail gerado e acessível

## Documentação

- `docs/hosted-papers.md`: Como funciona, privacidade, aprovação
- `docs/quality-score-v0.md`: Sinais, escala, limitações
- `docs/claims-and-refs-v0.md`: Pipeline, garantias, limitações

## Critérios de Aceite

- [ ] AID gerado automaticamente e único
- [ ] Versões incrementam corretamente
- [ ] Storage organizado por versão
- [ ] Upload de PDF funciona
- [ ] Streaming de PDF eficiente
- [ ] Thumbnails gerados assincronamente
- [ ] Páginas `/p/[aid]` e `/p/[aid]/viewer` funcionais
- [ ] Alias `/papers/[id]` redireciona corretamente
- [ ] Badge interno renderizado
- [ ] Testes E2E passando

