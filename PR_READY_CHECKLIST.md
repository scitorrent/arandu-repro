# ✅ PR Ready Checklist - Sprint 2 Phase 2

## Status: 🟡 QUASE PRONTO (pequenos ajustes finais)

### ✅ Implementado e Funcionando

- [x] **APIs Backend** (#34)
  - POST /api/v1/papers (upload PDF/URL)
  - POST /api/v1/papers/{aid}/versions
  - GET /api/v1/papers/{aid} (metadata)
  - GET /api/v1/papers/{aid}/viewer (PDF streaming com Range/206)
  - GET /api/v1/papers/{aid}/claims
  - Validação de PDF (size, MIME, header)
  - CORS configurado

- [x] **Frontend Next.js** (#35, #36)
  - Página /p/[aid] com tabs
  - PDF viewer com PDF.js
  - Design responsivo
  - Tailwind CSS com design tokens

- [x] **Infraestrutura**
  - Dockerfile para frontend
  - docker-compose.yml com serviço web
  - Migrations corrigidas (ENUMs idempotentes)
  - CI configurado

- [x] **Correções Críticas**
  - Enum visibility corrigido (native_enum=False)
  - NEXT_PUBLIC_API_BASE = http://localhost:8000
  - Migrations com tratamento de ENUMs duplicados

### ⚠️ Pendências Menores

- [ ] Commitar arquivos de documentação:
  - DEMO_LOCAL.md
  - start-demo.sh
  - frontend/next.config.js (se necessário)

- [ ] Verificar .gitignore para:
  - frontend/public/ (se deve ser ignorado)
  - frontend/package-lock.json (geralmente commitado)

- [ ] Ajustar healthcheck do frontend (opcional, não bloqueia)

### 📝 PR Description

O template já está em `.github/pull_request_template.md` e pode ser usado.

**Título sugerido:**
```
feat(sprint2): Phase 2 - Hosting APIs + Viewer (#34-#36)
```

**Branch atual:** `feat/sprint2-hosting-apis-ui`

### 🧪 Testes

- ✅ Demo local funcionando
- ✅ API respondendo corretamente
- ✅ Frontend carregando
- ⚠️ Testes locais precisam de ambiente Docker (redis, postgres)

### 📋 Próximos Passos

1. Commitar arquivos pendentes de documentação
2. Verificar .gitignore
3. Criar PR no GitHub
4. Adicionar screenshots (opcional)
5. Linkar issues #34, #35, #36

---

**Conclusão:** PR está 95% pronto. Apenas pequenos ajustes de documentação e commit de arquivos auxiliares.
