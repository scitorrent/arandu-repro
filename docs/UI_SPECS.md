# UI Specifications - Arandu CoReview Studio

## Visão Geral

Interface web minimalista e focada para o fluxo "Review MVP" usando Next.js + Tailwind CSS.

## Páginas

### 1. `/review/submit`

**Objetivo**: Submissão inicial de um paper para review.

**Componentes**:
- Formulário com campos:
  - URL/DOI (text input, required)
  - PDF upload (file input, optional se URL/DOI fornecido)
  - Repo GitHub (text input, optional)
- Botão "Submit Review"
- Loading state durante submissão
- Redirecionamento para `/review/[id]` após sucesso

**Validação**:
- URL/DOI válido ou PDF fornecido
- Feedback visual de erros

### 2. `/review/[id]`

**Objetivo**: Visualização e edição do review em progresso/completo.

**Layout**:
```
┌─────────────────────────────────────────┐
│ Header: Review Status, Score, Tier      │
├─────────────────────────────────────────┤
│ Tabs: Claims | Checklist | Score | Artifacts │
├─────────────────────────────────────────┤
│ Main Content (tab-dependent)            │
│  - Claims: ClaimCard[]                  │
│  - Checklist: ChecklistPanel            │
│  - Score: ScorePanel + NarrationDrawer │
│  - Artifacts: Download links            │
└─────────────────────────────────────────┘
```

**Componentes Principais**:

#### ClaimCard
- Texto do claim (editável inline)
- Seção (badge: intro/method/results/discussion)
- Spans (highlight no texto original)
- Citações sugeridas (top-k com score)
  - Botões: Accept / Edit / Reject
  - Preview de citação (title, authors, venue, year)
- Status visual (accepted/edited/rejected)

#### ChecklistPanel
- Lista de itens:
  - Dados disponíveis
  - Seeds fixos
  - Métricas definidas
  - Ablações reportadas
  - Comparativos com baselines
  - Licença
- Cada item: OK / Missing / Suspect
- Rationale (texto explicativo)
- Visual: checkmarks, warning icons, missing indicators

#### ScorePanel
- Score numérico (0-100) grande e destacado
- Tier badge (A/B/C/D) com cor
- SHAP barplot resumido (top-5 features positivas/negativas)
- Botão "Ver Explicação" → abre NarrationDrawer

#### NarrationDrawer
- Modal/drawer com duas seções:
  - **Executive Justification** (3-5 bullets)
    - Por que o score faz sentido
    - Riscos/viés identificados
    - Actionables para o autor
  - **Technical Deep-dive** (curto)
    - Como cada cluster de features pesou
    - Referências a trechos/artefatos
    - Links para evidências (claim_id, linha README, item checklist)
- Botão "Fechar"

### 3. `/review/[id]/artifacts`

**Objetivo**: Download de artefatos gerados.

**Componentes**:
- Links de download:
  - `report.html` (botão grande)
  - `review.json` (botão)
  - Badges (preview + copiar snippet)
- BadgeTile component:
  - Preview do badge (SVG)
  - Snippet markdown/HTML para copiar
  - Botão "Copy to Clipboard"

### 4. `/jobs` (futuro)

**Objetivo**: Histórico de reviews/jobs.

**Componentes**:
- Tabela com colunas:
  - Paper (title)
  - Status
  - Score/Tier
  - Created date
  - Actions (view, download)
- Filtros: status, tier, date range
- Paginação

## Componentes Reutilizáveis

### BadgeTile
- Props: `type` (claim-mapped, citations-augmented, method-check, score-tier), `reviewId`
- Renderiza preview SVG
- Botão "Copy snippet"
- Toast de confirmação ao copiar

### CopyToClipboard
- Componente utilitário
- Ícone sutil ao lado de código/logs
- Feedback visual ao copiar

### MetaTag / Chip
- Pill-shaped metadata display
- Props: `label`, `value`, `color?`
- Usado para: language, env type, created time

### LogViewer
- Monospace font, small size
- Scrollable area (max-height: 400px)
- Background claro, border sutil
- Botões: "Download full logs", "Copy snippet"
- Distinção visual: system logs vs experiment logs

## Design Tokens

Aplicar tokens do `DESIGN_SYSTEM_V0.md`:
- Cores: moss green (primary), blue (informational)
- Typography: Inter
- Spacing: sistema 4px
- Border radius: `--radius-md` (8px) default
- Shadows: `--shadow-sm` default

## A11y

- Contrastes AA
- Navegação por teclado
- ARIA labels
- Screen reader friendly

## Responsividade

- Mobile-first
- Breakpoints: sm (640px), md (768px), lg (1024px)
- Layout adaptativo (tabs → accordion no mobile)

## Roadmap

- [ ] Implementar `/review/submit`
- [ ] Implementar `/review/[id]` com tabs
- [ ] Implementar ClaimCard
- [ ] Implementar ChecklistPanel
- [ ] Implementar ScorePanel
- [ ] Implementar NarrationDrawer
- [ ] Implementar `/review/[id]/artifacts`
- [ ] Implementar BadgeTile
- [ ] Testes de acessibilidade
- [ ] Testes responsivos

