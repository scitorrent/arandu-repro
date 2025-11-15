# Sprint 2 - Fase 1: DB & Models - Grooming Técnico

## Objetivo
Criar migrations Alembic e modelos SQLAlchemy para as novas tabelas: `papers`, `quality_scores`, `claims`, `claim_links`.

## Especificações Técnicas

### 1. Tabela `papers`

**Propósito**: Armazenar metadados de papers hospedados e controle de visibilidade pública.

**Campos**:
```python
id: UUID (PK, default=uuid4)
title: str | None (nullable, max_length=500)
arxiv_id: str | None (nullable, unique, max_length=100)
repo_url: str | None (nullable, max_length=1000)
pdf_path: str (required, max_length=1000)  # Caminho relativo em PAPERS_BASE
approved_public: bool (default=False, index=True)
created_at: datetime (default=utcnow, index=True)
updated_at: datetime (default=utcnow, onupdate=utcnow)
```

**Constraints**:
- `id` é UUID v4 (primary key)
- `arxiv_id` é único se não-nulo
- `pdf_path` é obrigatório
- `approved_public` indexado para queries de visibilidade

**Relacionamentos**:
- One-to-many: `quality_scores` (um paper pode ter múltiplos scores ao longo do tempo)
- One-to-many: `claims` (um paper tem múltiplos claims)
- Many-to-many via `claim_links`: papers podem estar relacionados via claims

**Índices**:
- `idx_papers_approved_public` em `approved_public`
- `idx_papers_created_at` em `created_at`
- `idx_papers_arxiv_id` em `arxiv_id` (único)

---

### 2. Tabela `quality_scores`

**Propósito**: Armazenar scores de qualidade calculados para papers, com sinais e rationale.

**Campos**:
```python
id: UUID (PK, default=uuid4)
paper_id: UUID (FK → papers.id, required, index=True)
score: int (required, check: 0 <= score <= 100)
signals: JSON (required)  # Dict com sinais extraídos
rationale: JSON (required)  # Dict com explicação do score
version: str (default="v0", max_length=20)  # Versão do modelo/pipe
created_at: datetime (default=utcnow, index=True)
```

**Estrutura JSON `signals`**:
```json
{
  "has_readme_run_steps": bool,
  "has_script_paper_mapping": bool,
  "has_input_example": bool,
  "has_cpu_synthetic_path": bool,
  "has_seeds": bool,
  "has_env_file": bool,
  "readme_quality": int,  // 0-5 heurístico
  "reproducibility_signals_count": int
}
```

**Estrutura JSON `rationale`**:
```json
{
  "summary": str,
  "positive_factors": [str],
  "negative_factors": [str],
  "recommendations": [str]
}
```

**Constraints**:
- `paper_id` é FK obrigatória
- `score` entre 0 e 100 (check constraint)
- `signals` e `rationale` são JSON válidos

**Relacionamentos**:
- Many-to-one: `paper` (FK)

**Índices**:
- `idx_quality_scores_paper_id` em `paper_id`
- `idx_quality_scores_created_at` em `created_at`
- `idx_quality_scores_score` em `score` (para queries de ranking)

---

### 3. Tabela `claims`

**Propósito**: Armazenar claims extraídos de papers.

**Campos**:
```python
id: UUID (PK, default=uuid4)
paper_id: UUID (FK → papers.id, required, index=True)
text: str (required, max_length=5000)
span_start: int | None (nullable)  # Posição no texto original
span_end: int | None (nullable)
section: str | None (nullable, max_length=100)  # intro/method/results/discussion
confidence: float | None (nullable, check: 0.0 <= confidence <= 1.0)
created_at: datetime (default=utcnow, index=True)
```

**Constraints**:
- `paper_id` é FK obrigatória
- `text` é obrigatório
- `span_start` e `span_end` devem ser consistentes (se um existe, o outro também)
- `confidence` entre 0.0 e 1.0 se não-nulo

**Relacionamentos**:
- Many-to-one: `paper` (FK)
- One-to-many: `claim_links` (um claim pode ter múltiplos links)

**Índices**:
- `idx_claims_paper_id` em `paper_id`
- `idx_claims_section` em `section`
- `idx_claims_created_at` em `created_at`

---

### 4. Tabela `claim_links`

**Propósito**: Armazenar relações entre claims e papers/documentos de referência, com classificação de relação.

