# Quality Score Model - Arandu CoReview Studio

## Visão Geral

Modelo preditivo de **Score de Qualidade** (0-100) que estima a qualidade metodológica e reprodutibilidade provável de um paper dado features extraídas de paper, repo, traces, checklist e citações.

## Objetivo

Fornecer uma estimativa quantitativa e **explicável** da qualidade de um paper, com:
- Score 0-100 (calibrado)
- Tier (A/B/C/D)
- Explicações SHAP locais
- Narrativa executiva e técnica

## Features

### Paper/Texto

- Número de *claims* extraídos
- Densidade de evidências (claims por seção)
- Presença de:
  - Ablation studies
  - Baseline comparisons
  - Error bars / confidence intervals
  - Seeds / randomness control
  - Statistical tests
- Comprimento e estrutura (seções presentes)
- Qualidade de escrita (heurísticas simples)

### Repo

- Presença de arquivos de dependências:
  - `requirements.txt` / `pyproject.toml` / `environment.yml`
  - Lock files (`poetry.lock`, `Pipfile.lock`)
- Pinagem de versões (versões fixas vs ranges)
- CI/CD configurado (GitHub Actions, etc.)
- Testes presentes (`tests/`, `test_*.py`)
- README com seção "How to reproduce"
- Licença presente
- Estrutura de diretórios organizada

### Citações

- Cobertura: % de claims com ≥1 referência sugerida
- Diversidade: auto-cite vs externo
- Idade/autoridade das fontes (anos desde publicação, venue impact)
- Relevância média (score de rerank)

### Checklist

- % de itens OK
- Itens críticos faltantes:
  - Dados disponíveis
  - Seeds fixos
  - Métricas definidas
  - Ablações reportadas
  - Comparativos com baselines
  - Licença de código/dados

### Traces L1 (Repro Lite)

- Exit code = 0 (sucesso)
- Tempo de execução (normalizado)
- Variância de seed (se múltiplos runs)
- Footprint de dependências (número, tamanho)
- Warnings/errors capturados

### Engajamento

- Issues abertos/fechados no repo
- PRs abertos/fechados
- Releases/tags
- Documentação (docs/, wiki)

## Modelagem

### Algoritmo

- **Base**: LightGBM ou XGBoost (tabular ML)
- **Calibração**: Isotonic calibration para output 0-100
- **Validação**: K-fold cross-validation
- **Monitoramento**: Drift detection (distribuição de features)

### Treinamento

#### Dataset Inicial

- **Semente humana**: 50-200 papers com avaliação manual
- **Sinais fracos**: score heurístico inicial (regras) para calibrar via ML
- **Expansão**: coleta contínua de labels (feedback de revisores)

#### Feature Engineering

```python
@dataclass
class QualityFeatures:
    """
    Schema for features used in the Quality Score model.

    This dataclass captures methodological and reproducibility signals extracted from papers,
    repositories, checklists, traces, and citations. Each field represents a specific feature
    used to estimate the quality and reproducibility of a scientific paper.
    """
    # Paper
    num_claims: int
    claims_per_section: dict[str, float]
    has_ablation: bool
    has_baselines: bool
    has_error_bars: bool
    has_seeds: bool
    
    # Repo
    has_requirements: bool
    has_lock_file: bool
    versions_pinned: float  # 0-1
    has_ci: bool
    has_tests: bool
    has_repro_readme: bool
    has_license: bool
    
    # Citations
    citation_coverage: float  # 0-1
    citation_diversity: float  # 0-1
    avg_citation_relevance: float
    
    # Checklist
    checklist_pct_ok: float  # 0-1
    critical_items_missing: int
    
    # Traces
    repro_exit_code: int | None
    repro_duration: float | None
    repro_seed_variance: float | None
    
    # Engagement
    num_issues: int
    num_prs: int
    num_releases: int
```

### Inferência

#### Serviço Online

```python
POST /reviews/{id}/score/predict
→ {
    "score": 78.5,
    "tier": "B",
    "version": "v1.0.0",
    "features": {...},
    "shap_top": [...]
}
```

#### Tiers

- **A**: 85-100 (Excelente)
- **B**: 70-84 (Bom)
- **C**: 55-69 (Regular)
- **D**: <55 (Necessita melhorias)

## Explicabilidade (SHAP)

### SHAP Local

- **Método**: TreeExplainer (para GBMs) ou KernelSHAP (fallback)
- **Output**: top-k contribuições (positivas/negativas) por instância
- **Mapeamento**: features → evidências (âncoras no report)

### Formato

```python
@dataclass
class SHAPExplanation:
    feature_name: str
    feature_value: Any
    shap_value: float  # contribuição para o score
    evidence_anchor: str  # link para evidência no paper/repo
```

## Versionamento

- **Modelo**: versionado (semver)
- **Feature Schema**: versionado e validado
- **Compatibilidade**: modelos antigos mantidos para reprodutibilidade

## Métricas de Performance

- **MAE** (Mean Absolute Error): target <5 pontos
- **Calibração**: Brier score <0.1
- **Correlação**: com avaliação humana (target r>0.7)
- **Latency**: <500ms por predição

## Roadmap

- [ ] Feature builder (extração de features)
- [ ] Dataset semente (50-200 papers)
- [ ] Treinamento inicial (LightGBM + calibração)
- [ ] Serviço de inferência
- [ ] SHAP adapter
- [ ] Monitoramento de drift
- [ ] Pipeline de re-treinamento

