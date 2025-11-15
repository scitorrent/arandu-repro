# Sprint 2 - Fase 1: DB & Models - Grooming Técnico (Atualizado)

## Objetivo
Criar migrations Alembic e modelos SQLAlchemy para as novas tabelas: `papers`, `paper_versions`, `paper_external_ids`, `quality_scores`, `claims`, `claim_links`.

## Mudanças Principais

- **AID + Versionamento**: `papers` usa `aid` (TEXT UNIQUE) como identificador estável; `paper_versions` para versionamento
- **Visibilidade**: `visibility ENUM` + `approved_public_at` em vez de `approved_public BOOL`
- **IDs Externos Normalizados**: Tabela `paper_external_ids` para múltiplos tipos de IDs
- **Quality Scores Ancorados**: `scope` ENUM e `paper_version_id` opcional
- **Claims Ancorados à Versão**: `paper_version_id` obrigatório
- **Soft Delete**: `deleted_at` em papers e paper_versions

---

## Especificações Técnicas

### 1. Tabela `papers`

**Propósito**: Armazenar metadados de papers hospedados e controle de visibilidade pública.

**Campos**:
```python
id: UUID (PK, default=uuid4)
aid: TEXT (UNIQUE, required, index=True)  # Identificador estável (ULID/slug)
title: str | None (nullable, max_length=500)
repo_url: str | None (nullable, max_length=1000)
visibility: ENUM('private', 'unlisted', 'public') (default='private', index=True)
license: str | None (nullable, max_length=200)
created_by: str | None (nullable, max_length=200)  # Stub até auth
created_at: datetime (default=utcnow, index=True)
updated_at: datetime (default=utcnow, onupdate=utcnow)
approved_public_at: datetime | None (nullable, index=True)
deleted_at: datetime | None (nullable, index=True)  # Soft delete
```

**Constraints**:
- `id` é UUID v4 (primary key)
- `aid` é único e obrigatório (identificador estável)
- `visibility` é ENUM: 'private', 'unlisted', 'public'
- `deleted_at` para soft delete

**Relacionamentos**:
- One-to-many: `paper_versions` (um paper tem múltiplas versões)
- One-to-many: `paper_external_ids` (um paper tem múltiplos IDs externos)
- One-to-many: `quality_scores` (um paper pode ter múltiplos scores ao longo do tempo)
- Many-to-many via `claim_links`: papers podem estar relacionados via claims

**Índices**:
- `idx_papers_aid` em `aid` (único)
- `idx_papers_visibility` em `visibility`
- `idx_papers_created_at` em `created_at`
- `idx_papers_approved_public_at` em `approved_public_at`
- `idx_papers_deleted_at` em `deleted_at`

**Nota**: `pdf_path` removido de `papers` (agora em `paper_versions`).

---

### 2. Tabela `paper_versions`

**Propósito**: Versionamento de papers (PDF, metadados por versão).

**Campos**:
```python
id: UUID (PK, default=uuid4)
aid: TEXT (FK → papers.aid, required, index=True)
version: INT (required, check: version >= 1)
pdf_path: str (required, max_length=1000)  # Relativo a PAPERS_BASE/{aid}/v{version}/file.pdf
meta_json: JSON (nullable)  # Metadados específicos da versão
created_at: datetime (default=utcnow, index=True)
deleted_at: datetime | None (nullable, index=True)  # Soft delete
```

**Constraints**:
- `aid` é FK obrigatória para `papers.aid`
- `version` >= 1
- `UNIQUE(aid, version)` - uma versão única por paper
- `pdf_path` é obrigatório e relativo a `PAPERS_BASE/{aid}/v{version}/file.pdf`

**Relacionamentos**:
- Many-to-one: `paper` (FK via `aid`)
- One-to-many: `quality_scores` (scores podem ser ancorados a versão)
- One-to-many: `claims` (claims ancorados à versão)

**Índices**:
- `idx_paper_versions_aid_version` em `(aid, version)` (único)
- `idx_paper_versions_aid` em `aid`
- `idx_paper_versions_created_at` em `created_at`
- `idx_paper_versions_deleted_at` em `deleted_at`

---

### 3. Tabela `paper_external_ids`