**Campos**:
```python
id: UUID (PK, default=uuid4)
claim_id: UUID (FK → claims.id, required, index=True)
source_paper_id: UUID | None (FK → papers.id, nullable, index=True)
source_doc_id: str | None (nullable, max_length=200)  # Para docs externos (arXiv ID, DOI, etc.)
source_citation: str | None (nullable, max_length=500)  # Citação textual
relation: str (required, check: relation IN ('equivalent', 'complementary', 'contradictory', 'unclear'))
confidence: float (required, check: 0.0 <= confidence <= 1.0)
context_excerpt: str | None (nullable, max_length=2000)  # Trecho de contexto usado
created_at: datetime (default=utcnow, index=True)
```

**Constraints**:
- `claim_id` é FK obrigatória
- `source_paper_id` ou `source_doc_id` deve ser fornecido (check constraint)
- `relation` é enum: 'equivalent', 'complementary', 'contradictory', 'unclear'
- `confidence` entre 0.0 e 1.0

**Relacionamentos**:
- Many-to-one: `claim` (FK)
- Many-to-one: `source_paper` (FK opcional)

**Índices**:
- `idx_claim_links_claim_id` em `claim_id`
- `idx_claim_links_source_paper_id` em `source_paper_id`
- `idx_claim_links_relation` em `relation`
- `idx_claim_links_confidence` em `confidence`

---

## Relacionamentos entre Tabelas

```
papers (1) ──< (N) quality_scores
papers (1) ──< (N) claims
claims (1) ──< (N) claim_links
papers (1) ──< (N) claim_links [source_paper_id]
```

**Nota**: `claim_links` pode referenciar papers internos (`source_paper_id`) ou documentos externos (`source_doc_id`).

---

## Migrations Alembic

### Migration 1: `add_papers_table`
- Criar tabela `papers`
- Adicionar índices
- Adicionar constraints

### Migration 2: `add_quality_scores_table`
- Criar tabela `quality_scores`
- Adicionar FK para `papers`
- Adicionar check constraint para `score`
- Adicionar índices

### Migration 3: `add_claims_table`
- Criar tabela `claims`
- Adicionar FK para `papers`
- Adicionar check constraint para `confidence`
- Adicionar índices

### Migration 4: `add_claim_links_table`
- Criar tabela `claim_links`
- Adicionar FKs para `claims` e `papers`
- Adicionar check constraints para `relation` e `confidence`
- Adicionar constraint: `source_paper_id` OU `source_doc_id` deve existir
- Adicionar índices

**Ordem de execução**: 1 → 2 → 3 → 4 (respeitando dependências de FK)

---

## Modelos SQLAlchemy

### Estrutura de Arquivos
```
backend/app/models/
├── __init__.py
├── paper.py          # Novo
├── quality_score.py  # Novo
├── claim.py          # Novo
├── claim_link.py     # Novo
├── job.py            # Existente
├── review.py         # Existente
└── ...
```

### Modelo `Paper`
```python
from sqlalchemy import Column, String, Boolean, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base
import uuid
from datetime import datetime, UTC

class Paper(Base):
    __tablename__ = "papers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=True)
    arxiv_id = Column(String(100), nullable=True, unique=True)
    repo_url = Column(String(1000), nullable=True)
    pdf_path = Column(String(1000), nullable=False)
    approved_public = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)
    
    # Relationships
    quality_scores = relationship("QualityScore", back_populates="paper", cascade="all, delete-orphan")
    claims = relationship("Claim", back_populates="paper", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_papers_approved_public", "approved_public"),
        Index("idx_papers_created_at", "created_at"),
    )
```

### Modelo `QualityScore`
```python
from sqlalchemy import Column, Integer, JSON, String, DateTime, ForeignKey, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base
import uuid
from datetime import datetime, UTC

class QualityScore(Base):
    __tablename__ = "quality_scores"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    paper_id = Column(UUID(as_uuid=True), ForeignKey("papers.id", ondelete="CASCADE"), nullable=False, index=True)
    score = Column(Integer, nullable=False)
    signals = Column(JSON, nullable=False)
    rationale = Column(JSON, nullable=False)
    version = Column(String(20), default="v0", nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False, index=True)
    
    # Relationships
    paper = relationship("Paper", back_populates="quality_scores")
    
    __table_args__ = (
        CheckConstraint("score >= 0 AND score <= 100", name="check_score_range"),
        Index("idx_quality_scores_paper_id", "paper_id"),
        Index("idx_quality_scores_created_at", "created_at"),
        Index("idx_quality_scores_score", "score"),
    )
```

