from flask import Blueprint, request, jsonify
from src.services.social_media import SocialMediaManager, get_social_media_config
import os

social_bp = Blueprint('social', __name__)

@social_bp.route('/social/config', methods=['GET'])
def get_social_config():
    """Verificar configuração das redes sociais"""
    config = get_social_media_config()
    
    status = {
        'instagram': bool(config.get('instagram')),
        'facebook': bool(config.get('facebook')),
        'tiktok': bool(config.get('tiktok'))
    }
    
    return jsonify({
        'configured_platforms': status,
        'total_configured': sum(status.values()),
        'message': 'Configure as variáveis de ambiente para habilitar as integrações'
    })

@social_bp.route('/social/post', methods=['POST'])
def post_to_social():
    """Postar em redes sociais"""
    data = request.get_json()
    
    content = data.get('content')
    platforms = data.get('platforms', [])  # ['instagram', 'facebook', 'tiktok']
    image_url = data.get('image_url')
    video_url = data.get('video_url')
    
    if not content:
        return jsonify({'error': 'Conteúdo é obrigatório'}), 400
    
    if not platforms:
        return jsonify({'error': 'Selecione pelo menos uma plataforma'}), 400
    
    try:
        config = get_social_media_config()
        social_manager = SocialMediaManager(config)
        
        results = {}
        
        for platform in platforms:
            if platform == 'instagram':
                if not image_url:
                    results[platform] = {
                        'success': False,
                        'error': 'Instagram requer imagem'
                    }
                else:
                    results[platform] = social_manager.post_to_instagram(content, image_url)
            
            elif platform == 'facebook':
                results[platform] = social_manager.post_to_facebook(content, image_url)
            
            elif platform == 'tiktok':
                if not video_url:
                    results[platform] = {
                        'success': False,
                        'error': 'TikTok requer vídeo'
                    }
                else:
                    results[platform] = social_manager.post_to_tiktok(content, video_url)
            
            else:
                results[platform] = {
                    'success': False,
                    'error': 'Plataforma não suportada'
                }
        
        success_count = sum(1 for r in results.values() if r.get('success'))
        
        return jsonify({
            'success': success_count > 0,
            'results': results,
            'success_count': success_count,
            'total_platforms': len(platforms),
            'message': f'Postagem enviada para {success_count}/{len(platforms)} plataforma(s)'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Erro interno do servidor'
        }), 500

@social_bp.route('/social/templates', methods=['GET'])
def get_social_templates():
    """Obter templates de conteúdo para redes sociais"""
    templates = {
        'instagram': {
            'sushi_promo': {
                'content': '🍣 Sushi fresquinho saindo da cozinha! Peça já o seu delivery e ganhe 10% OFF com o cupom SUSHI10. #SushiDelivery #ComidaJaponesa #Delivery',
                'hashtags': ['#SushiDelivery', '#ComidaJaponesa', '#Delivery', '#SushiFresco', '#PedidoOnline']
            },
            'combo_special': {
                'content': '🥢 Combo especial para duas pessoas! Sashimi, temaki e hot roll por um preço incrível. Aproveite nossa promoção! #ComboSushi #PromoçãoEspecial',
                'hashtags': ['#ComboSushi', '#PromoçãoEspecial', '#SushiParaDois', '#Delivery']
            },
            'fresh_ingredients': {
                'content': '🐟 Ingredientes frescos, sabor autêntico! Nosso sushi é preparado com o melhor do mar. Experimente a diferença! #SushiFresco #QualidadePremium',
                'hashtags': ['#SushiFresco', '#QualidadePremium', '#IngredientesFrescos', '#SaborAutentico']
            }
        },
        'facebook': {
            'weekend_promo': {
                'content': 'Final de semana é sinônimo de sushi! 🍣 Aproveite nossa promoção especial de fim de semana: 15% OFF em todos os combinados. Válido até domingo. Peça pelo nosso delivery e receba em casa quentinho!',
                'call_to_action': 'Peça agora pelo nosso site ou WhatsApp!'
            },
            'new_menu': {
                'content': 'Novidades no cardápio! 🆕 Acabamos de lançar novos sabores de temaki e hot roll. Venha experimentar essas delícias da culinária japonesa. Delivery disponível em toda a cidade!',
                'call_to_action': 'Confira o cardápio completo no nosso site!'
            }
        },
        'tiktok': {
            'preparation_video': {
                'title': 'Como fazemos nosso sushi',
                'description': 'Veja o processo artesanal de preparação do nosso sushi! Ingredientes frescos e técnica japonesa tradicional. #SushiPreparation #ComidaJaponesa #Delivery'
            },
            'delivery_speed': {
                'title': 'Sushi delivery em 30 minutos',
                'description': 'Do pedido à sua mesa em apenas 30 minutos! Veja como nosso delivery é rápido e eficiente. #DeliveryRapido #SushiDelivery #PedidoOnline'
            }
        }
    }
    
    return jsonify(templates)