**Propósito**: Normalizar IDs externos (DOI, arXiv, PMID, URL) de papers.

**Campos**:
```python
id: UUID (PK, default=uuid4)
paper_id: UUID (FK → papers.id, required, index=True)
kind: ENUM('doi', 'arxiv', 'pmid', 'url') (required)
value: TEXT (required, max_length=500)
created_at: datetime (default=utcnow)
```

**Constraints**:
- `paper_id` é FK obrigatória
- `kind` é ENUM: 'doi', 'arxiv', 'pmid', 'url'
- `value` é obrigatório
- `UNIQUE(paper_id, kind)` - um tipo de ID único por paper

**Relacionamentos**:
- Many-to-one: `paper` (FK)

**Índices**:
- `idx_paper_external_ids_paper_id_kind` em `(paper_id, kind)` (único)
- `idx_paper_external_ids_kind_value` em `(kind, value)` (para buscas rápidas)

**Nota Opcional**: Manter `arxiv_id` como coluna denormalizada em `papers` + índice para consultas rápidas (não implementado inicialmente).

---

### 4. Tabela `quality_scores`

**Propósito**: Armazenar scores de qualidade calculados para papers ou versões, com sinais e rationale.

**Campos**:
```python
id: UUID (PK, default=uuid4)
paper_id: UUID | None (FK → papers.id, nullable, index=True)
paper_version_id: UUID | None (FK → paper_versions.id, nullable, index=True)
scope: ENUM('paper', 'version') (required)
score: int (required, check: 0 <= score <= 100)
signals: JSON (required)  # Dict com sinais extraídos
rationale: JSON (required)  # Dict com explicação do score
scoring_model_version: str (default="v0", max_length=20)  # Versão do modelo/pipe
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
- `scope` é ENUM: 'paper' ou 'version'
- **Check constraint**: `(scope='paper' AND paper_id IS NOT NULL AND paper_version_id IS NULL) OR (scope='version' AND paper_version_id IS NOT NULL AND paper_id IS NULL)`
- `score` entre 0 e 100 (check constraint)
- `signals` e `rationale` são JSON válidos

**Relacionamentos**:
- Many-to-one: `paper` (FK opcional, se `scope='paper'`)
- Many-to-one: `paper_version` (FK opcional, se `scope='version'`)

**Índices**:
- `idx_quality_scores_paper_id` em `paper_id`
- `idx_quality_scores_paper_version_id` em `paper_version_id`
- `idx_quality_scores_scope` em `scope`
- `idx_quality_scores_created_at` em `created_at`
- `idx_quality_scores_score` em `score` (para queries de ranking)

---

### 5. Tabela `claims`

**Propósito**: Armazenar claims extraídos de papers (ancorados à versão).

**Campos**:
```python
id: UUID (PK, default=uuid4)
paper_version_id: UUID (FK → paper_versions.id, required, index=True)
paper_id: UUID (FK → papers.id, nullable, index=True)  # GENERATED para join rápido (opcional)
text: str (required, max_length=5000)
span_start: int | None (nullable)  # Posição no texto original
span_end: int | None (nullable)
page: int | None (nullable)  # Página do PDF
bbox: JSON | None (nullable)  # Bounding box no PDF {x, y, width, height}
section: str | None (nullable, max_length=100, index=True)  # intro/method/results/discussion
confidence: float | None (nullable, check: 0.0 <= confidence <= 1.0)
extraction_model_version: str | None (nullable, max_length=50)  # Versão do modelo de extração
hash: str (UNIQUE, required, max_length=64)  # Hash do text+span+version para dedupe
created_at: datetime (default=utcnow, index=True)
```

**Constraints**:
- `paper_version_id` é FK obrigatória
- `text` é obrigatório
- `span_start` e `span_end` devem ser consistentes (se um existe, o outro também)
- `confidence` entre 0.0 e 1.0 se não-nulo
- `hash` é único (para dedupe)

**Relacionamentos**:
- Many-to-one: `paper_version` (FK obrigatória)
- Many-to-one: `paper` (FK opcional, para join rápido)
- One-to-many: `claim_links` (um claim pode ter múltiplos links)

**Índices**:
- `idx_claims_paper_version_id` em `paper_version_id`
- `idx_claims_paper_version_section` em `(paper_version_id, section)`
- `idx_claims_paper_id` em `paper_id`
- `idx_claims_section` em `section`
- `idx_claims_hash` em `hash` (único)
- `idx_claims_created_at` em `created_at`
- **GIN/trigram em `text`** (PostgreSQL) se disponível para busca full-text

---

### 6. Tabela `claim_links`

**Propósito**: Armazenar relações entre claims e papers/documentos de referência, com classificação de relação.

**Campos**:
```python
id: UUID (PK, default=uuid4)
claim_id: UUID (FK → claims.id, required, index=True)
source_paper_id: UUID | None (FK → papers.id, nullable, index=True)
source_doc_id: str | None (nullable, max_length=200)  # Para docs externos (arXiv ID, DOI, etc.)
source_citation: str | None (nullable, max_length=500)  # Citação textual
relation: ENUM('equivalent', 'complementary', 'contradictory', 'unclear') (required, index=True)
confidence: float (required, check: 0.0 <= confidence <= 1.0)
context_excerpt: str | None (nullable, max_length=2000)  # Trecho de contexto usado
reasoning_ref: str | None (nullable, max_length=500)  # Path para trace/justificativa do agente
created_at: datetime (default=utcnow, index=True)
```

**Constraints**:
- `claim_id` é FK obrigatória
- **Check constraint**: `source_paper_id IS NOT NULL OR source_doc_id IS NOT NULL`
- `relation` é ENUM: 'equivalent', 'complementary', 'contradictory', 'unclear'
- `confidence` entre 0.0 e 1.0
- **UNIQUE(claim_id, COALESCE(source_paper_id::text, source_doc_id), relation)** - um link único por claim+fonte+relação

**Relacionamentos**:
- Many-to-one: `claim` (FK)
- Many-to-one: `source_paper` (FK opcional)

**Índices**:
- `idx_claim_links_claim_id` em `claim_id`
- `idx_claim_links_source_paper_id` em `source_paper_id`
- `idx_claim_links_relation` em `relation`
- `idx_claim_links_confidence` em `confidence`
- `idx_claim_links_unique` em `(claim_id, COALESCE(source_paper_id::text, source_doc_id), relation)` (único)

---

## Relacionamentos entre Tabelas

```
papers (1) ──< (N) paper_versions
papers (1) ──< (N) paper_external_ids
papers (1) ──< (N) quality_scores [scope='paper']
paper_versions (1) ──< (N) quality_scores [scope='version']
paper_versions (1) ──< (N) claims
claims (1) ──< (N) claim_links
papers (1) ──< (N) claim_links [source_paper_id]
```

**Nota**: `claim_links` pode referenciar papers internos (`source_paper_id`) ou documentos externos (`source_doc_id`).

---

## Migrations Alembic

### Migration 1: `add_papers_table`
- Criar tabela `papers`
- Criar ENUM `paper_visibility` ('private', 'unlisted', 'public')
- Adicionar índices
- Adicionar constraints

### Migration 2: `add_paper_versions_table`
- Criar tabela `paper_versions`
- Adicionar FK para `papers.aid`
- Adicionar constraint UNIQUE(aid, version)
- Adicionar índices

### Migration 3: `add_paper_external_ids_table`
- Criar tabela `paper_external_ids`
- Criar ENUM `external_id_kind` ('doi', 'arxiv', 'pmid', 'url')
- Adicionar FK para `papers.id`
- Adicionar constraint UNIQUE(paper_id, kind)
- Adicionar índices

### Migration 4: `add_quality_scores_table`
- Criar tabela `quality_scores`
- Criar ENUM `quality_score_scope` ('paper', 'version')
- Adicionar FKs condicionais para `papers` e `paper_versions`
- Adicionar check constraint para `scope` e FKs
- Adicionar check constraint para `score`
- Adicionar índices

### Migration 5: `add_claims_table`
- Criar tabela `claims`
- Adicionar FK obrigatória para `paper_versions.id`
- Adicionar FK opcional para `papers.id` (para join rápido)
- Adicionar check constraints para `span_consistency` e `confidence`
- Adicionar constraint UNIQUE em `hash`
- Adicionar índices (incluindo GIN/trigram em `text` se PostgreSQL)

### Migration 6: `add_claim_links_table`
- Criar tabela `claim_links`
- Criar ENUM `claim_relation` ('equivalent', 'complementary', 'contradictory', 'unclear')
- Adicionar FK para `claims.id`
- Adicionar FK opcional para `papers.id`
- Adicionar check constraints para `source_exists` e `confidence`
- Adicionar constraint UNIQUE(claim_id, COALESCE(source_paper_id::text, source_doc_id), relation)
- Adicionar índices

**Ordem de execução**: 1 → 2 → 3 → 4 → 5 → 6 (respeitando dependências de FK)

---

## Modelos SQLAlchemy

### Estrutura de Arquivos
```
backend/app/models/
├── __init__.py
├── paper.py              # Novo
├── paper_version.py      # Novo
├── paper_external_id.py  # Novo
├── quality_score.py      # Novo
├── claim.py              # Novo
├── claim_link.py         # Novo
├── job.py                # Existente
├── review.py             # Existente
└── ...
```

### Modelo `Paper`
```python
from sqlalchemy import Column, String, DateTime, Index, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base
import uuid
from datetime import datetime, UTC
import enum

