from flask import Blueprint, request, jsonify
from src.models.user import db
from src.models.campaign import Campaign, Customer, CampaignDispatch, MessageLog
import pandas as pd
import io
import json
from datetime import datetime, timedelta
import os

campaign_bp = Blueprint('campaign', __name__)

@campaign_bp.route('/campaigns', methods=['GET'])
def get_campaigns():
    """Listar todas as campanhas"""
    campaigns = Campaign.query.all()
    return jsonify([{
        'id': c.id,
        'name': c.name,
        'status': c.status,
        'target_segment': c.target_segment,
        'created_at': c.created_at.isoformat(),
        'dispatches_count': len(c.dispatches)
    } for c in campaigns])

@campaign_bp.route('/campaigns', methods=['POST'])
def create_campaign():
    """Criar nova campanha"""
    data = request.get_json()
    
    campaign = Campaign(
        name=data['name'],
        message_template=data['message_template'],
        image_path=data.get('image_path'),
        coupon_code=data.get('coupon_code'),
        target_segment=data.get('target_segment', 'all')
    )
    
    db.session.add(campaign)
    db.session.commit()
    
    return jsonify({
        'id': campaign.id,
        'message': 'Campanha criada com sucesso'
    }), 201

@campaign_bp.route('/customers/import', methods=['POST'])
def import_customers():
    """Importar clientes via CSV"""
    if 'file' not in request.files:
        return jsonify({'error': 'Nenhum arquivo enviado'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Nenhum arquivo selecionado'}), 400
    
    if not file.filename.endswith('.csv'):
        return jsonify({'error': 'Arquivo deve ser CSV'}), 400
    
    try:
        # Ler CSV
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        df = pd.read_csv(stream)
        
        # Validar colunas obrigatórias
        required_columns = ['name', 'phone']
        if not all(col in df.columns for col in required_columns):
            return jsonify({
                'error': f'Colunas obrigatórias: {required_columns}. Encontradas: {list(df.columns)}'
            }), 400
        
        imported_count = 0
        updated_count = 0
        
        for _, row in df.iterrows():
            # Verificar se cliente já existe
            existing_customer = Customer.query.filter_by(phone=row['phone']).first()
            
            if existing_customer:
                # Atualizar dados existentes
                existing_customer.name = row['name']
                existing_customer.email = row.get('email', existing_customer.email)
                existing_customer.location = row.get('location', existing_customer.location)
                existing_customer.average_ticket = float(row.get('average_ticket', existing_customer.average_ticket or 0))
                existing_customer.order_frequency = int(row.get('order_frequency', existing_customer.order_frequency or 0))
                existing_customer.preferred_items = row.get('preferred_items', existing_customer.preferred_items)
                existing_customer.updated_at = datetime.utcnow()
                updated_count += 1
            else:
                # Criar novo cliente
                customer = Customer(
                    name=row['name'],
                    phone=row['phone'],
                    email=row.get('email'),
                    location=row.get('location'),
                    average_ticket=float(row.get('average_ticket', 0)),
                    order_frequency=int(row.get('order_frequency', 0)),
                    preferred_items=row.get('preferred_items')
                )
                db.session.add(customer)
                imported_count += 1
        
        # Segmentar clientes após importação
        _segment_customers()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Importação concluída',
            'imported': imported_count,
            'updated': updated_count,
            'total': imported_count + updated_count
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao processar arquivo: {str(e)}'}), 500

@campaign_bp.route('/customers/segments', methods=['GET'])
def get_customer_segments():
    """Obter estatísticas de segmentação de clientes"""
    segments = db.session.query(
        Customer.segment,
        db.func.count(Customer.id).label('count')
    ).group_by(Customer.segment).all()
    
    total_customers = Customer.query.count()
    
    return jsonify({
        'total_customers': total_customers,
        'segments': [{'segment': s.segment, 'count': s.count} for s in segments]
    })

@campaign_bp.route('/campaigns/<int:campaign_id>/schedule', methods=['POST'])
def schedule_campaign(campaign_id):
    """Agendar disparos de uma campanha"""
    campaign = Campaign.query.get_or_404(campaign_id)
    data = request.get_json()
    
    start_date = datetime.fromisoformat(data['start_date'])
    target_segment = data.get('target_segment', campaign.target_segment)
    
    # Buscar clientes do segmento
    query = Customer.query
    if target_segment and target_segment != 'all':
        query = query.filter(Customer.segment == target_segment)
    
    customers = query.all()
    
    if not customers:
        return jsonify({'error': 'Nenhum cliente encontrado para o segmento'}), 400
    
    # Dividir em grupos de 300
    groups = [customers[i:i+300] for i in range(0, len(customers), 300)]
    
    # Criar disparos programados
    for group_index, group in enumerate(groups):
        for dispatch_number in range(1, 4):  # 3 disparos
            dispatch_date = start_date + timedelta(days=(dispatch_number - 1) * 2)
            
            dispatch = CampaignDispatch(
                campaign_id=campaign_id,
                customer_group=group_index + 1,
                dispatch_number=dispatch_number,
                scheduled_date=dispatch_date,
                customers_count=len(group)
            )
            db.session.add(dispatch)
    
    campaign.status = 'active'
    db.session.commit()
    
    return jsonify({
        'message': 'Campanha agendada com sucesso',
        'groups_created': len(groups),
        'total_dispatches': len(groups) * 3,
        'total_customers': len(customers)
    })

def _segment_customers():
    """Segmentar clientes automaticamente"""
    customers = Customer.query.all()
    
    for customer in customers:
        # Lógica de segmentação
        if customer.average_ticket >= 100:
            customer.segment = 'high_ticket'
        elif customer.order_frequency >= 8:  # 8+ pedidos por mês
            customer.segment = 'frequent'
        elif customer.location:
            customer.segment = 'location_based'
        else:
            customer.segment = 'standard'

@campaign_bp.route('/knowledge/books', methods=['GET'])
def get_marketing_books():
    """Retornar conhecimento sobre livros de marketing"""
    books_knowledge = {
        "essential_books": [
            {
                "title": "Isso é Marketing",
                "author": "Seth Godin",
                "key_concepts": [
                    "Criar algo notável (vaca roxa)",
                    "Marketing é sobre mudança",
                    "Encontrar e servir seu público mínimo viável"
                ],
                "application_to_sushi": "Criar experiências únicas no delivery que se destaquem da concorrência"
            },
            {
                "title": "Marketing 4.0",
                "author": "Philip Kotler",
                "key_concepts": [
                    "Conectividade e engajamento digital",
                    "Jornada do cliente omnichannel",
                    "Marketing centrado no humano"
                ],
                "application_to_sushi": "Integrar todos os pontos de contato digital para uma experiência consistente"
            },
            {
                "title": "Marketing para Restaurantes",
                "author": "Diversos",
                "key_concepts": [
                    "Estratégias específicas para food service",
                    "Otimização de delivery",
                    "Fidelização de clientes"
                ],
                "application_to_sushi": "Aplicação direta de táticas testadas no setor de alimentação"
            }
        ],
        "key_strategies": [
            "Segmentação baseada em comportamento de compra",
            "Personalização de ofertas",
            "Automação de campanhas",
            "Monitoramento de ROI",
            "Experiência omnichannel"
        ]
    }
    
    return jsonify(books_knowledge)

@campaign_bp.route('/ai/generate-content', methods=['POST'])
def generate_marketing_content():
    """Gerar conteúdo de marketing usando IA"""
    data = request.get_json()
    content_type = data.get('type', 'whatsapp')
    target_segment = data.get('segment', 'all')
    product_focus = data.get('product', 'sushi')
    
    # Templates baseados no conhecimento dos livros
    templates = {
        'whatsapp': {
            'high_ticket': {
                'message': "Olá {nome_cliente}! 🍣 Que tal experimentar nossa seleção premium? Temos uma oferta especial para clientes VIP como você. Use o cupom {cupom_desconto} e ganhe 15% OFF no seu próximo pedido premium. Acesse: {link_cardapio}",
                'image_suggestion': "Imagem de combinado premium com sashimis e peças especiais"
            },
            'frequent': {
                'message': "Oi {nome_cliente}! 😊 Notamos que você ama nossos {sabor_preferido}! Preparamos uma surpresa especial: {cupom_desconto} com 10% OFF para seu próximo pedido. Peça já: {link_cardapio}",
                'image_suggestion': "Imagem do item preferido do cliente em destaque"
            },
            'standard': {
                'message': "Olá {nome_cliente}! 🍱 Está com vontade de sushi fresquinho? Temos uma promoção imperdível para você! Use {cupom_desconto} e ganhe desconto especial. Confira: {link_cardapio}",
                'image_suggestion': "Imagem de combinado popular com boa relação custo-benefício"
            }
        },
        'instagram': {
            'post': "🍣 Frescor que você pode sentir! Nossos sushis são preparados na hora com ingredientes premium. #SushiFresco #DeliveryDeQualidade #SushiLovers",
            'story': "Swipe para ver nossos combinados mais pedidos! 👆 Stories com enquete sobre sabor favorito"
        },
        'facebook': {
            'post': "🥢 A tradição japonesa na sua casa! Delivery de sushi com a qualidade que você merece. Peça já e comprove a diferença!"
        }
    }
    
    if content_type == 'whatsapp':
        segment_template = templates['whatsapp'].get(target_segment, templates['whatsapp']['standard'])
        return jsonify({
            'content_type': 'whatsapp',
            'message_template': segment_template['message'],
            'image_suggestion': segment_template['image_suggestion'],
            'variables': ['nome_cliente', 'cupom_desconto', 'link_cardapio', 'sabor_preferido']
        })
    else:
        return jsonify(templates.get(content_type, {'message': 'Tipo de conteúdo não encontrado'}))

