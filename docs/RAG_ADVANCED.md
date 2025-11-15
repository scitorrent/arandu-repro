# RAG Avançado para Arandu CoReview Studio

## Visão Geral

Sistema de RAG (Retrieval-Augmented Generation) híbrido para sugerir citações relevantes por *claim* extraído de papers científicos.

## Arquitetura

### Índices

1. **Índice Local por Paper** (FAISS HNSW)
   - Embeddings: `intfloat/e5-base` ou `all-MiniLM-L6-v2`
   - Estrutura: HNSW (Hierarchical Navigable Small World) para busca rápida
   - Escopo: seções do paper atual (intro, method, results, discussion)

2. **Corpus Externo Leve** (CrossRef/arXiv via API + cache SQLite)
   - Fonte: APIs CrossRef e arXiv
   - Cache: SQLite local para reduzir chamadas
   - Estrutura: metadados (title, authors, venue, year, DOI/URL) + embeddings

### Pipeline de Busca Híbrida

```
Claim Text
    ↓
[Embedding] → Dense Vector (e5-base)
    ↓
[BM25] → Sparse Vector (tantivy/whoosh)
    ↓
[Late Fusion] → Z-score normalization + weighted combination
    ↓
[Top-50 Candidates]
    ↓
[Re-ranking] → Cross-encoder (bge-reranker-large)
    ↓
[Top-K Results] → Dedup + MMR diversification
    ↓
Citations with scores
```

### Componentes

#### 1. Embedding Service
- Modelo: `intfloat/e5-base` (768 dim) ou `all-MiniLM-L6-v2` (384 dim)
- Função: converter texto (claims, papers) em vetores densos
- Cache: embeddings de papers processados

#### 2. BM25 Searcher
- Biblioteca: `tantivy` (Rust) ou `whoosh` (Python)
- Função: busca esparsa baseada em termos
- Índice: on-the-fly para corpus externo

#### 3. Hybrid Fusion
- Método: Late fusion com z-score normalization
- Pesos: configuráveis (default: 0.6 dense, 0.4 sparse)
- Output: lista unificada de top-50 candidatos

#### 4. Re-ranker
- Modelo: `bge-reranker-large` (cross-encoder)
- Função: reordenar top-50 → top-k (k=5-10)
- Input: (claim, candidate_title+abstract) pairs

#### 5. Deduplication & Diversification
- Normalização: DOI, Title (lowercase, remove punctuation)
- Agrupamento: por obra (mesmo DOI = mesmo paper)
- Diversificação: MMR (Maximal Marginal Relevance) para evitar redundância

## Implementação

### Estrutura de Dados

```python
@dataclass
class CitationCandidate:
    title: str
    authors: list[str]
    venue: str
    year: int
    doi: str | None
    url: str
    abstract: str | None
    score_dense: float
    score_sparse: float
    score_final: float
    score_rerank: float
    justification: str  # Por que esta citação é relevante
```

### API Contracts

```python
def suggest_citations(
    claim_text: str,
    claim_section: str,  # intro/method/results/discussion
    paper_context: dict,  # metadados do paper atual
    top_k: int = 5,
    min_score: float = 0.3
) -> list[CitationCandidate]:
    """Sugere citações relevantes para um claim."""
    pass
```

## Configuração

### Variáveis de Ambiente

```bash
RAG_EMBEDDING_MODEL=intfloat/e5-base
RAG_RERANKER_MODEL=BAAI/bge-reranker-large
RAG_DENSE_WEIGHT=0.6
RAG_SPARSE_WEIGHT=0.4
RAG_TOP_K=5
RAG_MIN_SCORE=0.3
CROSSREF_API_KEY=optional
ARXIV_CACHE_TTL=86400  # 24h
```

## Métricas

- **Recall@K**: % de citações relevantes encontradas no top-K
- **Precision@K**: % de citações no top-K que são relevantes
- **Latency**: tempo médio de busca (target: <2s por claim)
- **Cache hit rate**: % de buscas servidas do cache

## Roadmap

- [ ] Implementar embedding service com cache
- [ ] Integrar BM25 com tantivy/whoosh
- [ ] Implementar late fusion
- [ ] Integrar re-ranker cross-encoder
- [ ] Adicionar dedup e MMR
- [ ] Testes com papers de referência
- [ ] Otimização de latência