class PaperVisibility(str, enum.Enum):
    PRIVATE = "private"
    UNLISTED = "unlisted"
    PUBLIC = "public"

class Paper(Base):
    __tablename__ = "papers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    aid = Column(String, unique=True, nullable=False, index=True)  # Identificador estável
    title = Column(String(500), nullable=True)
    repo_url = Column(String(1000), nullable=True)
    visibility = Column(SQLEnum(PaperVisibility), default=PaperVisibility.PRIVATE, nullable=False, index=True)
    license = Column(String(200), nullable=True)
    created_by = Column(String(200), nullable=True)  # Stub até auth
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)
    approved_public_at = Column(DateTime(timezone=True), nullable=True, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)  # Soft delete
    
    # Relationships
    versions = relationship("PaperVersion", back_populates="paper", cascade="all, delete-orphan")
    external_ids = relationship("PaperExternalId", back_populates="paper", cascade="all, delete-orphan")
    quality_scores = relationship("QualityScore", back_populates="paper", foreign_keys="QualityScore.paper_id", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_papers_aid", "aid", unique=True),
        Index("idx_papers_visibility", "visibility"),
        Index("idx_papers_created_at", "created_at"),
        Index("idx_papers_approved_public_at", "approved_public_at"),
        Index("idx_papers_deleted_at", "deleted_at"),
    )
