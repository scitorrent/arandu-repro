# Demo Local - Arandu CoReview Studio

## 🚀 Início Rápido

### Opção 1: Docker Compose (Recomendado)

```bash
# 1. Navegar para o diretório do projeto
cd /Users/59388/coding/scitorrent-org/arandu

# 2. Iniciar todos os serviços
cd infra
docker compose up --build

# Aguardar até ver:
# ✅ api_1    | Application startup complete.
# ✅ web_1    | Ready on http://localhost:3000
```

**Serviços disponíveis:**
- 🌐 **Frontend**: http://localhost:3000
- 🔌 **API**: http://localhost:8000
- 🗄️ **Database**: localhost:5432
- 📦 **Redis**: localhost:6379

### Opção 2: Desenvolvimento Local (Sem Docker)

#### Backend

```bash
# Terminal 1: Backend API
cd backend

# Instalar dependências (se ainda não instalou)
pip install -e ".[dev]"

# Configurar variáveis de ambiente
export DATABASE_URL="postgresql://arandu:arandu@localhost:5432/arandu"
export REDIS_URL="redis://localhost:6379/0"
export PAPERS_BASE="/tmp/arandu/papers"
export WEB_ORIGIN="http://localhost:3000"

# Rodar migrations
alembic upgrade head

# Iniciar API
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend

```bash
# Terminal 2: Frontend
cd frontend

# Instalar dependências (se ainda não instalou)
npm install

# Configurar variável de ambiente
echo "NEXT_PUBLIC_API_BASE=http://localhost:8000" > .env.local

# Iniciar servidor de desenvolvimento
npm run dev
```

## 📝 Testando a Demo

### 1. Verificar Health Checks

```bash
# API Health
curl http://localhost:8000/health

# Frontend (abrir no navegador)
open http://localhost:3000
```

### 2. Upload de Paper via API

```bash
# Criar um PDF de teste mínimo (ou usar um PDF existente)
# Exemplo: criar um PDF simples
cat > /tmp/test.pdf << 'EOF'
%PDF-1.4
1 0 obj
<< /Type /Catalog >>
endobj
xref
0 0
trailer
<< /Size 0 /Root 1 0 R >>
startxref
0
%%EOF
EOF

# Upload do PDF
curl -X POST http://localhost:8000/api/v1/papers \
  -F "pdf=@/tmp/test.pdf" \
  -F "title=Test Paper" \
  -F "visibility=private" \
  -F "license=MIT"

# Resposta esperada:
# {
#   "aid": "abc123xyz...",
#   "version": 1,
#   "viewer_url": "http://localhost:8000/api/v1/papers/abc123xyz/viewer",
#   "paper_url": "http://localhost:8000/api/v1/papers/abc123xyz"
# }
```

### 3. Visualizar Paper na UI

1. Abrir navegador: http://localhost:3000
2. Navegar para: http://localhost:3000/p/[aid]
   - Substituir `[aid]` pelo `aid` retornado no upload
3. Verificar:
   - ✅ Página carrega
   - ✅ PDF viewer funciona (se PDF válido)
   - ✅ Tabs (PDF | Review | Artifacts) aparecem

### 4. Testar PDF Viewer

```bash
# Acessar diretamente o viewer
open http://localhost:3000/p/[aid]/viewer
```

## 🔧 Troubleshooting

### Problema: Frontend não conecta com API

**Solução:**
1. Verificar se API está rodando: `curl http://localhost:8000/health`
2. Verificar CORS no backend (`WEB_ORIGIN` configurado)
3. Verificar `NEXT_PUBLIC_API_BASE` no frontend

### Problema: Erro de migração

**Solução:**
```bash
cd backend
alembic upgrade head
# Se houver erro, verificar DATABASE_URL
```

### Problema: PDF não carrega

**Solução:**
1. Verificar se PDF é válido (header `%PDF`)
2. Verificar logs do backend: `docker compose logs api`
3. Verificar permissões de `PAPERS_BASE`

### Problema: Docker Compose não inicia

**Solução:**
```bash
# Limpar volumes antigos (cuidado: apaga dados)
docker compose down -v

# Rebuild
docker compose up --build
```

## 📊 Verificar Logs

```bash
# Todos os serviços
docker compose logs -f

# Apenas API
docker compose logs -f api

# Apenas Frontend
docker compose logs -f web

# Apenas Database
docker compose logs -f db
```

## 🎯 Checklist de Demo

- [ ] Docker Compose iniciado sem erros
- [ ] API responde em http://localhost:8000/health
- [ ] Frontend carrega em http://localhost:3000
- [ ] Upload de PDF funciona via API
- [ ] Paper aparece na UI em `/p/[aid]`
- [ ] PDF viewer carrega (se PDF válido)
- [ ] Tabs funcionam (PDF | Review | Artifacts)

## 🚨 Notas Importantes

1. **Primeira execução**: Pode demorar alguns minutos para buildar as imagens
2. **Migrations**: Rodam automaticamente no Docker, mas podem precisar ser executadas manualmente em dev local
3. **PDFs de teste**: Use PDFs válidos para testar o viewer (PDF.js requer PDFs válidos)
4. **Portas**: Certifique-se de que as portas 3000, 8000, 5432, 6379 estão livres

## 📚 Próximos Passos

Após a demo funcionar:
- Testar upload via UI (quando implementado)
- Testar review completo (quando pipeline estiver rodando)
- Verificar badges e relatórios

