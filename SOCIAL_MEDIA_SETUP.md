# Configuração das Redes Sociais - Agente IA Sushi Marketing

## Variáveis de Ambiente Necessárias

Para habilitar a integração com as redes sociais, configure as seguintes variáveis de ambiente:

### Instagram (via Facebook Graph API)
```bash
export INSTAGRAM_ACCESS_TOKEN="seu_token_de_acesso_instagram"
export INSTAGRAM_PAGE_ID="id_da_sua_pagina_instagram"
```

### Facebook
```bash
export FACEBOOK_ACCESS_TOKEN="seu_token_de_acesso_facebook"
export FACEBOOK_PAGE_ID="id_da_sua_pagina_facebook"
```

### TikTok
```bash
export TIKTOK_ACCESS_TOKEN="seu_token_de_acesso_tiktok"
```

### WhatsApp (Evolution API)
```bash
export EVOLUTION_API_URL="http://localhost:8080"
export EVOLUTION_API_KEY="sua_chave_da_evolution_api"
export EVOLUTION_INSTANCE="nome_da_sua_instancia"
```

## Como Obter os Tokens

### Instagram e Facebook
1. Acesse [Facebook Developers](https://developers.facebook.com/)
2. Crie um novo app
3. Adicione o produto "Instagram Graph API"
4. Configure as permissões necessárias:
   - `instagram_basic`
   - `instagram_content_publish`
   - `pages_show_list`
   - `pages_read_engagement`
5. Gere o token de acesso de longa duração

### TikTok
1. Acesse [TikTok Developers](https://developers.tiktok.com/)
2. Registre-se como desenvolvedor
3. Crie um novo app
4. Solicite acesso ao Content Posting API
5. Configure o OAuth 2.0 para obter tokens

### Evolution API (WhatsApp)
1. Configure sua instância da Evolution API
2. Obtenha a chave de API da sua instalação
3. Configure o nome da instância

## Funcionalidades Implementadas

### ✅ Instagram
- Postagem de imagens com legenda
- Suporte a hashtags
- Templates de conteúdo específicos para sushi

### ✅ Facebook
- Postagem de texto
- Postagem de imagens com texto
- Suporte a call-to-action

### ✅ TikTok
- Upload de vídeos
- Configuração de título e descrição
- Verificação de status do upload

### ✅ WhatsApp (Evolution API)
- Envio de mensagens de texto
- Envio de imagens com legenda
- Segmentação de clientes
- Disparos programados

## Endpoints da API

### Verificar Configuração
```
GET /api/social/config
```

### Postar em Redes Sociais
```
POST /api/social/post
{
  "content": "Texto da postagem",
  "platforms": ["instagram", "facebook", "tiktok"],
  "image_url": "https://exemplo.com/imagem.jpg",
  "video_url": "https://exemplo.com/video.mp4"
}
```

### Obter Templates de Conteúdo
```
GET /api/social/templates
```

### Gerar Ideias de Conteúdo
```
GET /api/social/content-ideas?segment=high_ticket&platform=instagram
```

## Limitações e Considerações

### Instagram
- Requer conta business ou creator
- Apenas imagens e vídeos (não suporta texto puro)
- Limite de 25 posts por dia via API

### Facebook
- Suporta texto, imagens e vídeos
- Requer página do Facebook (não perfil pessoal)
- Rate limits aplicáveis

### TikTok
- Requer aprovação para Content Posting API
- Apenas vídeos
- Políticas rigorosas de conteúdo

### WhatsApp
- Requer Evolution API configurada
- Respeitar políticas anti-spam
- Limite de mensagens por instância

## Próximos Passos

1. **Configurar Credenciais**: Obtenha os tokens necessários
2. **Testar Conexões**: Use o endpoint `/api/social/config`
3. **Criar Conteúdo**: Use os templates ou gere ideias personalizadas
4. **Agendar Posts**: Implemente sistema de agendamento
5. **Monitorar Analytics**: Integre APIs de métricas

## Suporte

Para dúvidas sobre configuração ou problemas com as integrações, consulte:
- [Documentação Facebook Graph API](https://developers.facebook.com/docs/graph-api/)
- [Documentação TikTok API](https://developers.tiktok.com/doc/)
- [Documentação Evolution API](https://doc.evolution-api.com/)