```

### Modelo `PaperVersion`
```python
from sqlalchemy import Column, String, Integer, JSON, DateTime, ForeignKey, Index, UniqueConstraint, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base
import uuid
from datetime import datetime, UTC

class PaperVersion(Base):
    __tablename__ = "paper_versions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    aid = Column(String, ForeignKey("papers.aid", ondelete="CASCADE"), nullable=False, index=True)
    version = Column(Integer, nullable=False)
    pdf_path = Column(String(1000), nullable=False)  # Relativo a PAPERS_BASE/{aid}/v{version}/file.pdf
    meta_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)  # Soft delete
    
    # Relationships
    paper = relationship("Paper", back_populates="versions", foreign_keys=[aid])
    quality_scores = relationship("QualityScore", back_populates="paper_version", foreign_keys="QualityScore.paper_version_id", cascade="all, delete-orphan")
    claims = relationship("Claim", back_populates="paper_version", cascade="all, delete-orphan")
    
    __table_args__ = (
        UniqueConstraint("aid", "version", name="uq_paper_versions_aid_version"),
        CheckConstraint("version >= 1", name="check_version_positive"),
        Index("idx_paper_versions_aid", "aid"),
        Index("idx_paper_versions_created_at", "created_at"),
        Index("idx_paper_versions_deleted_at", "deleted_at"),
    )
```

### Modelo `PaperExternalId`
```python
from sqlalchemy import Column, String, DateTime, ForeignKey, Index, UniqueConstraint, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base
import uuid
from datetime import datetime, UTC
import enum

class ExternalIdKind(str, enum.Enum):
    DOI = "doi"
    ARXIV = "arxiv"
    PMID = "pmid"
    URL = "url"

