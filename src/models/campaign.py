from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import json

# Importar db do módulo de autenticação
from .auth import db

class Campaign(db.Model):
    __tablename__ = 'campaigns'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    message_template = db.Column(db.Text, nullable=False)
    image_path = db.Column(db.String(255))
    coupon_code = db.Column(db.String(50))
    target_segment = db.Column(db.String(50))  # 'high_ticket', 'frequent', 'location', etc.
    status = db.Column(db.String(20), default='draft')  # draft, active, completed, paused
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamento com disparos
    dispatches = db.relationship('CampaignDispatch', backref='campaign', lazy=True, cascade='all, delete-orphan')

class Customer(db.Model):
    __tablename__ = 'customers'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False, unique=True)
    email = db.Column(db.String(100))
    location = db.Column(db.String(100))
    average_ticket = db.Column(db.Float, default=0.0)
    order_frequency = db.Column(db.Integer, default=0)  # pedidos por mês
    last_order_date = db.Column(db.DateTime)
    preferred_items = db.Column(db.Text)  # JSON string com itens preferidos
    segment = db.Column(db.String(50))  # high_ticket, frequent, location_based, etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class CampaignDispatch(db.Model):
    __tablename__ = 'campaign_dispatches'
    
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaigns.id'), nullable=False)
    customer_group = db.Column(db.Integer, nullable=False)  # grupo de 300 clientes
    dispatch_number = db.Column(db.Integer, nullable=False)  # 1, 2 ou 3
    scheduled_date = db.Column(db.DateTime, nullable=False)
    sent_date = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='scheduled')  # scheduled, sent, failed
    customers_count = db.Column(db.Integer, default=0)
    success_count = db.Column(db.Integer, default=0)
    failed_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class MessageLog(db.Model):
    __tablename__ = 'message_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaigns.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    dispatch_id = db.Column(db.Integer, db.ForeignKey('campaign_dispatches.id'), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    message_content = db.Column(db.Text)
    image_path = db.Column(db.String(255))
    sent_date = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='pending')  # pending, sent, delivered, failed
    whatsapp_message_id = db.Column(db.String(100))
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

