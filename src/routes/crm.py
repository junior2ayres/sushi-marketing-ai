from flask import Blueprint, request, jsonify
from src.services.crm import CRMAnalytics, CRMRecommendations, campaign_scheduler
from src.models.campaign import Campaign, Customer, CampaignDispatch, MessageLog
from src.models.user import db
from datetime import datetime, timedelta
import json

crm_bp = Blueprint('crm', __name__)

@crm_bp.route('/crm/analytics/campaign/<int:campaign_id>', methods=['GET'])
def get_campaign_analytics(campaign_id):
    """Obter analytics detalhados de uma campanha"""
    try:
        analytics = CRMAnalytics.get_campaign_performance(campaign_id)
        
        if not analytics:
            return jsonify({'error': 'Campanha não encontrada'}), 404
        
        return jsonify({
            'success': True,
            'analytics': analytics
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@crm_bp.route('/crm/analytics/customer/<int:customer_id>', methods=['GET'])
def get_customer_analytics(customer_id):
    """Obter analytics de engajamento de um cliente"""
    try:
        analytics = CRMAnalytics.get_customer_engagement(customer_id)
        
        if not analytics:
            return jsonify({'error': 'Cliente não encontrado'}), 404
        
        return jsonify({
            'success': True,
            'analytics': analytics
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@crm_bp.route('/crm/analytics/segments', methods=['GET'])
def get_segments_analytics():
    """Obter análise por segmentos de clientes"""
    try:
        analytics = CRMAnalytics.get_segment_analysis()
        
        return jsonify({
            'success': True,
            'segments': analytics,
            'total_segments': len(analytics)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@crm_bp.route('/crm/recommendations/campaigns', methods=['GET'])
def get_campaign_recommendations():
    """Obter recomendações de campanhas"""
    segment = request.args.get('segment')
    
    try:
        recommendations = CRMRecommendations.get_campaign_recommendations(segment)
        
        return jsonify({
            'success': True,
            'recommendations': recommendations,
            'segment': segment or 'all'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@crm_bp.route('/crm/recommendations/content', methods=['GET'])
def get_content_recommendations():
    """Obter recomendações de conteúdo"""
    platform = request.args.get('platform', 'instagram')
    segment = request.args.get('segment', 'frequent')
    
    try:
        recommendations = CRMRecommendations.get_content_recommendations(platform, segment)
        
        return jsonify({
            'success': True,
            'recommendations': recommendations,
            'platform': platform,
            'segment': segment
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@crm_bp.route('/crm/dashboard', methods=['GET'])
def get_crm_dashboard():
    """Obter dados do dashboard de CRM"""
    try:
        # Estatísticas gerais
        total_customers = Customer.query.count()
        total_campaigns = Campaign.query.count()
        active_campaigns = Campaign.query.filter_by(status='active').count()
        
        # Disparos pendentes
        pending_dispatches = CampaignDispatch.query.filter_by(status='scheduled').count()
        
        # Mensagens enviadas hoje
        today = datetime.utcnow().date()
        messages_today = MessageLog.query.filter(
            db.func.date(MessageLog.sent_date) == today
        ).count()
        
        # Últimas campanhas
        recent_campaigns = Campaign.query.order_by(Campaign.created_at.desc()).limit(5).all()
        
        # Segmentação de clientes
        segments = db.session.query(
            Customer.segment,
            db.func.count(Customer.id).label('count')
        ).group_by(Customer.segment).all()
        
        return jsonify({
            'success': True,
            'dashboard': {
                'totals': {
                    'customers': total_customers,
                    'campaigns': total_campaigns,
                    'active_campaigns': active_campaigns,
                    'pending_dispatches': pending_dispatches,
                    'messages_today': messages_today
                },
                'recent_campaigns': [{
                    'id': c.id,
                    'name': c.name,
                    'status': c.status,
                    'target_segment': c.target_segment,
                    'created_at': c.created_at.isoformat()
                } for c in recent_campaigns],
                'customer_segments': [{
                    'segment': s.segment,
                    'count': s.count
                } for s in segments]
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@crm_bp.route('/crm/customers/search', methods=['GET'])
def search_customers():
    """Buscar clientes por critérios"""
    query = request.args.get('q', '')
    segment = request.args.get('segment')
    min_ticket = request.args.get('min_ticket', type=float)
    max_ticket = request.args.get('max_ticket', type=float)
    min_frequency = request.args.get('min_frequency', type=int)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    try:
        # Construir query
        customers_query = Customer.query
        
        if query:
            customers_query = customers_query.filter(
                db.or_(
                    Customer.name.ilike(f'%{query}%'),
                    Customer.phone.ilike(f'%{query}%'),
                    Customer.email.ilike(f'%{query}%')
                )
            )
        
        if segment:
            customers_query = customers_query.filter(Customer.segment == segment)
        
        if min_ticket is not None:
            customers_query = customers_query.filter(Customer.average_ticket >= min_ticket)
        
        if max_ticket is not None:
            customers_query = customers_query.filter(Customer.average_ticket <= max_ticket)
        
        if min_frequency is not None:
            customers_query = customers_query.filter(Customer.order_frequency >= min_frequency)
        
        # Paginar resultados
        customers = customers_query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        return jsonify({
            'success': True,
            'customers': [{
                'id': c.id,
                'name': c.name,
                'phone': c.phone,
                'email': c.email,
                'segment': c.segment,
                'average_ticket': c.average_ticket,
                'order_frequency': c.order_frequency,
                'last_order_date': c.last_order_date.isoformat() if c.last_order_date else None
            } for c in customers.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': customers.total,
                'pages': customers.pages,
                'has_next': customers.has_next,
                'has_prev': customers.has_prev
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@crm_bp.route('/crm/campaigns/performance', methods=['GET'])
def get_campaigns_performance():
    """Obter performance de todas as campanhas"""
    try:
        campaigns = Campaign.query.all()
        performance_data = []
        
        for campaign in campaigns:
            analytics = CRMAnalytics.get_campaign_performance(campaign.id)
            if analytics:
                performance_data.append(analytics)
        
        # Ordenar por taxa de sucesso
        performance_data.sort(key=lambda x: x['success_rate'], reverse=True)
        
        return jsonify({
            'success': True,
            'campaigns': performance_data,
            'total_campaigns': len(performance_data)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@crm_bp.route('/crm/scheduler/status', methods=['GET'])
def get_scheduler_status():
    """Obter status do agendador de campanhas"""
    try:
        return jsonify({
            'success': True,
            'scheduler': {
                'running': campaign_scheduler.running,
                'thread_alive': campaign_scheduler.thread.is_alive() if campaign_scheduler.thread else False
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@crm_bp.route('/crm/scheduler/start', methods=['POST'])
def start_scheduler():
    """Iniciar o agendador de campanhas"""
    try:
        if not campaign_scheduler.running:
            campaign_scheduler.start()
            return jsonify({
                'success': True,
                'message': 'Agendador iniciado com sucesso'
            })
        else:
            return jsonify({
                'success': True,
                'message': 'Agendador já está em execução'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@crm_bp.route('/crm/scheduler/stop', methods=['POST'])
def stop_scheduler():
    """Parar o agendador de campanhas"""
    try:
        if campaign_scheduler.running:
            campaign_scheduler.stop()
            return jsonify({
                'success': True,
                'message': 'Agendador parado com sucesso'
            })
        else:
            return jsonify({
                'success': True,
                'message': 'Agendador já está parado'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@crm_bp.route('/crm/export/customers', methods=['GET'])
def export_customers():
    """Exportar dados de clientes em CSV"""
    segment = request.args.get('segment')
    
    try:
        import io
        import csv
        
        # Buscar clientes
        query = Customer.query
        if segment:
            query = query.filter(Customer.segment == segment)
        
        customers = query.all()
        
        # Criar CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Cabeçalho
        writer.writerow([
            'ID', 'Nome', 'Telefone', 'Email', 'Localização', 
            'Ticket Médio', 'Frequência', 'Segmento', 'Último Pedido'
        ])
        
        # Dados
        for customer in customers:
            writer.writerow([
                customer.id,
                customer.name,
                customer.phone,
                customer.email or '',
                customer.location or '',
                customer.average_ticket or 0,
                customer.order_frequency or 0,
                customer.segment or '',
                customer.last_order_date.strftime('%Y-%m-%d') if customer.last_order_date else ''
            ])
        
        output.seek(0)
        
        return jsonify({
            'success': True,
            'csv_data': output.getvalue(),
            'total_customers': len(customers),
            'segment': segment or 'all'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