class PaperExternalId(Base):
    __tablename__ = "paper_external_ids"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    paper_id = Column(UUID(as_uuid=True), ForeignKey("papers.id", ondelete="CASCADE"), nullable=False, index=True)
    kind = Column(SQLEnum(ExternalIdKind), nullable=False)
    value = Column(String(500), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    
    # Relationships
    paper = relationship("Paper", back_populates="external_ids")
    
    __table_args__ = (
        UniqueConstraint("paper_id", "kind", name="uq_paper_external_ids_paper_kind"),
        Index("idx_paper_external_ids_kind_value", "kind", "value"),
    )
```

### Modelo `QualityScore`
```python
from sqlalchemy import Column, Integer, JSON, String, DateTime, ForeignKey, Index, CheckConstraint, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base
import uuid
from datetime import datetime, UTC
import enum

class QualityScoreScope(str, enum.Enum):
    PAPER = "paper"
    VERSION = "version"

class QualityScore(Base):
    __tablename__ = "quality_scores"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    paper_id = Column(UUID(as_uuid=True), ForeignKey("papers.id", ondelete="CASCADE"), nullable=True, index=True)
    paper_version_id = Column(UUID(as_uuid=True), ForeignKey("paper_versions.id", ondelete="CASCADE"), nullable=True, index=True)
    scope = Column(SQLEnum(QualityScoreScope), nullable=False, index=True)
    score = Column(Integer, nullable=False)
    signals = Column(JSON, nullable=False)
    rationale = Column(JSON, nullable=False)
    scoring_model_version = Column(String(20), default="v0", nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False, index=True)
    
    # Relationships
    paper = relationship("Paper", back_populates="quality_scores", foreign_keys=[paper_id])
    paper_version = relationship("PaperVersion", back_populates="quality_scores", foreign_keys=[paper_version_id])
    
    __table_args__ = (
        CheckConstraint(
            "(scope = 'paper' AND paper_id IS NOT NULL AND paper_version_id IS NULL) OR "
            "(scope = 'version' AND paper_version_id IS NOT NULL AND paper_id IS NULL)",
            name="check_quality_score_scope"
        ),
        CheckConstraint("score >= 0 AND score <= 100", name="check_score_range"),
        Index("idx_quality_scores_paper_id", "paper_id"),
        Index("idx_quality_scores_paper_version_id", "paper_version_id"),
        Index("idx_quality_scores_scope", "scope"),
        Index("idx_quality_scores_created_at", "created_at"),
        Index("idx_quality_scores_score", "score"),
    )
```

### Modelo `Claim`
```python
from sqlalchemy import Column, String, Integer, Float, JSON, DateTime, ForeignKey, Index, CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base
import uuid
from datetime import datetime, UTC

class Claim(Base):
    __tablename__ = "claims"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    paper_version_id = Column(UUID(as_uuid=True), ForeignKey("paper_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    paper_id = Column(UUID(as_uuid=True), ForeignKey("papers.id", ondelete="CASCADE"), nullable=True, index=True)  # Para join rápido
    text = Column(String(5000), nullable=False)
    span_start = Column(Integer, nullable=True)
    span_end = Column(Integer, nullable=True)
    page = Column(Integer, nullable=True)  # Página do PDF
    bbox = Column(JSON, nullable=True)  # Bounding box {x, y, width, height}
    section = Column(String(100), nullable=True, index=True)
    confidence = Column(Float, nullable=True)
    extraction_model_version = Column(String(50), nullable=True)
    hash = Column(String(64), unique=True, nullable=False)  # Hash para dedupe
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False, index=True)
    
    # Relationships
    paper_version = relationship("PaperVersion", back_populates="claims", foreign_keys=[paper_version_id])
    paper = relationship("Paper", foreign_keys=[paper_id])
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
        UniqueConstraint("hash", name="uq_claims_hash"),
        Index("idx_claims_paper_version_id", "paper_version_id"),
        Index("idx_claims_paper_version_section", "paper_version_id", "section"),
        Index("idx_claims_paper_id", "paper_id"),
        Index("idx_claims_section", "section"),
        Index("idx_claims_hash", "hash", unique=True),
        Index("idx_claims_created_at", "created_at"),
        # GIN/trigram em text (PostgreSQL) - adicionar via migration separada se necessário
    )
```

### Modelo `ClaimLink`
```python
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Index, CheckConstraint, UniqueConstraint, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy import func
from app.db.base import Base
import uuid
from datetime import datetime, UTC
import enum

class ClaimRelation(str, enum.Enum):
    EQUIVALENT = "equivalent"
    COMPLEMENTARY = "complementary"
    CONTRADICTORY = "contradictory"
    UNCLEAR = "unclear"

class ClaimLink(Base):
    __tablename__ = "claim_links"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id = Column(UUID(as_uuid=True), ForeignKey("claims.id", ondelete="CASCADE"), nullable=False, index=True)
    source_paper_id = Column(UUID(as_uuid=True), ForeignKey("papers.id", ondelete="SET NULL"), nullable=True, index=True)
    source_doc_id = Column(String(200), nullable=True)
    source_citation = Column(String(500), nullable=True)
    relation = Column(SQLEnum(ClaimRelation), nullable=False, index=True)
    confidence = Column(Float, nullable=False)
    context_excerpt = Column(String(2000), nullable=True)
    reasoning_ref = Column(String(500), nullable=True)  # Path para trace/justificativa
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False, index=True)
    
    # Relationships
    claim = relationship("Claim", back_populates="claim_links", foreign_keys=[claim_id])
    source_paper = relationship("Paper", foreign_keys=[source_paper_id])
    
    __table_args__ = (
        CheckConstraint(
            "source_paper_id IS NOT NULL OR source_doc_id IS NOT NULL",
            name="check_source_exists"
        ),
        CheckConstraint(
            "confidence >= 0.0 AND confidence <= 1.0",
            name="check_confidence_range"
        ),
        # UNIQUE(claim_id, COALESCE(source_paper_id::text, source_doc_id), relation)
        # Nota: UniqueConstraint com COALESCE pode precisar de índice funcional ou trigger
        Index("idx_claim_links_claim_id", "claim_id"),
        Index("idx_claim_links_source_paper_id", "source_paper_id"),
        Index("idx_claim_links_relation", "relation"),
        Index("idx_claim_links_confidence", "confidence"),
    )