@social_bp.route('/social/schedule', methods=['POST'])
def schedule_social_post():
    """Agendar postagem em redes sociais (placeholder)"""
    data = request.get_json()
    
    # Esta funcionalidade requereria um sistema de agendamento
    # Por enquanto, retornamos uma resposta de sucesso simulada
    
    return jsonify({
        'success': True,
        'message': 'Postagem agendada com sucesso',
        'scheduled_for': data.get('schedule_date'),
        'platforms': data.get('platforms', []),
        'note': 'Funcionalidade de agendamento será implementada em versão futura'
    })

@social_bp.route('/social/analytics', methods=['GET'])
def get_social_analytics():
    """Obter analytics das redes sociais (placeholder)"""
    # Esta funcionalidade requereria integração com APIs de analytics
    # Por enquanto, retornamos dados simulados
    
    analytics = {
        'instagram': {
            'followers': 1250,
            'posts_this_month': 15,
            'engagement_rate': 4.2,
            'top_hashtags': ['#SushiDelivery', '#ComidaJaponesa', '#Delivery']
        },
        'facebook': {
            'page_likes': 890,
            'posts_this_month': 12,
            'reach': 5600,
            'engagement': 340
        },
        'tiktok': {
            'followers': 2100,
            'videos_this_month': 8,
            'total_views': 45000,
            'average_watch_time': '15s'
        }
    }
    
    return jsonify({
        'success': True,
        'analytics': analytics,
        'note': 'Dados simulados - integração com APIs de analytics será implementada'
    })

@social_bp.route('/social/content-ideas', methods=['GET'])
def get_content_ideas():
    """Gerar ideias de conteúdo baseadas em marketing para sushi"""
    segment = request.args.get('segment', 'general')
    platform = request.args.get('platform', 'instagram')
    
    ideas = {
        'general': {
            'instagram': [
                '🍣 Foto do sushi sendo preparado (behind the scenes)',
                '🥢 Flat lay dos ingredientes frescos',
                '📱 Stories com enquete: "Qual seu sushi favorito?"',
                '🎥 Reels mostrando a montagem de um temaki',
                '🌟 Depoimento de cliente satisfeito'
            ],
            'facebook': [
                'Post educativo sobre os benefícios do peixe cru',
                'Compartilhar a história da culinária japonesa',
                'Promoção especial para novos clientes',
                'Dicas de como conservar sushi em casa',
                'Apresentar a equipe de sushimen'
            ],
            'tiktok': [
                'Vídeo rápido da preparação do sushi',
                'Trend de "POV: você pediu sushi delivery"',
                'Comparação: sushi caseiro vs profissional',
                'Reação de primeira vez comendo sushi',
                'Tutorial rápido de como usar hashi'
            ]
        },
        'high_ticket': {
            'instagram': [
                '🏆 Showcase de combinados premium',
                '💎 Ingredientes importados e especiais',
                '👨‍🍳 Apresentação do chef especialista',
                '🍾 Harmonização com sake premium',
                '📸 Fotografia profissional dos pratos'
            ]
        },
        'frequent': {
            'instagram': [
                '🎁 Programa de fidelidade',
                '📅 "Sushi da semana" para clientes VIP',
                '⭐ Agradecimento aos clientes fiéis',
                '🔄 Novidades exclusivas para frequentadores',
                '💝 Brindes especiais'
            ]
        }
    }
    
    selected_ideas = ideas.get(segment, ideas['general']).get(platform, ideas['general']['instagram'])
    
    return jsonify({
        'segment': segment,
        'platform': platform,
        'ideas': selected_ideas,
        'total_ideas': len(selected_ideas)
    })

