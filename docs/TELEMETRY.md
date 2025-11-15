# Telemetria e Métricas - Arandu CoReview Studio

## Visão Geral

Sistema de métricas e KPIs para monitorar aquisição, valor, custo e qualidade do Arandu CoReview Studio.

## Métricas

### Aquisição

- **#reviews/semana**: Número de reviews submetidos por semana
- **%autores que adotam badge**: Porcentagem de autores que adicionam badge ao README após review
- **Taxa de conversão**: Submissão → Review completo → Badge adotado

### Valor

- **%claims com cite aceita**: Porcentagem de claims que têm pelo menos uma citação aceita pelo revisor
- **TTFR (Tempo até First Review)**: Tempo médio desde submissão até review completo
- **Taxa de aceitação de sugestões**: % de sugestões (citações, checklist items) aceitas vs rejeitadas

### Custo

- **CPU-h/review**: CPU horas consumidas por review (incluindo RAG, ML, Repro Lite)
- **$/review**: Custo estimado por review (compute + storage + APIs externas)
- **Latência média**: Tempo médio de processamento por review

### Qualidade

- **NPS revisor/autor**: Net Promoter Score de revisores e autores
- **Correlação score vs avaliação humana**: Correlação entre Quality Score e avaliação manual (target: r>0.7)
- **Estabilidade SHAP**: Variância das explicações SHAP entre runs similares
- **Precisão de citações**: % de citações sugeridas que são relevantes (avaliação manual)

## Implementação

### Estrutura de Dados

```python
@dataclass
class ReviewMetrics:
    """
    Stores metrics for a single review, including acquisition, value, cost, and quality indicators.

    Acquisition:
        - badge_adopted, badge_adopted_at
    Value:
        - num_claims, num_claims_with_accepted_cites, num_suggestions_accepted, num_suggestions_rejected, ttfr_seconds
    Cost:
        - cpu_hours, estimated_cost_usd, latency_seconds
    Quality:
        - quality_score, human_evaluation_score, nps_reviewer, nps_author
    """
    review_id: str
    submitted_at: datetime
    completed_at: datetime | None
    ttfr_seconds: float | None
    
    # Aquisição
    badge_adopted: bool
    badge_adopted_at: datetime | None
    
    # Valor
    num_claims: int
    num_claims_with_accepted_cites: int
    num_suggestions_accepted: int
    num_suggestions_rejected: int
    
    # Custo
    cpu_hours: float
    estimated_cost_usd: float
    latency_seconds: float
    
    # Qualidade
    quality_score: float | None
    human_evaluation_score: float | None  # se disponível
    nps_reviewer: int | None
    nps_author: int | None
```

### Coleta

- **Eventos**: Log estruturado (JSON) para cada evento significativo
- **Agregação**: Jobs periódicos para calcular métricas agregadas
- **Storage**: Tabela `review_metrics` no banco de dados

### Dashboard (Futuro)

- Visualização de KPIs principais
- Tendências temporais
- Alertas para anomalias

## Roadmap

- [ ] Estrutura de dados para métricas
- [ ] Coleta de eventos
- [ ] Jobs de agregação
- [ ] Dashboard básico
- [ ] Alertas