```

**Nota sobre UNIQUE constraint**: A constraint `UNIQUE(claim_id, COALESCE(source_paper_id::text, source_doc_id), relation)` pode precisar ser implementada via índice funcional (PostgreSQL) ou trigger. Alternativa: criar índice parcial ou validar na aplicação.

---

## Schemas Pydantic

### Estrutura de Arquivos
```
backend/app/schemas/
├── __init__.py
├── paper.py              # Novo
├── paper_version.py      # Novo
├── paper_external_id.py  # Novo
├── quality_score.py      # Novo
├── claim.py              # Novo
├── claim_link.py         # Novo
├── job.py                # Existente
├── review.py             # Existente
└── ...
```

### Schema `Paper`
```python
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional
from enum import Enum

class PaperVisibility(str, Enum):
    PRIVATE = "private"
    UNLISTED = "unlisted"
    PUBLIC = "public"

class PaperBase(BaseModel):
    aid: str = Field(..., max_length=100)  # Identificador estável
    title: Optional[str] = Field(None, max_length=500)
    repo_url: Optional[str] = Field(None, max_length=1000)
    visibility: PaperVisibility = PaperVisibility.PRIVATE
    license: Optional[str] = Field(None, max_length=200)
    created_by: Optional[str] = Field(None, max_length=200)

class PaperCreate(PaperBase):
    pass

class PaperUpdate(BaseModel):
    title: Optional[str] = None
    repo_url: Optional[str] = None
    visibility: Optional[PaperVisibility] = None
    license: Optional[str] = None

class Paper(PaperBase):
    id: UUID
    approved_public_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class PaperWithRelations(Paper):
    versions: list["PaperVersion"] = []
    external_ids: list["PaperExternalId"] = []
    quality_scores: list["QualityScore"] = []
```

### Schema `PaperVersion`
```python
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, Any

