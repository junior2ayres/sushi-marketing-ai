from flask import Blueprint, request, jsonify
from src.services.messaging import WhatsAppService, CampaignExecutor, SocialMediaService
from src.models.campaign import CampaignDispatch, MessageLog
from src.models.user import db
from datetime import datetime
import os

messaging_bp = Blueprint('messaging', __name__)

# Configurações da Evolution API (devem ser configuradas via variáveis de ambiente)
EVOLUTION_API_URL = os.getenv('EVOLUTION_API_URL', 'http://localhost:8080')
EVOLUTION_API_KEY = os.getenv('EVOLUTION_API_KEY', 'your-api-key')
EVOLUTION_INSTANCE = os.getenv('EVOLUTION_INSTANCE', 'your-instance')

@messaging_bp.route('/whatsapp/test-connection', methods=['GET'])
def test_whatsapp_connection():
    """Testar conexão com Evolution API"""
    try:
        whatsapp_service = WhatsAppService(
            EVOLUTION_API_URL, 
            EVOLUTION_API_KEY, 
            EVOLUTION_INSTANCE
        )
        
        status = whatsapp_service.get_instance_status()
        return jsonify({
            'status': 'success',
            'connection': status
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@messaging_bp.route('/whatsapp/send-test', methods=['POST'])
def send_test_message():
    """Enviar mensagem de teste"""
    data = request.get_json()
    phone = data.get('phone')
    message = data.get('message', 'Mensagem de teste do agente de IA para sushi delivery!')
    
    if not phone:
        return jsonify({'error': 'Número de telefone é obrigatório'}), 400
    
    try:
        whatsapp_service = WhatsAppService(
            EVOLUTION_API_URL, 
            EVOLUTION_API_KEY, 
            EVOLUTION_INSTANCE
        )
        
        result = whatsapp_service.send_text_message(phone, message)
        
        return jsonify({
            'status': 'success',
            'message': 'Mensagem enviada com sucesso',
            'result': result
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@messaging_bp.route('/dispatches/execute/<int:dispatch_id>', methods=['POST'])
def execute_dispatch(dispatch_id):
    """Executar um disparo específico"""
    try:
        whatsapp_service = WhatsAppService(
            EVOLUTION_API_URL, 
            EVOLUTION_API_KEY, 
            EVOLUTION_INSTANCE
        )
        
        executor = CampaignExecutor(whatsapp_service)
        result = executor.execute_dispatch(dispatch_id)
        
        return jsonify({
            'status': 'success',
            'result': result
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@messaging_bp.route('/dispatches/pending', methods=['GET'])
def get_pending_dispatches():
    """Listar disparos pendentes"""
    now = datetime.utcnow()
    
    pending_dispatches = CampaignDispatch.query.filter(
        CampaignDispatch.status == 'scheduled',
        CampaignDispatch.scheduled_date <= now
    ).all()
    
    return jsonify([{
        'id': d.id,
        'campaign_id': d.campaign_id,
        'campaign_name': d.campaign.name,
        'customer_group': d.customer_group,
        'dispatch_number': d.dispatch_number,
        'scheduled_date': d.scheduled_date.isoformat(),
        'customers_count': d.customers_count
    } for d in pending_dispatches])

@messaging_bp.route('/dispatches/execute-pending', methods=['POST'])
def execute_pending_dispatches():
    """Executar todos os disparos pendentes"""
    now = datetime.utcnow()
    
    pending_dispatches = CampaignDispatch.query.filter(
        CampaignDispatch.status == 'scheduled',
        CampaignDispatch.scheduled_date <= now
    ).all()
    
    if not pending_dispatches:
        return jsonify({
            'status': 'success',
            'message': 'Nenhum disparo pendente encontrado',
            'executed': 0
        })
    
    try:
        whatsapp_service = WhatsAppService(
            EVOLUTION_API_URL, 
            EVOLUTION_API_KEY, 
            EVOLUTION_INSTANCE
        )
        
        executor = CampaignExecutor(whatsapp_service)
        results = []
        
        for dispatch in pending_dispatches:
            try:
                result = executor.execute_dispatch(dispatch.id)
                results.append(result)
            except Exception as e:
                results.append({
                    'dispatch_id': dispatch.id,
                    'error': str(e)
                })
        
        return jsonify({
            'status': 'success',
            'message': f'{len(results)} disparos processados',
            'results': results
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@messaging_bp.route('/social-media/post', methods=['POST'])
def post_to_social_media():
    """Postar em redes sociais"""
    data = request.get_json()
    platform = data.get('platform')  # instagram, facebook, tiktok
    content = data.get('content')
    image_path = data.get('image_path')
    
    if not platform or not content:
        return jsonify({'error': 'Platform e content são obrigatórios'}), 400
    
    try:
        social_service = SocialMediaService()
        
        if platform == 'instagram':
            result = social_service.post_to_instagram(content, image_path)
        elif platform == 'facebook':
            result = social_service.post_to_facebook(content, image_path)
        elif platform == 'tiktok':
            result = social_service.post_to_tiktok(content, image_path)
        else:
            return jsonify({'error': 'Plataforma não suportada'}), 400
        
        return jsonify({
            'status': 'success',
            'platform': platform,
            'result': result
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@messaging_bp.route('/reports/campaign/<int:campaign_id>', methods=['GET'])
def get_campaign_report(campaign_id):
    """Relatório de uma campanha específica"""
    dispatches = CampaignDispatch.query.filter_by(campaign_id=campaign_id).all()
    
    total_sent = sum(d.success_count or 0 for d in dispatches)
    total_failed = sum(d.failed_count or 0 for d in dispatches)
    total_scheduled = sum(d.customers_count for d in dispatches if d.status == 'scheduled')
    
    # Logs de mensagens para análise detalhada
    message_logs = MessageLog.query.filter_by(campaign_id=campaign_id).all()
    
    return jsonify({
        'campaign_id': campaign_id,
        'total_dispatches': len(dispatches),
        'total_sent': total_sent,
        'total_failed': total_failed,
        'total_scheduled': total_scheduled,
        'success_rate': (total_sent / (total_sent + total_failed)) * 100 if (total_sent + total_failed) > 0 else 0,
        'dispatches': [{
            'id': d.id,
            'group': d.customer_group,
            'dispatch_number': d.dispatch_number,
            'status': d.status,
            'scheduled_date': d.scheduled_date.isoformat(),
            'sent_date': d.sent_date.isoformat() if d.sent_date else None,
            'success_count': d.success_count,
            'failed_count': d.failed_count
        } for d in dispatches],
        'recent_messages': [{
            'phone': log.phone_number,
            'status': log.status,
            'sent_date': log.sent_date.isoformat() if log.sent_date else None,
            'error': log.error_message
        } for log in message_logs[-10:]]  # Últimas 10 mensagens
    })

