import schedule
import time
import threading
from datetime import datetime, timedelta
from src.models.campaign import CampaignDispatch
from src.models.user import db
from src.services.messaging import WhatsAppService, CampaignExecutor
import os
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CampaignScheduler:
    """Agendador de campanhas para execução automática"""
    
    def __init__(self):
        self.running = False
        self.thread = None
        
        # Configurações da Evolution API
        self.evolution_api_url = os.getenv('EVOLUTION_API_URL', 'http://localhost:8080')
        self.evolution_api_key = os.getenv('EVOLUTION_API_KEY', 'your-api-key')
        self.evolution_instance = os.getenv('EVOLUTION_INSTANCE', 'your-instance')
        
        # Configurar agendamento para verificar disparos pendentes a cada 5 minutos
        schedule.every(5).minutes.do(self.check_pending_dispatches)
        
        logger.info("CampaignScheduler inicializado")
    
    def start(self):
        """Iniciar o agendador em uma thread separada"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
            self.thread.start()
            logger.info("CampaignScheduler iniciado")
    
    def stop(self):
        """Parar o agendador"""
        self.running = False
        if self.thread:
            self.thread.join()
        logger.info("CampaignScheduler parado")
    
    def _run_scheduler(self):
        """Executar o loop do agendador"""
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Verificar a cada minuto
            except Exception as e:
                logger.error(f"Erro no agendador: {str(e)}")
                time.sleep(60)
    
    def check_pending_dispatches(self):
        """Verificar e executar disparos pendentes"""
        try:
            from src.main import app
            
            with app.app_context():
                now = datetime.utcnow()
                
                # Buscar disparos que devem ser executados agora
                pending_dispatches = CampaignDispatch.query.filter(
                    CampaignDispatch.status == 'scheduled',
                    CampaignDispatch.scheduled_date <= now
                ).all()
                
                if not pending_dispatches:
                    logger.info("Nenhum disparo pendente encontrado")
                    return
                
                logger.info(f"Encontrados {len(pending_dispatches)} disparos pendentes")
                
                # Configurar serviços
                whatsapp_service = WhatsAppService(
                    self.evolution_api_url,
                    self.evolution_api_key,
                    self.evolution_instance
                )
                
                executor = CampaignExecutor(whatsapp_service)
                
                # Executar cada disparo
                for dispatch in pending_dispatches:
                    try:
                        logger.info(f"Executando disparo {dispatch.id} da campanha {dispatch.campaign.name}")
                        result = executor.execute_dispatch(dispatch.id)
                        logger.info(f"Disparo {dispatch.id} executado: {result['success_count']} sucessos, {result['failed_count']} falhas")
                    except Exception as e:
                        logger.error(f"Erro ao executar disparo {dispatch.id}: {str(e)}")
                        # Marcar disparo como falhou
                        dispatch.status = 'failed'
                        db.session.commit()
                
        except Exception as e:
            logger.error(f"Erro ao verificar disparos pendentes: {str(e)}")

class CRMAnalytics:
    """Classe para análises e relatórios de CRM"""
    
    @staticmethod
    def get_campaign_performance(campaign_id):
        """Obter performance de uma campanha"""
        from src.models.campaign import Campaign, CampaignDispatch, MessageLog
        
        campaign = Campaign.query.get(campaign_id)
        if not campaign:
            return None
        
        dispatches = CampaignDispatch.query.filter_by(campaign_id=campaign_id).all()
        message_logs = MessageLog.query.filter_by(campaign_id=campaign_id).all()
        
        total_sent = sum(d.success_count or 0 for d in dispatches)
        total_failed = sum(d.failed_count or 0 for d in dispatches)
        total_scheduled = sum(d.customers_count for d in dispatches if d.status == 'scheduled')
        
        # Calcular métricas por disparo (1º, 2º, 3º)
        dispatch_metrics = {}
        for dispatch_num in [1, 2, 3]:
            dispatch_data = [d for d in dispatches if d.dispatch_number == dispatch_num]
            dispatch_metrics[f'dispatch_{dispatch_num}'] = {
                'total_groups': len(dispatch_data),
                'sent': sum(d.success_count or 0 for d in dispatch_data),
                'failed': sum(d.failed_count or 0 for d in dispatch_data),
                'pending': len([d for d in dispatch_data if d.status == 'scheduled'])
            }
        
        return {
            'campaign_id': campaign_id,
            'campaign_name': campaign.name,
            'target_segment': campaign.target_segment,
            'status': campaign.status,
            'created_at': campaign.created_at.isoformat(),
            'total_dispatches': len(dispatches),
            'total_sent': total_sent,
            'total_failed': total_failed,
            'total_scheduled': total_scheduled,
            'success_rate': (total_sent / (total_sent + total_failed)) * 100 if (total_sent + total_failed) > 0 else 0,
            'dispatch_metrics': dispatch_metrics,
            'message_logs_count': len(message_logs)
        }
    
    @staticmethod
    def get_customer_engagement(customer_id):
        """Obter engajamento de um cliente específico"""
        from src.models.campaign import Customer, MessageLog
        
        customer = Customer.query.get(customer_id)
        if not customer:
            return None
        
        message_logs = MessageLog.query.filter_by(customer_id=customer_id).all()
        
        # Calcular métricas de engajamento
        total_messages = len(message_logs)
        successful_messages = len([m for m in message_logs if m.status == 'sent'])
        failed_messages = len([m for m in message_logs if m.status == 'failed'])
        
        # Última interação
        last_message = max(message_logs, key=lambda m: m.sent_date) if message_logs else None
        
        return {
            'customer_id': customer_id,
            'customer_name': customer.name,
            'phone': customer.phone,
            'segment': customer.segment,
            'average_ticket': customer.average_ticket,
            'order_frequency': customer.order_frequency,
            'total_messages_received': total_messages,
            'successful_deliveries': successful_messages,
            'failed_deliveries': failed_messages,
            'delivery_rate': (successful_messages / total_messages) * 100 if total_messages > 0 else 0,
            'last_message_date': last_message.sent_date.isoformat() if last_message and last_message.sent_date else None,
            'campaigns_participated': len(set(m.campaign_id for m in message_logs))
        }
    
    @staticmethod
    def get_segment_analysis():
        """Análise por segmento de clientes"""
        from src.models.campaign import Customer, MessageLog
        
        segments = db.session.query(
            Customer.segment,
            db.func.count(Customer.id).label('customer_count'),
            db.func.avg(Customer.average_ticket).label('avg_ticket'),
            db.func.avg(Customer.order_frequency).label('avg_frequency')
        ).group_by(Customer.segment).all()
        
        segment_analysis = []
        
        for segment in segments:
            # Buscar mensagens para este segmento
            segment_customers = Customer.query.filter_by(segment=segment.segment).all()
            customer_ids = [c.id for c in segment_customers]
            
            if customer_ids:
                segment_messages = MessageLog.query.filter(MessageLog.customer_id.in_(customer_ids)).all()
                successful_messages = len([m for m in segment_messages if m.status == 'sent'])
                total_messages = len(segment_messages)
            else:
                successful_messages = 0
                total_messages = 0
            
            segment_analysis.append({
                'segment': segment.segment,
                'customer_count': segment.customer_count,
                'avg_ticket': float(segment.avg_ticket or 0),
                'avg_frequency': float(segment.avg_frequency or 0),
                'total_messages_sent': total_messages,
                'successful_deliveries': successful_messages,
                'delivery_rate': (successful_messages / total_messages) * 100 if total_messages > 0 else 0
            })
        
        return segment_analysis

class CRMRecommendations:
    """Sistema de recomendações baseado em dados do CRM"""
    
    @staticmethod
    def get_campaign_recommendations(segment=None):
        """Obter recomendações de campanhas baseadas em dados históricos"""
        recommendations = []
        
        if segment == 'high_ticket' or segment is None:
            recommendations.append({
                'segment': 'high_ticket',
                'title': 'Campanha Premium VIP',
                'description': 'Ofereça produtos premium com desconto exclusivo para clientes de alto valor',
                'suggested_discount': '15-20%',
                'best_time': 'Quinta-feira 18:00-20:00',
                'message_template': 'Olá {nome_cliente}! Como cliente VIP, você tem acesso exclusivo à nossa seleção premium. Use {cupom_desconto} e ganhe 15% OFF em combinados especiais.',
                'expected_conversion': '8-12%'
            })
        
        if segment == 'frequent' or segment is None:
            recommendations.append({
                'segment': 'frequent',
                'title': 'Programa de Fidelidade',
                'description': 'Recompense clientes frequentes com benefícios especiais',
                'suggested_discount': '10%',
                'best_time': 'Terça-feira 19:00-21:00',
                'message_template': 'Oi {nome_cliente}! Você é um dos nossos clientes mais especiais. Aproveite {cupom_desconto} com 10% OFF no seu {sabor_preferido} favorito!',
                'expected_conversion': '15-20%'
            })
        
        if segment == 'location_based' or segment is None:
            recommendations.append({
                'segment': 'location_based',
                'title': 'Promoção Regional',
                'description': 'Campanhas específicas por região com frete grátis',
                'suggested_discount': 'Frete grátis',
                'best_time': 'Domingo 17:00-19:00',
                'message_template': 'Olá {nome_cliente}! Promoção especial na sua região: frete grátis em pedidos acima de R$ 50. Use {cupom_desconto}!',
                'expected_conversion': '12-18%'
            })
        
        return recommendations
    
    @staticmethod
    def get_content_recommendations(platform, segment):
        """Recomendações de conteúdo baseadas em performance"""
        content_recommendations = {
            'instagram': {
                'high_ticket': [
                    'Showcase de ingredientes premium importados',
                    'Behind the scenes com o chef especialista',
                    'Comparação: sushi comum vs premium',
                    'Depoimentos de clientes VIP'
                ],
                'frequent': [
                    'Stories com enquete sobre sabores favoritos',
                    'Programa de pontos e recompensas',
                    'Novidades exclusivas para clientes fiéis',
                    'Agradecimento personalizado'
                ],
                'location_based': [
                    'Mapa de entregas na região',
                    'Tempo de entrega por bairro',
                    'Parcerias com estabelecimentos locais',
                    'Eventos e promoções regionais'
                ]
            },
            'facebook': {
                'high_ticket': [
                    'Artigo sobre a arte do sushi premium',
                    'Vídeo da seleção de ingredientes',
                    'História dos pratos especiais',
                    'Harmonização com bebidas premium'
                ],
                'frequent': [
                    'Dicas de conservação do sushi',
                    'Curiosidades sobre a culinária japonesa',
                    'Receitas simples para acompanhar',
                    'Benefícios nutricionais do peixe'
                ]
            },
            'whatsapp': {
                'high_ticket': [
                    'Convite para degustação exclusiva',
                    'Cardápio premium com preços especiais',
                    'Atendimento personalizado via WhatsApp',
                    'Agendamento de pedidos especiais'
                ],
                'frequent': [
                    'Lembrete semanal do dia do sushi',
                    'Ofertas relâmpago para clientes fiéis',
                    'Pesquisa de satisfação rápida',
                    'Novidades do cardápio em primeira mão'
                ]
            }
        }
        
        return content_recommendations.get(platform, {}).get(segment, [])

# Instância global do agendador
campaign_scheduler = CampaignScheduler()

# Função para inicializar o agendador quando a aplicação iniciar
def init_scheduler():
    """Inicializar o agendador de campanhas"""
    campaign_scheduler.start()

# Função para parar o agendador quando a aplicação for encerrada
def stop_scheduler():
    """Parar o agendador de campanhas"""
    campaign_scheduler.stop()