class PaperVersionBase(BaseModel):
    aid: str = Field(..., max_length=100)
    version: int = Field(..., ge=1)
    pdf_path: str = Field(..., max_length=1000)
    meta_json: Optional[Dict[str, Any]] = None

class PaperVersionCreate(PaperVersionBase):
    pass

class PaperVersion(PaperVersionBase):
    id: UUID
    created_at: datetime
    deleted_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
```

### Schema `PaperExternalId`
```python
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from enum import Enum

class ExternalIdKind(str, Enum):
    DOI = "doi"
    ARXIV = "arxiv"
    PMID = "pmid"
    URL = "url"

class PaperExternalIdBase(BaseModel):
    kind: ExternalIdKind
    value: str = Field(..., max_length=500)

class PaperExternalIdCreate(PaperExternalIdBase):
    paper_id: UUID

class PaperExternalId(PaperExternalIdBase):
    id: UUID
    paper_id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True
```

### Schema `QualityScore`
```python
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum

class QualityScoreScope(str, Enum):
    PAPER = "paper"
    VERSION = "version"

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
    scope: QualityScoreScope
    score: int = Field(..., ge=0, le=100)
    signals: Dict[str, Any]
    rationale: Dict[str, Any]
    scoring_model_version: str = "v0"

class QualityScoreCreate(QualityScoreBase):
    paper_id: Optional[UUID] = None
    paper_version_id: Optional[UUID] = None
    
    @field_validator("paper_id", "paper_version_id")
    @classmethod
    def validate_scope(cls, v, info):
        scope = info.data.get("scope")
        if scope == QualityScoreScope.PAPER and not info.data.get("paper_id"):
            raise ValueError("paper_id required when scope='paper'")
        if scope == QualityScoreScope.VERSION and not info.data.get("paper_version_id"):
            raise ValueError("paper_version_id required when scope='version'")
        return v

class QualityScore(QualityScoreBase):
    id: UUID
    paper_id: Optional[UUID] = None
    paper_version_id: Optional[UUID] = None
    created_at: datetime
    
    class Config:
        from_attributes = True
```

### Schema `Claim`
```python
from pydantic import BaseModel, Field, field_validator
from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, Any
import hashlib

class ClaimBase(BaseModel):
    text: str = Field(..., max_length=5000)
    span_start: Optional[int] = None
    span_end: Optional[int] = None
    page: Optional[int] = None
    bbox: Optional[Dict[str, Any]] = None  # {x, y, width, height}
    section: Optional[str] = Field(None, max_length=100)
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    extraction_model_version: Optional[str] = Field(None, max_length=50)

class ClaimCreate(ClaimBase):
    paper_version_id: UUID
    
    @field_validator("span_start", "span_end")
    @classmethod
    def validate_span(cls, v, info):
        span_start = info.data.get("span_start")
        span_end = info.data.get("span_end")
        if (span_start is None) != (span_end is None):
            raise ValueError("span_start and span_end must both be set or both be None")
        return v
    
    def compute_hash(self, paper_version_id: UUID) -> str:
        """Compute hash for deduplication."""
        content = f"{self.text}|{self.span_start}|{self.span_end}|{paper_version_id}"
        return hashlib.sha256(content.encode()).hexdigest()

class Claim(ClaimBase):
    id: UUID
    paper_version_id: UUID
    paper_id: Optional[UUID] = None
    hash: str
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
    reasoning_ref: Optional[str] = Field(None, max_length=500)
    
    @field_validator("source_paper_id", "source_doc_id")
    @classmethod
    def validate_source(cls, v, info):
        source_paper_id = info.data.get("source_paper_id")
        source_doc_id = info.data.get("source_doc_id")
        if not source_paper_id and not source_doc_id:
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

1. **Criar modelos SQLAlchemy** (`paper.py`, `paper_version.py`, `paper_external_id.py`, `quality_score.py`, `claim.py`, `claim_link.py`)
2. **Atualizar `__init__.py`** para exportar novos modelos
3. **Criar migrations Alembic** (6 migrations na ordem: papers → paper_versions → paper_external_ids → quality_scores → claims → claim_links)
4. **Criar schemas Pydantic** (6 schemas correspondentes)
5. **Atualizar `__init__.py`** dos schemas
6. **Testar migrations** (up/down)
7. **Testar modelos** (CRUD básico, validações de scope, dedupe de claims)

