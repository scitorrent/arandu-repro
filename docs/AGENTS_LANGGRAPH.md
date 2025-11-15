# Agentes LangGraph - Arandu CoReview Studio

## Visão Geral

Pipeline de agentes usando LangGraph para processar papers, extrair claims, sugerir citações, gerar checklist, executar Repro Lite, calcular Quality Score e gerar narrativas.

## Arquitetura

### State (Estado Global)

```python
@dataclass
class ReviewState:
    """
    Global state for the agent pipeline.

    Holds all relevant information and artifacts produced during the review process,
    including paper metadata, repository info, extracted claims, checklist, reproducibility
    trace, quality score, generated artifacts, errors, and additional metadata.
    """
    review_id: str  # UUID
    paper: PaperMeta
    repo: RepoMeta | None
    claims: list[Claim]
    checklist: Checklist
    repro_lite: ReproLiteTrace | None
    quality: QualityScore | None
    artifacts: Artifacts
    errors: list[str]
    metadata: dict
```

### Nodes (Agentes)

#### 1. Ingestion Agent
- **Input**: URL/DOI ou PDF base64
- **Output**: PaperMeta (title, authors, venue, year, pdf_ptr)
- **Função**: 
  - Baixa PDF/HTML
  - Cleaning (remove headers/footers)
  - Extrai metadados (title, authors, venue, year)
- **Tools**: PDF parser, HTML parser, metadata extractors

#### 2. Claim Extractor
- **Input**: PaperMeta (pdf_ptr)
- **Output**: list[Claim] com text, section, spans
- **Função**:
  - Segmenta claims por seção (intro/method/results/discussion)
  - Gera spans (posições no texto)
  - Usa LLM + heurísticas
- **Tools**: LLM (GPT-4/Claude), PDF parser, section detector

#### 3. Citation Suggester
- **Input**: list[Claim], PaperMeta
- **Output**: list[Claim] com citations_suggested[]
- **Função**:
  - RAG híbrido (embeddings + BM25)
  - Re-rank (cross-encoder)
  - Retorna BibTeX + scores
- **Tools**: RAG pipeline, CrossRef/arXiv APIs

#### 4. Checklist Agent
- **Input**: PaperMeta, RepoMeta, list[Claim]
- **Output**: Checklist preenchido
- **Função**:
  - Regras determinísticas + LLM
  - Preenche rationale para cada item
- **Tools**: LLM, rule engine

#### 5. Repro Lite Runner (opcional)
- **Input**: RepoMeta, PaperMeta
- **Output**: ReproLiteTrace
- **Função**:
  - Smoke-run CPU-only em toy data/seed fixo
  - Coleta traces (exit_code, duration, logs, env_fingerprint)
- **Tools**: Docker executor (reuso do Arandu Repro v0)

#### 6. Feature Builder
- **Input**: PaperMeta, RepoMeta, list[Claim], Checklist, ReproLiteTrace
- **Output**: QualityFeatures
- **Função**: Agrega features para o modelo de qualidade
- **Tools**: Feature extractors

#### 7. Quality Predictor
- **Input**: QualityFeatures
- **Output**: QualityScore (score, tier, features_map)
- **Função**: Carrega modelo treinado, retorna score/tier
- **Tools**: ML model service

#### 8. SHAP Explainer
- **Input**: QualityScore, QualityFeatures
- **Output**: SHAPExplanation[] (top-k)
- **Função**: Computa contribuições locais
- **Tools**: SHAP library

#### 9. Score-Narrator Agent
- **Input**: QualityScore, SHAPExplanation[], PaperMeta, RepoMeta, list[Claim], Checklist
- **Output**: Narrative (executive + technical)
- **Função**: 
  - Lê score, SHAP, features, paper/repo
  - Argumenta (executivo+técnico) com business sense
  - Ancora evidências (claim_id, linha README, item checklist)
- **Tools**: LLM (GPT-4/Claude), templates

#### 10. Report Builder
- **Input**: ReviewState completo
- **Output**: Artifacts (report.html, review.json, badges)
- **Função**: Gera artefatos finais
- **Tools**: Template engine, badge generator

## Edges (Fluxo)

```
START
  ↓
Ingestion Agent
  ↓
Claim Extractor
  ↓
┌─────────────────┬─────────────────┐
│                 │                 │
Citation Suggester  Checklist Agent
│                 │                 │
└────────┬────────┴────────┬────────┘
         │                 │
         └────────┬─────────┘
                  ↓
         (optional) Repro Lite Runner
                  ↓
         Feature Builder
                  ↓
         ┌────────┴────────┐
         │                 │
Quality Predictor    SHAP Explainer
         │                 │
         └────────┬────────┘
                  ↓
         Score-Narrator Agent
                  ↓
         Report Builder
                  ↓
         END
```

## Implementação

### LangGraph Setup

```python
from langgraph.graph import StateGraph, END

def create_review_graph():
    workflow = StateGraph(ReviewState)
    
    # Add nodes
    workflow.add_node("ingestion", ingestion_agent)
    workflow.add_node("claim_extractor", claim_extractor_agent)
    workflow.add_node("citation_suggester", citation_suggester_agent)
    workflow.add_node("checklist", checklist_agent)
    workflow.add_node("repro_lite", repro_lite_runner)
    workflow.add_node("feature_builder", feature_builder)
    workflow.add_node("quality_predictor", quality_predictor)
    workflow.add_node("shap_explainer", shap_explainer)
    workflow.add_node("score_narrator", score_narrator_agent)
    workflow.add_node("report_builder", report_builder)
    
    # Add edges
    workflow.set_entry_point("ingestion")
    workflow.add_edge("ingestion", "claim_extractor")
    workflow.add_edge("claim_extractor", "citation_suggester")
    workflow.add_edge("claim_extractor", "checklist")
    workflow.add_conditional_edges(
        "checklist",
        should_run_repro_lite,
        {
            "yes": "repro_lite",
            "no": "feature_builder"
        }
    )
    workflow.add_edge("repro_lite", "feature_builder")
    workflow.add_edge("feature_builder", "quality_predictor")
    workflow.add_edge("quality_predictor", "shap_explainer")
    workflow.add_edge("shap_explainer", "score_narrator")
    workflow.add_edge("score_narrator", "report_builder")
    workflow.add_edge("report_builder", END)
    
    return workflow.compile()
```

### Error Handling

- Cada node pode adicionar erros ao `state.errors`
- Conditional edges podem pular nodes em caso de erro
- Fallback para valores padrão quando possível

## Configuração

### Variáveis de Ambiente

```bash
LLM_MODEL=gpt-4-turbo-preview
LLM_TEMPERATURE=0.3
RAG_ENABLED=true
REPRO_LITE_ENABLED=true
QUALITY_SCORE_ENABLED=true
SHAP_ENABLED=true
```

## Roadmap

- [ ] Implementar Ingestion Agent
- [ ] Implementar Claim Extractor
- [ ] Integrar Citation Suggester (RAG)
- [ ] Implementar Checklist Agent
- [ ] Integrar Repro Lite Runner
- [ ] Implementar Feature Builder
- [ ] Integrar Quality Predictor
- [ ] Implementar SHAP Explainer
- [ ] Implementar Score-Narrator Agent
- [ ] Implementar Report Builder
- [ ] Testes end-to-end

