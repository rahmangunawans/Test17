from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect
from app import db
from models import Notification, User
from datetime import datetime, timedelta
import logging

notifications_bp = Blueprint('notifications', __name__)

# SocketIO instance will be initialized in app.py
socketio = None

def init_socketio(app, socketio_instance):
    """Initialize SocketIO with the app"""
    global socketio
    socketio = socketio_instance

def cleanup_old_notifications():
    """Delete notifications older than 5 days"""
    try:
        five_days_ago = datetime.utcnow() - timedelta(days=5)
        old_notifications = Notification.query.filter(
            Notification.created_at < five_days_ago
        ).all()
        
        if old_notifications:
            for notification in old_notifications:
                db.session.delete(notification)
            db.session.commit()
            logging.info(f"Cleaned up {len(old_notifications)} old notifications")
    except Exception as e:
        logging.error(f"Failed to cleanup old notifications: {e}")
        db.session.rollback()

@notifications_bp.route('/notifications')
@login_required
def get_notifications():
    """Get user notifications via API"""
    try:
        # Clean up old notifications first
        cleanup_old_notifications()
        
        # Get user-specific notifications
        user_notifications = Notification.query.filter_by(
            user_id=current_user.id
        ).order_by(Notification.created_at.desc()).limit(20).all()
        
        # Get global notifications that user hasn't read yet
        global_notifications = Notification.query.filter_by(
            is_global=True,
            user_id=None
        ).filter(
            ~Notification.id.in_(
                db.session.query(Notification.id).filter(
                    Notification.user_id == current_user.id,
                    Notification.is_read == True
                )
            )
        ).order_by(Notification.created_at.desc()).limit(10).all()
        
        all_notifications = user_notifications + global_notifications
        all_notifications.sort(key=lambda x: x.created_at, reverse=True)
        
        return jsonify({
            'success': True,
            'notifications': [notif.to_dict() for notif in all_notifications[:20]],
            'unread_count': len([n for n in all_notifications if not n.is_read])
        })
    except Exception as e:
        logging.error(f"Error fetching notifications: {e}")
        return jsonify({'success': False, 'message': 'Failed to fetch notifications'})

@notifications_bp.route('/notifications/mark_read/<int:notification_id>', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    """Mark a notification as read"""
    try:
        notification = Notification.query.get(notification_id)
        if not notification:
            return jsonify({'success': False, 'message': 'Notification not found'})
        
        # Check if user owns this notification or it's a global notification
        if notification.user_id != current_user.id and not notification.is_global:
            return jsonify({'success': False, 'message': 'Access denied'})
        
        notification.is_read = True
        notification.read_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        logging.error(f"Error marking notification as read: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Failed to mark notification as read'})

@notifications_bp.route('/notifications/mark_all_read', methods=['POST'])
@login_required
def mark_all_notifications_read():
    """Mark all user notifications as read"""
    try:
        # Mark user-specific notifications as read
        Notification.query.filter_by(
            user_id=current_user.id,
            is_read=False
        ).update({
            'is_read': True,
            'read_at': datetime.utcnow()
        })
        
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        logging.error(f"Error marking all notifications as read: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Failed to mark notifications as read'})

def create_notification(user_id=None, title="", message="", notification_type="info", 
                       is_global=False, action_url=None, icon="bell"):
    """Create a new notification"""
    try:
        from models import Notification
        from app import db
        
        logging.info(f"Creating notification: {title} - Global: {is_global}")
        
        notification = Notification()
        notification.user_id = user_id
        notification.title = title
        notification.message = message
        notification.type = notification_type
        notification.is_global = is_global
        notification.action_url = action_url
        notification.icon = icon
        
        db.session.add(notification)
        db.session.commit()
        
        logging.info(f"Notification created successfully with ID: {notification.id}")
        
        return notification
    except Exception as e:
        logging.error(f"Error creating notification: {e}")
        import traceback
        logging.error(f"Full traceback: {traceback.format_exc()}")
        db.session.rollback()
        return None

def notify_new_episode(content_title, episode_number, episode_title, content_id):
    """Create notification for new episode"""
    create_notification(
        title="Episode Baru Tersedia!",
        message=f"Episode {episode_number} dari {content_title} - {episode_title} sudah dapat ditonton",
        notification_type="episode",
        is_global=True,
        action_url=f"/anime/{content_id}",
        icon="play-circle"
    )

def notify_new_content(content_title, content_type, content_id):
    """Create notification for new content"""
    type_text = "Anime" if content_type == "anime" else "Film"
    create_notification(
        title=f"{type_text} Baru Ditambahkan!",
        message=f"{content_title} telah ditambahkan ke platform",
        notification_type="content",
        is_global=True,
        action_url=f"/anime/{content_id}",
        icon="plus-circle"
    )

def notify_subscription_success(user_id, subscription_type):
    """Create notification for successful subscription"""
    type_text = {
        'vip_monthly': 'VIP Bulanan',
        'vip_3month': 'VIP 3 Bulan',
        'vip_yearly': 'VIP Tahunan'
    }.get(subscription_type, 'VIP')
    
    create_notification(
        user_id=user_id,
        title="Berlangganan Berhasil!",
        message=f"Selamat! Anda sekarang adalah member {type_text}. Nikmati semua konten premium!",
        notification_type="success",
        action_url="/dashboard",
        icon="crown"
    )

def notify_admin_message(user_id, title, message):
    """Create notification from admin to user"""
    create_notification(
        user_id=user_id,
        title=title,
        message=message,
        notification_type="info",
        icon="user-shield"
    )

# SocketIO Event Handlers
def setup_socketio_events(socketio_instance):
    """Setup SocketIO event handlers"""
    global socketio
    socketio = socketio_instance
    
    @socketio.on('connect')
    def handle_connect():
        if current_user.is_authenticated:
            join_room(f'user_{current_user.id}')
            logging.info(f'User {current_user.username} connected to notifications')
    
    @socketio.on('disconnect')
    def handle_disconnect():
        if current_user.is_authenticated:
            leave_room(f'user_{current_user.id}')
            logging.info(f'User {current_user.username} disconnected from notifications')
    
    @socketio.on('join_notifications')
    def handle_join_notifications():
        if current_user.is_authenticated:
            join_room(f'user_{current_user.id}')
            emit('notification_status', {'status': 'connected'})
    
    @socketio.on('mark_notification_read')
    def handle_mark_read(data):
        if current_user.is_authenticated:
            notification_id = data.get('notification_id')
            if notification_id:
                try:
                    notification = Notification.query.get(notification_id)
                    if notification and (notification.user_id == current_user.id or notification.is_global):
                        notification.is_read = True
                        notification.read_at = datetime.utcnow()
                        db.session.commit()
                        emit('notification_marked_read', {'notification_id': notification_id})
                except Exception as e:
                    logging.error(f"Error marking notification as read via SocketIO: {e}")
                    db.session.rollback()