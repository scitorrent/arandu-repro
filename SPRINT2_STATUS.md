# Sprint 2 - Status Report

## ✅ Implementado (Phase 2 - Hosting APIs + Viewer)

### Backend APIs (#34)
- ✅ `POST /api/v1/papers` - Upload PDF ou URL, cria paper com versão 1
- ✅ `POST /api/v1/papers/{aid}/versions` - Cria nova versão
- ✅ `GET /api/v1/papers/{aid}` - Retorna metadata com counts
- ✅ `GET /api/v1/papers/{aid}/viewer` - Stream PDF com Range/206 support
- ✅ `HEAD /api/v1/papers/{aid}/viewer` - Metadata do PDF
- ✅ `GET /api/v1/papers/{aid}/claims` - Lista claims com paginação
- ✅ Validação de PDF (size, MIME, header)
- ✅ Storage utils integrado
- ✅ CORS configurado para Next.js

### Frontend (#35, #36)
- ✅ Next.js 14 App Router (TypeScript)
- ✅ Tailwind CSS com design tokens
- ✅ `/p/[aid]` page com tabs (PDF | Review | Artifacts)
- ✅ `/p/[aid]/viewer` page com PDF.js
- ✅ Responsive, mobile-first
- ✅ Acessibilidade (focus rings, high contrast)

### Infrastructure
- ✅ Dockerfile para frontend
- ✅ docker-compose.yml com serviço `web`
- ✅ CI configurado para testes com Postgres

### Database & Models (Phase 1 - ✅ Completo)
- ✅ 6 tabelas criadas: `papers`, `paper_versions`, `paper_external_ids`, `quality_scores`, `claims`, `claim_links`
- ✅ Migrations Alembic (up/down testadas)
- ✅ ENUMs centralizados
- ✅ Índices compostos e GIN
- ✅ Soft delete implementado
- ✅ Validações condicionais (scope, dedupe, unicidade)

### Tests
- ✅ `test_papers_api.py` - Testes de API
- ✅ `test_models_papers.py` - Testes de modelos
- ✅ `test_migrations_papers.py` - Testes de migrations
- ✅ `test_conditional_rules.py` - Testes de regras
- ✅ `test_storage_permissions.py` - Testes de storage
- ✅ `test_concurrency.py` - Testes de concorrência
- ✅ `test_e2e_smoke.py` - Smoke test E2E

### Bugs Corrigidos
- ✅ **Bug 1**: `shutil.move()` corrigido em `papers.py` (caminho do arquivo, não diretório)
- ✅ **Bug 2**: `ReviewResponse` schema corrigido para extrair campos de `paper_meta` JSON
- ✅ **Bug 3**: `.env.bak` removido e `.gitignore` atualizado
- ✅ **Bug 4**: Dependência `python-magic` tornada opcional (fallback para extensão)

## ⚠️ Pendências Antes do PR

### 1. Testes
- [ ] Executar testes localmente e garantir que passam
- [ ] Verificar se CI está configurado corretamente
- [ ] Testar E2E manualmente (upload PDF → visualizar)

### 2. Documentação
- [x] README atualizado com exemplos de uso
- [ ] Verificar se há documentação faltando nos novos módulos

### 3. Segurança
- [x] `.env.bak` removido
- [x] `.gitignore` atualizado
- ⚠️ **AÇÃO NECESSÁRIA**: Rotacionar credenciais expostas no histórico do Git
  - `GEMINI_API_KEY` que estava em `.env.bak`
  - `GCP_PROJECT_ID` que estava em `.env.bak`

### 4. DoD Checklist (PR Template)
- [x] APIs (#34) implementadas com validações, storage, Range streaming
- [x] Frontend viewer/page (#35/#36) carrega PDFs do backend e renderiza
- [ ] CI: Postgres service, `alembic upgrade head`, testes de API passam
- [ ] `docker-compose up` traz api+db+redis+worker+web healthy
- [x] README atualizado com exemplos

## 📋 Próximos Passos

### Imediato (Antes do PR)
1. ✅ Commitar correções de bugs
2. ✅ Verificar se todos os arquivos estão commitados
3. ⚠️ Testar localmente (`docker-compose up`)
4. ⚠️ Executar testes (`pytest tests/api/test_papers_api.py`)

### Após Merge
- **#37**: Public/Private toggle + approval flow
- **#38**: Review tab minimal renderer
- **#39**: Basic upload UI (drag/drop)

## 🚨 Ações Críticas

1. **Rotacionar Credenciais**: As credenciais expostas em `.env.bak` precisam ser rotacionadas:
   - Gerar nova `GEMINI_API_KEY` no Google Cloud Console
   - Atualizar `.env` local com nova chave
   - Considerar usar secrets management (ex: GitHub Secrets) para CI/CD

2. **Testar Localmente**: Antes de abrir o PR, testar:
   ```bash
   docker-compose up
   # Upload um PDF
   curl -X POST http://localhost:8000/api/v1/papers -F "pdf=@test.pdf"
   # Verificar se a página carrega
   open http://localhost:3000/p/[aid]
   ```

## 📊 Status Geral

**Phase 1 (DB & Models)**: ✅ **100% Completo**
**Phase 2 (APIs + Frontend)**: ✅ **95% Completo** (pendente testes locais)

**Pronto para PR?**: ⚠️ **Quase** - Faltam testes locais e verificação de CI

