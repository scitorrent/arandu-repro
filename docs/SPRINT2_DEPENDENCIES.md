# Sprint 2 - Análise de Dependências entre PRs

## Dependências Identificadas

### PR #1: Foundation ✅
- **Dependências:** Nenhuma (base)
- **Usado por:** Todos os outros PRs

### PR #2: Ingestion & Claims ✅
- **Dependências:** PR #1
- **Usado por:** PR #3, #4, #5, #6, #7, #8
- **Status:** Implementado

### PR #3: RAG Pipeline (skeleton) ✅
- **Dependências:** PR #1, #2 (usa claims)
- **Usado por:** PR #5, #7, #8
- **Status:** Implementado (skeleton, precisa corpus)

### PR #4: Method Checklist ✅
- **Dependências:** PR #1, #2 (usa claims)
- **Usado por:** PR #5, #6, #7, #8
- **Status:** Implementado

### PR #5: Quality Score + SHAP ✅
- **Dependências:** PR #1, #2, #3, #4 (usa claims, citations, checklist)
- **Usado por:** PR #6, #7, #8
- **Status:** Implementado

### PR #6: Badges 🔄
- **Dependências:** PR #1, #2, #4, #5 (usa claims, checklist, quality score)
- **Usado por:** PR #7, #8
- **Status:** Pendente

### PR #7: Reports 🔄
- **Dependências:** PR #1, #2, #3, #4, #5, #6 (usa tudo)
- **Usado por:** PR #8, #9
- **Status:** Pendente

### PR #8: LangGraph Pipeline 🔄
- **Dependências:** PR #1, #2, #3, #4, #5, #6, #7 (integra tudo)
- **Usado por:** PR #9
- **Status:** Pendente

### PR #9: UI Next.js 🔄
- **Dependências:** PR #8 (consome pipeline)
- **Usado por:** PR #11
- **Status:** Pendente

### PR #10: Telemetria 🔄
- **Dependências:** PR #1 (pode ser paralelo)
- **Usado por:** Nenhum (independente)
- **Status:** Pendente

### PR #11: E2E Tests 🔄
- **Dependências:** Todos os anteriores
- **Usado por:** Nenhum (validação final)
- **Status:** Pendente

## Estratégia Recomendada

### Opção A: Continuar no mesmo branch (Recomendado para Sprint)
**Vantagens:**
- ✅ Desenvolvimento rápido, sem overhead de múltiplos PRs
- ✅ Testes integrados desde o início
- ✅ Menos conflitos de merge
- ✅ Alinhado com "single PR" mencionado no plano original

**Desvantagens:**
- ⚠️ PR grande no final (mas pode ser dividido em commits lógicos)
- ⚠️ Revisão mais complexa no final

**Ação:**
1. Continuar implementando PRs #6-11 no mesmo branch
2. Fazer commits separados por funcionalidade
3. No final, criar 1 PR grande ou dividir em 2-3 PRs menores:
   - PR A: Backend core (#1-5) ✅ já feito
   - PR B: Artefatos (#6-7)
   - PR C: Pipeline + UI (#8-9)
   - PR D: Telemetria + Tests (#10-11)

### Opção B: Criar PRs separados agora
**Vantagens:**
- ✅ Revisões incrementais
- ✅ Merge gradual

**Desvantagens:**
- ⚠️ Overhead de criar branches/PRs
- ⚠️ Dependências bloqueiam desenvolvimento
- ⚠️ Mais complexo para sprint focada

**Ação:**
1. Fazer PR do que já está (#1-5)
2. Criar branches separados para #6-11
3. Mergear conforme dependências resolvidas

## Recomendação Final

**Continuar no mesmo branch e fazer PR único no final** (Opção A), porque:

1. **Sprint focada:** O plano original menciona "1 PR único: `feat(review): Sprint 2 — review MVP`"
2. **Dependências claras:** PRs #6-11 dependem fortemente dos anteriores
3. **Testes integrados:** Melhor validar tudo junto
4. **Velocidade:** Menos overhead administrativo

**Estrutura de commits sugerida:**
```
feat(review): Sprint 2 — review MVP

- PR #1: Foundation (review model, API, migration)
- PR #2: Ingestion & Claims
- PR #3: RAG Pipeline skeleton
- PR #4: Method Checklist
- PR #5: Quality Score + SHAP
- PR #6: Badges
- PR #7: Reports
- PR #8: LangGraph Pipeline (opcional, pode ser simplificado)
- PR #9: UI Next.js
- PR #10: Telemetria
- PR #11: E2E Tests
```

## Próximos Passos

1. ✅ **Continuar implementando** PRs #6-11 no mesmo branch
2. ✅ **Fazer commits separados** por funcionalidade
3. ✅ **No final, revisar e criar PR** (único ou dividido em 2-3)
4. ✅ **Testar end-to-end** antes de merge

## Nota sobre LangGraph (PR #8)

O PR #8 (LangGraph Pipeline) pode ser **opcional** ou **simplificado**:
- O pipeline atual já funciona sem LangGraph (chamadas diretas)
- LangGraph adiciona orquestração, mas não é crítico para MVP
- Pode ser adiado para v0.3 se necessário

