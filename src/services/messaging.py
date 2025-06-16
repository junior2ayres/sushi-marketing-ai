import requests
import json
from datetime import datetime
import os
from src.models.campaign import MessageLog, CampaignDispatch, Customer
from src.models.user import db

class WhatsAppService:
    def __init__(self, evolution_api_url, api_key, instance_name):
        self.api_url = evolution_api_url.rstrip('/')
        self.api_key = api_key
        self.instance_name = instance_name
        self.headers = {
            'Content-Type': 'application/json',
            'apikey': api_key
        }
    
    def send_text_message(self, phone_number, message):
        """Enviar mensagem de texto via Evolution API"""
        url = f"{self.api_url}/message/sendText/{self.instance_name}"
        
        payload = {
            "number": phone_number,
            "text": message
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Erro ao enviar mensagem: {str(e)}")
    
    def send_media_message(self, phone_number, message, media_path):
        """Enviar mensagem com imagem via Evolution API"""
        url = f"{self.api_url}/message/sendMedia/{self.instance_name}"
        
        # Se for um caminho local, converter para base64 ou URL
        if os.path.exists(media_path):
            with open(media_path, 'rb') as f:
                import base64
                media_base64 = base64.b64encode(f.read()).decode()
                media_url = f"data:image/jpeg;base64,{media_base64}"
        else:
            media_url = media_path  # Assumir que é uma URL
        
        payload = {
            "number": phone_number,
            "mediatype": "image",
            "media": media_url,
            "caption": message
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Erro ao enviar mídia: {str(e)}")
    
    def get_instance_status(self):
        """Verificar status da instância"""
        url = f"{self.api_url}/instance/connectionState/{self.instance_name}"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Erro ao verificar status: {str(e)}")

class CampaignExecutor:
    def __init__(self, whatsapp_service):
        self.whatsapp_service = whatsapp_service
    
    def execute_dispatch(self, dispatch_id):
        """Executar um disparo específico"""
        dispatch = CampaignDispatch.query.get(dispatch_id)
        if not dispatch:
            raise Exception(f"Disparo {dispatch_id} não encontrado")
        
        if dispatch.status != 'scheduled':
            raise Exception(f"Disparo {dispatch_id} não está agendado")
        
        campaign = dispatch.campaign
        
        # Buscar clientes do grupo
        customers = self._get_customers_for_dispatch(dispatch)
        
        success_count = 0
        failed_count = 0
        
        for customer in customers:
            try:
                # Personalizar mensagem
                personalized_message = self._personalize_message(
                    campaign.message_template, 
                    customer, 
                    campaign.coupon_code
                )
                
                # Enviar mensagem
                if campaign.image_path:
                    result = self.whatsapp_service.send_media_message(
                        customer.phone, 
                        personalized_message, 
                        campaign.image_path
                    )
                else:
                    result = self.whatsapp_service.send_text_message(
                        customer.phone, 
                        personalized_message
                    )
                
                # Registrar log de sucesso
                message_log = MessageLog(
                    campaign_id=campaign.id,
                    customer_id=customer.id,
                    dispatch_id=dispatch.id,
                    phone_number=customer.phone,
                    message_content=personalized_message,
                    image_path=campaign.image_path,
                    sent_date=datetime.utcnow(),
                    status='sent',
                    whatsapp_message_id=result.get('key', {}).get('id')
                )
                db.session.add(message_log)
                success_count += 1
                
            except Exception as e:
                # Registrar log de erro
                message_log = MessageLog(
                    campaign_id=campaign.id,
                    customer_id=customer.id,
                    dispatch_id=dispatch.id,
                    phone_number=customer.phone,
                    message_content=personalized_message if 'personalized_message' in locals() else '',
                    status='failed',
                    error_message=str(e)
                )
                db.session.add(message_log)
                failed_count += 1
        
        # Atualizar status do disparo
        dispatch.status = 'sent'
        dispatch.sent_date = datetime.utcnow()
        dispatch.success_count = success_count
        dispatch.failed_count = failed_count
        
        db.session.commit()
        
        return {
            'dispatch_id': dispatch_id,
            'success_count': success_count,
            'failed_count': failed_count,
            'total_customers': len(customers)
        }
    
    def _get_customers_for_dispatch(self, dispatch):
        """Obter clientes para um disparo específico"""
        campaign = dispatch.campaign
        
        # Buscar clientes do segmento
        query = Customer.query
        if campaign.target_segment and campaign.target_segment != 'all':
            query = query.filter(Customer.segment == campaign.target_segment)
        
        all_customers = query.all()
        
        # Dividir em grupos de 300 e pegar o grupo específico
        start_index = (dispatch.customer_group - 1) * 300
        end_index = start_index + 300
        
        return all_customers[start_index:end_index]
    
    def _personalize_message(self, template, customer, coupon_code):
        """Personalizar mensagem com dados do cliente"""
        personalized = template
        
        # Substituir variáveis
        replacements = {
            '{nome_cliente}': customer.name,
            '{cupom_desconto}': coupon_code or 'DESCONTO10',
            '{link_cardapio}': 'https://seu-cardapio.com.br',
            '{sabor_preferido}': customer.preferred_items or 'sushi'
        }
        
        for placeholder, value in replacements.items():
            personalized = personalized.replace(placeholder, str(value))
        
        return personalized

class SocialMediaService:
    def __init__(self):
        self.instagram_api = None  # Configurar com credenciais
        self.facebook_api = None   # Configurar com credenciais
        self.tiktok_api = None     # Configurar com credenciais
    
    def post_to_instagram(self, content, image_path=None):
        """Postar no Instagram (placeholder)"""
        # Implementar integração com Instagram Graph API
        return {"status": "success", "message": "Post agendado para Instagram"}
    
    def post_to_facebook(self, content, image_path=None):
        """Postar no Facebook (placeholder)"""
        # Implementar integração com Facebook Graph API
        return {"status": "success", "message": "Post agendado para Facebook"}
    
    def post_to_tiktok(self, content, video_path=None):
        """Postar no TikTok (placeholder)"""
        # Implementar integração com TikTok API
        return {"status": "success", "message": "Post agendado para TikTok"}