---

## Critérios de Aceite Técnicos

- [ ] 6 migrations criadas e testadas (up/down)
- [ ] 6 modelos SQLAlchemy criados com relacionamentos corretos
- [ ] Constraints e índices aplicados corretamente
- [ ] Schemas Pydantic criados com validações
- [ ] Testes unitários para modelos (CRUD básico)
- [ ] Testes de integridade referencial (cascade deletes)
- [ ] Testes de regras condicionais (scope em quality_scores)
- [ ] Testes de dedupe de claims por hash
- [ ] Testes de unicidade (aid, version) e paper_external_ids
- [ ] Documentação inline (docstrings nos modelos)

---

## Testes Sugeridos

### Testes Unitários
```python
# test_models_paper.py
- test_create_paper_with_aid()
- test_paper_visibility_enum()
- test_paper_soft_delete()
- test_paper_with_versions()
- test_paper_with_external_ids()

# test_models_paper_version.py
- test_create_paper_version()
- test_unique_aid_version()
- test_version_positive_check()
- test_pdf_path_relative()

# test_models_paper_external_id.py
- test_create_external_id()
- test_unique_paper_kind()
- test_external_id_kinds()

# test_models_quality_score.py
- test_create_quality_score_paper_scope()
- test_create_quality_score_version_scope()
- test_scope_validation()
- test_score_range_validation()

# test_models_claim.py
- test_create_claim()
- test_span_consistency()
- test_confidence_range()
- test_hash_dedupe()
- test_bbox_structure()

# test_models_claim_link.py
- test_create_claim_link()
- test_source_validation()
- test_relation_enum()
- test_unique_claim_source_relation()
```

### Testes de Migrations
```python
# test_migrations.py
- test_papers_table_created()
- test_paper_versions_table_created()
- test_paper_external_ids_table_created()
- test_quality_scores_table_created()
- test_claims_table_created()
- test_claim_links_table_created()
- test_foreign_keys()
- test_indexes()
- test_constraints()
- test_enums()
- test_all_migrations_reversible()
```

---

## Notas de Implementação

1. **AID Generation**: Gerar `aid` automaticamente (ULID ou slug baseado em título) no momento da criação
2. **UUIDs**: Usar `UUID(as_uuid=True)` no SQLAlchemy para compatibilidade com PostgreSQL e SQLite
3. **JSON Fields**: Usar `JSON` do SQLAlchemy (PostgreSQL) ou `Text` com serialização JSON (SQLite fallback)
4. **Timezones**: Sempre usar `timezone=True` em `DateTime` e `datetime.now(UTC)`
5. **Cascade Deletes**: Papers deletam versions, external_ids, quality_scores; versions deletam claims; claims deletam claim_links
6. **Check Constraints**: Validar no banco e no Pydantic (defesa em profundidade)
7. **Soft Delete**: Usar `deleted_at IS NULL` em queries padrão; adicionar filtros explícitos quando necessário
8. **PDF Path Validation**: Validar existência física do arquivo no insert/update de `paper_versions`
9. **Hash Computation**: Calcular hash de claims no momento da criação para dedupe
10. **UNIQUE Constraint Complexa**: Para `claim_links`, considerar índice funcional ou validação na aplicação

---

## Configuração de Ambiente

### Variáveis de Ambiente
```bash
PAPERS_BASE=/var/arandu/papers  # Obrigatória
DB_URL=postgresql://...
```

### Validação de Storage
- `paper_versions.pdf_path` sempre relativo a `PAPERS_BASE`
- Formato esperado: `/papers/{aid}/v{version}/file.pdf`
- Validar existência física no insert/update

---

## Dependências Externas

- SQLAlchemy 2.0+
- Alembic
- Pydantic 2.0+
- PostgreSQL (produção) ou SQLite (dev/test)
- ULID library (opcional, para geração de `aid`)

---

## Próximos Passos (Após Fase 1)

- Fase 2: Storage/Config (configurar `PAPERS_BASE`, upload de PDF, validação de paths)
- Fase 3: APIs (endpoints `/papers` usando os modelos criados, geração de `aid`)