### Modelo `Claim`
```python
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base
import uuid
from datetime import datetime, UTC

class Claim(Base):
    __tablename__ = "claims"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    paper_id = Column(UUID(as_uuid=True), ForeignKey("papers.id", ondelete="CASCADE"), nullable=False, index=True)
    text = Column(String(5000), nullable=False)
    span_start = Column(Integer, nullable=True)
    span_end = Column(Integer, nullable=True)
    section = Column(String(100), nullable=True, index=True)
    confidence = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False, index=True)
    
    # Relationships
    paper = relationship("Paper", back_populates="claims")
    claim_links = relationship("ClaimLink", back_populates="claim", cascade="all, delete-orphan")
    
    __table_args__ = (
        CheckConstraint(
            "(span_start IS NULL AND span_end IS NULL) OR (span_start IS NOT NULL AND span_end IS NOT NULL)",
            name="check_span_consistency"
        ),
        CheckConstraint(
            "confidence IS NULL OR (confidence >= 0.0 AND confidence <= 1.0)",
            name="check_confidence_range"
        ),
        Index("idx_claims_paper_id", "paper_id"),
        Index("idx_claims_section", "section"),
        Index("idx_claims_created_at", "created_at"),
    )
```

### Modelo `ClaimLink`
```python
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base
import uuid
from datetime import datetime, UTC

class ClaimLink(Base):
    __tablename__ = "claim_links"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id = Column(UUID(as_uuid=True), ForeignKey("claims.id", ondelete="CASCADE"), nullable=False, index=True)
    source_paper_id = Column(UUID(as_uuid=True), ForeignKey("papers.id", ondelete="SET NULL"), nullable=True, index=True)
    source_doc_id = Column(String(200), nullable=True)  # arXiv ID, DOI, etc.
    source_citation = Column(String(500), nullable=True)
    relation = Column(String(50), nullable=False)  # equivalent, complementary, contradictory, unclear
    confidence = Column(Float, nullable=False)
    context_excerpt = Column(String(2000), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False, index=True)
    
    # Relationships
    claim = relationship("Claim", back_populates="claim_links")
    source_paper = relationship("Paper", foreign_keys=[source_paper_id])
    
    __table_args__ = (
        CheckConstraint(
            "source_paper_id IS NOT NULL OR source_doc_id IS NOT NULL",
            name="check_source_exists"
        ),
        CheckConstraint(
            "relation IN ('equivalent', 'complementary', 'contradictory', 'unclear')",
            name="check_relation_valid"
        ),
        CheckConstraint(
            "confidence >= 0.0 AND confidence <= 1.0",
            name="check_confidence_range"
        ),
        Index("idx_claim_links_claim_id", "claim_id"),
        Index("idx_claim_links_source_paper_id", "source_paper_id"),
        Index("idx_claim_links_relation", "relation"),
        Index("idx_claim_links_confidence", "confidence"),
    )
```

---

## Schemas Pydantic

### Estrutura de Arquivos
```
backend/app/schemas/
├── __init__.py
├── paper.py          # Novo
├── quality_score.py  # Novo
├── claim.py          # Novo
├── claim_link.py     # Novo
├── job.py            # Existente
├── review.py         # Existente
└── ...
```

### Schema `Paper`
```python
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional

class PaperBase(BaseModel):
    title: Optional[str] = Field(None, max_length=500)
    arxiv_id: Optional[str] = Field(None, max_length=100)
    repo_url: Optional[str] = Field(None, max_length=1000)
    pdf_path: str = Field(..., max_length=1000)

class PaperCreate(PaperBase):
    pass

class PaperUpdate(BaseModel):
    title: Optional[str] = None
    arxiv_id: Optional[str] = None
    repo_url: Optional[str] = None
    approved_public: Optional[bool] = None

class Paper(PaperBase):
    id: UUID
    approved_public: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class PaperWithRelations(Paper):
    quality_scores: list["QualityScore"] = []
    claims: list["Claim"] = []
```

### Schema `QualityScore`
```python
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Dict, Any

class QualityScoreSignals(BaseModel):
    has_readme_run_steps: bool
    has_script_paper_mapping: bool
    has_input_example: bool
    has_cpu_synthetic_path: bool
    has_seeds: bool
    has_env_file: bool
    readme_quality: int = Field(..., ge=0, le=5)
    reproducibility_signals_count: int = Field(..., ge=0)

class QualityScoreRationale(BaseModel):
    summary: str
    positive_factors: list[str]
    negative_factors: list[str]
    recommendations: list[str]

class QualityScoreBase(BaseModel):
    score: int = Field(..., ge=0, le=100)
    signals: Dict[str, Any]
    rationale: Dict[str, Any]
    version: str = "v0"

class QualityScoreCreate(QualityScoreBase):
    paper_id: UUID

class QualityScore(QualityScoreBase):
    id: UUID
    paper_id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True
```

