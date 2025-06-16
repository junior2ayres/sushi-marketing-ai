import requests
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional

class InstagramService:
    """Serviço para integração com Instagram Graph API"""
    
    def __init__(self, access_token: str, page_id: str):
        self.access_token = access_token
        self.page_id = page_id
        self.base_url = "https://graph.facebook.com/v19.0"
        
    def create_media_container(self, image_url: str, caption: str) -> str:
        """Criar container de mídia para postagem"""
        url = f"{self.base_url}/{self.page_id}/media"
        
        params = {
            'image_url': image_url,
            'caption': caption,
            'access_token': self.access_token
        }
        
        response = requests.post(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        return data['id']
    
    def publish_media(self, creation_id: str) -> Dict[str, Any]:
        """Publicar mídia criada"""
        url = f"{self.base_url}/{self.page_id}/media_publish"
        
        params = {
            'creation_id': creation_id,
            'access_token': self.access_token
        }
        
        response = requests.post(url, params=params)
        response.raise_for_status()
        
        return response.json()
    
    def post_image(self, image_url: str, caption: str) -> Dict[str, Any]:
        """Postar imagem no Instagram"""
        try:
            # Criar container de mídia
            creation_id = self.create_media_container(image_url, caption)
            
            # Publicar mídia
            result = self.publish_media(creation_id)
            
            return {
                'success': True,
                'post_id': result.get('id'),
                'message': 'Post publicado com sucesso no Instagram'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Erro ao publicar no Instagram'
            }

class FacebookService:
    """Serviço para integração com Facebook Graph API"""
    
    def __init__(self, access_token: str, page_id: str):
        self.access_token = access_token
        self.page_id = page_id
        self.base_url = "https://graph.facebook.com/v19.0"
    
    def post_text(self, message: str) -> Dict[str, Any]:
        """Postar texto no Facebook"""
        url = f"{self.base_url}/{self.page_id}/feed"
        
        params = {
            'message': message,
            'access_token': self.access_token
        }
        
        try:
            response = requests.post(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            return {
                'success': True,
                'post_id': data.get('id'),
                'message': 'Post publicado com sucesso no Facebook'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Erro ao publicar no Facebook'
            }
    
    def post_image(self, image_url: str, message: str) -> Dict[str, Any]:
        """Postar imagem com texto no Facebook"""
        url = f"{self.base_url}/{self.page_id}/photos"
        
        params = {
            'url': image_url,
            'caption': message,
            'access_token': self.access_token
        }
        
        try:
            response = requests.post(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            return {
                'success': True,
                'post_id': data.get('id'),
                'message': 'Imagem publicada com sucesso no Facebook'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Erro ao publicar imagem no Facebook'
            }

class TikTokService:
    """Serviço para integração com TikTok Content Posting API"""
    
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.base_url = "https://open.tiktokapis.com/v2"
    
    def upload_video(self, video_url: str, title: str, description: str = "") -> Dict[str, Any]:
        """Upload de vídeo para TikTok"""
        url = f"{self.base_url}/post/publish/video/init/"
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'post_info': {
                'title': title,
                'description': description,
                'privacy_level': 'SELF_ONLY',  # ou 'PUBLIC_TO_EVERYONE'
                'disable_duet': False,
                'disable_comment': False,
                'disable_stitch': False,
                'video_cover_timestamp_ms': 1000
            },
            'source_info': {
                'source': 'FILE_UPLOAD',
                'video_url': video_url
            }
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            return {
                'success': True,
                'publish_id': result.get('data', {}).get('publish_id'),
                'message': 'Vídeo enviado com sucesso para TikTok'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Erro ao enviar vídeo para TikTok'
            }
    
    def check_upload_status(self, publish_id: str) -> Dict[str, Any]:
        """Verificar status do upload"""
        url = f"{self.base_url}/post/publish/status/fetch/"
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'publish_id': publish_id
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            
            return response.json()
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Erro ao verificar status do upload'
            }

class SocialMediaManager:
    """Gerenciador central para todas as redes sociais"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.instagram = None
        self.facebook = None
        self.tiktok = None
        
        # Inicializar serviços se as credenciais estiverem disponíveis
        if config.get('instagram'):
            self.instagram = InstagramService(
                config['instagram']['access_token'],
                config['instagram']['page_id']
            )
        
        if config.get('facebook'):
            self.facebook = FacebookService(
                config['facebook']['access_token'],
                config['facebook']['page_id']
            )
        
        if config.get('tiktok'):
            self.tiktok = TikTokService(
                config['tiktok']['access_token']
            )
    
    def post_to_instagram(self, content: str, image_url: Optional[str] = None) -> Dict[str, Any]:
        """Postar no Instagram"""
        if not self.instagram:
            return {
                'success': False,
                'error': 'Instagram não configurado',
                'message': 'Credenciais do Instagram não encontradas'
            }
        
        if image_url:
            return self.instagram.post_image(image_url, content)
        else:
            return {
                'success': False,
                'error': 'Instagram requer imagem',
                'message': 'Instagram não suporta posts apenas de texto'
            }
    
    def post_to_facebook(self, content: str, image_url: Optional[str] = None) -> Dict[str, Any]:
        """Postar no Facebook"""
        if not self.facebook:
            return {
                'success': False,
                'error': 'Facebook não configurado',
                'message': 'Credenciais do Facebook não encontradas'
            }
        
        if image_url:
            return self.facebook.post_image(image_url, content)
        else:
            return self.facebook.post_text(content)
    
    def post_to_tiktok(self, title: str, video_url: str, description: str = "") -> Dict[str, Any]:
        """Postar no TikTok"""
        if not self.tiktok:
            return {
                'success': False,
                'error': 'TikTok não configurado',
                'message': 'Credenciais do TikTok não encontradas'
            }
        
        return self.tiktok.upload_video(video_url, title, description)
    
    def post_to_all_platforms(self, content: str, image_url: Optional[str] = None, 
                             video_url: Optional[str] = None) -> Dict[str, Any]:
        """Postar em todas as plataformas configuradas"""
        results = {}
        
        # Instagram (requer imagem)
        if self.instagram and image_url:
            results['instagram'] = self.post_to_instagram(content, image_url)
        
        # Facebook (texto ou imagem)
        if self.facebook:
            results['facebook'] = self.post_to_facebook(content, image_url)
        
        # TikTok (requer vídeo)
        if self.tiktok and video_url:
            results['tiktok'] = self.post_to_tiktok(content, video_url, content)
        
        return {
            'success': True,
            'results': results,
            'message': f'Postagem enviada para {len(results)} plataforma(s)'
        }

def get_social_media_config() -> Dict[str, Any]:
    """Obter configurações das redes sociais a partir de variáveis de ambiente"""
    config = {}
    
    # Instagram
    if os.getenv('INSTAGRAM_ACCESS_TOKEN') and os.getenv('INSTAGRAM_PAGE_ID'):
        config['instagram'] = {
            'access_token': os.getenv('INSTAGRAM_ACCESS_TOKEN'),
            'page_id': os.getenv('INSTAGRAM_PAGE_ID')
        }
    
    # Facebook
    if os.getenv('FACEBOOK_ACCESS_TOKEN') and os.getenv('FACEBOOK_PAGE_ID'):
        config['facebook'] = {
            'access_token': os.getenv('FACEBOOK_ACCESS_TOKEN'),
            'page_id': os.getenv('FACEBOOK_PAGE_ID')
        }
    
    # TikTok
    if os.getenv('TIKTOK_ACCESS_TOKEN'):
        config['tiktok'] = {
            'access_token': os.getenv('TIKTOK_ACCESS_TOKEN')
        }
    
    return config

# Exemplo de uso
if __name__ == "__main__":
    # Configurar credenciais
    config = get_social_media_config()
    
    # Criar gerenciador
    social_manager = SocialMediaManager(config)
    
    # Exemplo de postagem
    content = "🍣 Sushi fresquinho acabou de sair da cozinha! Peça já o seu delivery. #SushiDelivery #ComidaJaponesa"
    image_url = "https://exemplo.com/sushi-image.jpg"
    
    # Postar em todas as plataformas
    result = social_manager.post_to_all_platforms(content, image_url)
    print(json.dumps(result, indent=2))