### Schema `Claim`
```python
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional

class ClaimBase(BaseModel):
    text: str = Field(..., max_length=5000)
    span_start: Optional[int] = None
    span_end: Optional[int] = None
    section: Optional[str] = Field(None, max_length=100)
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)

class ClaimCreate(ClaimBase):
    paper_id: UUID

class Claim(ClaimBase):
    id: UUID
    paper_id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True
```

### Schema `ClaimLink`
```python
from pydantic import BaseModel, Field, field_validator
from uuid import UUID
from datetime import datetime
from typing import Optional, Literal

class ClaimLinkBase(BaseModel):
    source_paper_id: Optional[UUID] = None
    source_doc_id: Optional[str] = Field(None, max_length=200)
    source_citation: Optional[str] = Field(None, max_length=500)
    relation: Literal["equivalent", "complementary", "contradictory", "unclear"]
    confidence: float = Field(..., ge=0.0, le=1.0)
    context_excerpt: Optional[str] = Field(None, max_length=2000)
    
    @field_validator("source_paper_id", "source_doc_id")
    @classmethod
    def validate_source(cls, v, info):
        if not v and not info.data.get("source_paper_id") and not info.data.get("source_doc_id"):
            raise ValueError("Either source_paper_id or source_doc_id must be provided")
        return v

class ClaimLinkCreate(ClaimLinkBase):
    claim_id: UUID

class ClaimLink(ClaimLinkBase):
    id: UUID
    claim_id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True
```

---

## Ordem de Implementação

1. **Criar modelos SQLAlchemy** (`paper.py`, `quality_score.py`, `claim.py`, `claim_link.py`)
2. **Atualizar `__init__.py`** para exportar novos modelos
3. **Criar migrations Alembic** (4 migrations na ordem: papers → quality_scores → claims → claim_links)
4. **Criar schemas Pydantic** (`paper.py`, `quality_score.py`, `claim.py`, `claim_link.py`)
5. **Atualizar `__init__.py`** dos schemas
6. **Testar migrations** (up/down)
7. **Testar modelos** (CRUD básico)

---

## Critérios de Aceite Técnicos

- [ ] 4 migrations criadas e testadas (up/down)
- [ ] 4 modelos SQLAlchemy criados com relacionamentos corretos
- [ ] Constraints e índices aplicados corretamente
- [ ] Schemas Pydantic criados com validações
- [ ] Testes unitários para modelos (CRUD básico)
- [ ] Testes de integridade referencial (cascade deletes)
- [ ] Documentação inline (docstrings nos modelos)

---

## Testes Sugeridos

### Testes Unitários
```python
# test_models_paper.py
- test_create_paper()
- test_paper_with_quality_scores()
- test_paper_with_claims()
- test_paper_cascade_delete()

# test_models_quality_score.py
- test_create_quality_score()
- test_score_range_validation()
- test_signals_json_structure()

# test_models_claim.py
- test_create_claim()
- test_span_consistency()
- test_confidence_range()

# test_models_claim_link.py
- test_create_claim_link()
- test_source_validation()
- test_relation_enum()
```

### Testes de Migrations
```python
# test_migrations.py
- test_papers_table_created()
- test_quality_scores_table_created()
- test_claims_table_created()
- test_claim_links_table_created()
- test_foreign_keys()
- test_indexes()
- test_constraints()
```

---

## Notas de Implementação

1. **UUIDs**: Usar `UUID(as_uuid=True)` no SQLAlchemy para compatibilidade com PostgreSQL e SQLite
2. **JSON Fields**: Usar `JSON` do SQLAlchemy (PostgreSQL) ou `Text` com serialização JSON (SQLite fallback)
3. **Timezones**: Sempre usar `timezone=True` em `DateTime` e `datetime.now(UTC)`
4. **Cascade Deletes**: Papers deletam quality_scores e claims; claims deletam claim_links
5. **Check Constraints**: Validar no banco e no Pydantic (defesa em profundidade)

---

## Dependências Externas

- SQLAlchemy 2.0+
- Alembic
- Pydantic 2.0+
- PostgreSQL (produção) ou SQLite (dev/test)

---

## Próximos Passos (Após Fase 1)

- Fase 2: Storage/Config (configurar `PAPERS_BASE`, upload de PDF)
- Fase 3: APIs (endpoints `/papers` usando os modelos criados)

