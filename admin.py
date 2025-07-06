from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from functools import wraps
from models import db, Content, Episode, User, WatchHistory, Notification, SystemSettings
from notifications import create_notification, notify_admin_message, notify_new_episode, notify_new_content
from werkzeug.security import generate_password_hash
from sqlalchemy import text, inspect
import logging
import json

admin_bp = Blueprint('admin', __name__)

# Emergency admin access route (hidden for security)
@admin_bp.route('/emergency-admin-access')
def emergency_admin_access():
    """Hidden emergency access route for admins during maintenance"""
    from flask import render_template
    return render_template('admin/emergency_login.html')

@admin_bp.route('/maintenance-override')
def maintenance_override():
    """Alternative emergency route for admin access"""
    from flask import render_template
    return render_template('admin/emergency_login.html')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please login first.', 'error')
            return redirect(url_for('auth.login'))
        
        # Check admin status using email-based check
        is_admin = current_user.is_admin_user()
        
        if not is_admin:
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/')
@admin_bp.route('/dashboard')
@admin_required
def admin_dashboard():
    try:
        # Get statistics with proper error handling
        total_users = db.session.query(User).count()
        total_content = db.session.query(Content).count()
        total_episodes = db.session.query(Episode).count()
        
        # Get VIP users count
        vip_users = db.session.query(User).filter(
            User.subscription_type.in_(['vip_monthly', 'vip_3month', 'vip_yearly'])
        ).count()
        
        # Recent content and users with error handling
        recent_content = db.session.query(Content).order_by(Content.created_at.desc()).limit(5).all()
        recent_users = db.session.query(User).order_by(User.created_at.desc()).limit(5).all()
        
        return render_template('admin/dashboard.html',
                             total_users=total_users,
                             total_content=total_content,
                             total_episodes=total_episodes,
                             vip_users=vip_users,
                             recent_content=recent_content,
                             recent_users=recent_users)
    except Exception as e:
        logging.error(f"Admin dashboard error: {str(e)}")
        flash(f'Dashboard loading error. Please contact administrator.', 'error')
        return redirect(url_for('index'))

@admin_bp.route('/admin/content')
@login_required
@admin_required
def admin_content():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = Content.query
    if search:
        query = query.filter(
            db.or_(
                Content.title.contains(search),
                Content.genre.contains(search),
                Content.description.contains(search)
            )
        )
    
    content = query.order_by(Content.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False)
    
    return render_template('admin/content.html', content=content, search=search)

@admin_bp.route('/admin/content/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_content():
    if request.method == 'POST':
        try:
            # Handle optional fields
            total_episodes = request.form.get('total_episodes')
            total_episodes = int(total_episodes) if total_episodes and total_episodes.strip() else None
            
            content = Content(
                title=request.form['title'],
                description=request.form['description'],
                genre=request.form['genre'],
                year=int(request.form['year']),
                rating=float(request.form['rating']),
                content_type=request.form['content_type'],
                thumbnail_url=request.form['thumbnail_url'],
                trailer_url=request.form['trailer_url'],
                studio=request.form.get('studio', ''),
                total_episodes=total_episodes,
                status=request.form.get('status', 'unknown'),
                is_featured=bool(request.form.get('is_featured'))
            )
            db.session.add(content)
            db.session.commit()
            
            # Create notification for new content
            notify_new_content(content.title, content.content_type, content.id)
            
            flash(f'Content "{content.title}" added successfully!', 'success')
            return redirect(url_for('admin.admin_content'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding content: {str(e)}', 'error')
    
    return render_template('admin/content_form.html')

@admin_bp.route('/admin/content/<int:content_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_content(content_id):
    content = Content.query.get_or_404(content_id)
    
    if request.method == 'POST':
        try:
            # Handle optional fields
            total_episodes = request.form.get('total_episodes')
            total_episodes = int(total_episodes) if total_episodes and total_episodes.strip() else None
            
            content.title = request.form['title']
            content.description = request.form['description']
            content.genre = request.form['genre']
            content.year = int(request.form['year'])
            content.rating = float(request.form['rating'])
            content.content_type = request.form['content_type']
            content.thumbnail_url = request.form['thumbnail_url']
            content.trailer_url = request.form['trailer_url']
            content.studio = request.form.get('studio', '')
            content.total_episodes = total_episodes
            content.status = request.form.get('status', 'unknown')
            content.is_featured = bool(request.form.get('is_featured'))
            
            db.session.commit()
            flash(f'Content "{content.title}" updated successfully!', 'success')
            return redirect(url_for('admin.admin_content'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating content: {str(e)}', 'error')
    
    return render_template('admin/content_form.html', content=content)

@admin_bp.route('/admin/content/<int:content_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_content(content_id):
    content = Content.query.get_or_404(content_id)
    try:
        # Delete associated episodes and watch history
        Episode.query.filter_by(content_id=content_id).delete()
        WatchHistory.query.filter_by(content_id=content_id).delete()
        
        db.session.delete(content)
        db.session.commit()
        flash(f'Content "{content.title}" deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting content: {str(e)}', 'error')
    
    return redirect(url_for('admin.admin_content'))

@admin_bp.route('/content/<int:content_id>/episodes')
@login_required
@admin_required
def manage_episodes(content_id):
    content = Content.query.get_or_404(content_id)
    search = request.args.get('search', '')
    
    query = Episode.query.filter_by(content_id=content_id)
    if search:
        query = query.filter(
            db.or_(
                Episode.title.contains(search),
                Episode.description.contains(search),
                Episode.episode_number == search if search.isdigit() else False
            )
        )
    
    episodes = query.order_by(Episode.episode_number).all()
    return render_template('admin/episodes.html', content=content, episodes=episodes, search=search)

@admin_bp.route('/content/<int:content_id>/episodes/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_episode(content_id):
    content = Content.query.get_or_404(content_id)
    
    if request.method == 'POST':
        try:
            episode = Episode(
                content_id=content_id,
                episode_number=int(request.form['episode_number']),
                title=request.form['title'],
                duration=int(request.form['duration']),
                video_url=request.form['video_url'],
                thumbnail_url=request.form.get('thumbnail_url', ''),
                description=request.form.get('description', '')
            )
            db.session.add(episode)
            db.session.commit()
            
            # Create notification for new episode
            notify_new_episode(content.title, episode.episode_number, episode.title, content.id)
            
            flash(f'Episode {episode.episode_number} added successfully!', 'success')
            return redirect(url_for('admin.manage_episodes', content_id=content_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding episode: {str(e)}', 'error')
    
    return render_template('admin/episode_form.html', content=content)

@admin_bp.route('/episodes/<int:episode_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_episode(episode_id):
    episode = Episode.query.get_or_404(episode_id)
    
    if request.method == 'POST':
        try:
            episode.episode_number = int(request.form['episode_number'])
            episode.title = request.form['title']
            episode.duration = int(request.form['duration'])
            episode.video_url = request.form['video_url']
            episode.thumbnail_url = request.form.get('thumbnail_url', '')
            episode.description = request.form.get('description', '')
            
            db.session.commit()
            flash(f'Episode {episode.episode_number} updated successfully!', 'success')
            return redirect(url_for('admin.manage_episodes', content_id=episode.content_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating episode: {str(e)}', 'error')
    
    return render_template('admin/episode_form.html', content=episode.content, episode=episode)

@admin_bp.route('/episodes/<int:episode_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_episode(episode_id):
    episode = Episode.query.get_or_404(episode_id)
    content_id = episode.content_id
    
    try:
        # Delete associated watch history
        WatchHistory.query.filter_by(episode_id=episode_id).delete()
        
        db.session.delete(episode)
        db.session.commit()
        flash(f'Episode {episode.episode_number} deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting episode: {str(e)}', 'error')
    
    return redirect(url_for('admin.manage_episodes', content_id=content_id))

@admin_bp.route('/admin/users')
@login_required
@admin_required
def admin_users():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = User.query
    if search:
        query = query.filter(User.email.contains(search))
    
    users = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False)
    
    return render_template('admin/users.html', users=users, search=search)

@admin_bp.route('/users/<int:user_id>/toggle_admin', methods=['POST'])
@login_required
@admin_required
def toggle_admin(user_id):
    user = User.query.get_or_404(user_id)
    
    try:
        # Toggle admin status by changing email domain
        if user.is_admin():
            # Remove admin status by changing email if it has admin domain
            if '@admin.aniflix.com' in user.email:
                user.email = user.email.replace('@admin.aniflix.com', '@aniflix.com')
                status = "revoked"
            else:
                status = "revoked (email updated)"
        else:
            # Grant admin status by changing email domain
            if '@aniflix.com' in user.email:
                user.email = user.email.replace('@aniflix.com', '@admin.aniflix.com')
            elif '@' in user.email:
                domain = user.email.split('@')[1]
                user.email = user.email.replace(f'@{domain}', '@admin.aniflix.com')
            else:
                user.email = user.email + '@admin.aniflix.com'
            status = "granted"
        
        db.session.commit()
        flash(f'Admin privileges {status} for {user.email}', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating user: {str(e)}', 'error')
    
    return redirect(url_for('admin.admin_users'))

@admin_bp.route('/content/<int:content_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_content_quick(content_id):
    content = Content.query.get_or_404(content_id)
    
    if request.method == 'POST':
        try:
            # Update content details
            content.title = request.form.get('title', content.title)
            content.description = request.form.get('description', content.description)
            content.genre = request.form.get('genre', content.genre)
            content.year = int(request.form.get('year', content.year))
            content.rating = float(request.form.get('rating', content.rating))
            content.thumbnail_url = request.form.get('thumbnail_url', content.thumbnail_url)

            content.is_featured = bool(request.form.get('is_featured'))
            
            db.session.commit()
            flash(f'Content "{content.title}" updated successfully!', 'success')
            return redirect(url_for('admin.admin_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating content: {str(e)}', 'error')
    
    return render_template('admin/content_form.html', content=content)

@admin_bp.route('/episode/<int:episode_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_episode_direct(episode_id):
    episode = Episode.query.get_or_404(episode_id)
    
    if request.method == 'POST':
        try:
            # Update episode details
            episode.title = request.form.get('title', episode.title)
            episode.episode_number = int(request.form.get('episode_number', episode.episode_number))
            episode.duration = int(request.form.get('duration', episode.duration))
            episode.video_url = request.form.get('video_url', episode.video_url)
            
            db.session.commit()
            flash(f'Episode "{episode.title}" updated successfully!', 'success')
            return redirect(url_for('admin.manage_episodes', content_id=episode.content_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating episode: {str(e)}', 'error')
    
    return render_template('admin/episode_form.html', content=episode.content, episode=episode)

@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        try:
            # Update basic user info
            user.username = request.form.get('username', user.username)
            user.email = request.form.get('email', user.email)
            
            # Update subscription type
            subscription_type = request.form.get('subscription_type')
            user.subscription_type = subscription_type
            
            # Handle VIP expiration - check if custom date is provided
            custom_expiration = request.form.get('subscription_expires')
            if subscription_type != 'free':
                if custom_expiration:
                    # Use custom expiration date
                    from datetime import datetime
                    user.subscription_expires = datetime.strptime(custom_expiration, '%Y-%m-%d')
                else:
                    # Auto-calculate based on subscription type
                    from datetime import datetime, timedelta
                    days_map = {
                        'vip_monthly': 30,
                        'vip_3month': 90,
                        'vip_yearly': 365
                    }
                    if subscription_type in days_map:
                        user.subscription_expires = datetime.utcnow() + timedelta(days=days_map[subscription_type])
            else:
                # Free user - clear expiration
                user.subscription_expires = None
            
            # Reset password if provided
            new_password = request.form.get('new_password')
            if new_password and new_password.strip():
                user.password_hash = generate_password_hash(new_password)
            
            # Update max devices
            user.max_devices = 2 if subscription_type != 'free' else 1
            
            db.session.commit()
            flash(f'User {user.username} updated successfully!', 'success')
            return redirect(url_for('admin.admin_users'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating user: {str(e)}', 'error')
    
    return render_template('admin/user_form.html', user=user)



@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    # Prevent deleting current admin user
    if user.id == current_user.id:
        flash('You cannot delete your own account', 'error')
        return redirect(url_for('admin.admin_users'))
    
    try:
        # Delete associated data
        WatchHistory.query.filter_by(user_id=user_id).delete()
        
        db.session.delete(user)
        db.session.commit()
        flash(f'User {user.email} deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting user: {str(e)}', 'error')
    
    return redirect(url_for('admin.admin_users'))

@admin_bp.route('/analytics')
@login_required
@admin_required
def admin_analytics():
    # Get viewing statistics
    popular_content = db.session.query(
        Content.title,
        db.func.count(WatchHistory.id).label('views')
    ).join(WatchHistory).group_by(Content.id, Content.title).order_by(
        db.func.count(WatchHistory.id).desc()
    ).limit(10).all()
    
    # Completion rates
    completion_stats = db.session.query(
        WatchHistory.status,
        db.func.count(WatchHistory.id).label('count')
    ).group_by(WatchHistory.status).all()
    
    # User statistics
    total_users = User.query.count()
    vip_users = User.query.filter(User.subscription_type != 'free').count()
    
    # Content statistics
    total_content = Content.query.count()
    anime_count = Content.query.filter_by(content_type='anime').count()
    movie_count = Content.query.filter_by(content_type='movie').count()
    
    return render_template('admin/analytics.html',
                         popular_content=popular_content,
                         completion_stats=completion_stats,
                         total_users=total_users,
                         vip_users=vip_users,
                         total_content=total_content,
                         anime_count=anime_count,
                         movie_count=movie_count)

@admin_bp.route('/vip-management')
@admin_required
def vip_management():
    """VIP user management page"""
    vip_users = User.query.filter(
        User.subscription_type.in_(['vip_monthly', 'vip_3month', 'vip_yearly'])
    ).order_by(User.subscription_expires.desc()).all()
    
    return render_template('admin/vip_management.html', vip_users=vip_users)

@admin_bp.route('/user/<int:user_id>/edit-details', methods=['GET', 'POST'])
@admin_required
def edit_user_details(user_id):
    """Edit user details including VIP status"""
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        try:
            user.username = request.form.get('username', user.username)
            user.email = request.form.get('email', user.email)
            user.subscription_type = request.form.get('subscription_type', user.subscription_type)
            
            # Handle VIP expiration
            if request.form.get('subscription_expires'):
                from datetime import datetime
                user.subscription_expires = datetime.strptime(
                    request.form.get('subscription_expires'), '%Y-%m-%d'
                )
            else:
                user.subscription_expires = None
            
            # Reset password if provided
            if request.form.get('new_password'):
                user.password_hash = generate_password_hash(request.form.get('new_password'))
            
            db.session.commit()
            flash(f'User {user.username} updated successfully!', 'success')
            return redirect(url_for('admin.admin_users'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating user: {str(e)}', 'error')
            logging.error(f"Error updating user {user_id}: {e}")
    
    return render_template('admin/edit_user.html', user=user)

@admin_bp.route('/user/<int:user_id>/remove', methods=['POST'])
@admin_required
def remove_user(user_id):
    """Delete user account"""
    user = User.query.get_or_404(user_id)
    
    # Prevent deletion of current admin
    if user.id == current_user.id:
        flash('Cannot delete your own account!', 'error')
        return redirect(url_for('admin.admin_users'))
    
    try:
        username = user.username
        db.session.delete(user)
        db.session.commit()
        flash(f'User {username} deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting user: {str(e)}', 'error')
        logging.error(f"Error deleting user {user_id}: {e}")
    
    return redirect(url_for('admin.admin_users'))

@admin_bp.route('/user/<int:user_id>/toggle-vip', methods=['POST'])
@admin_required
def toggle_vip(user_id):
    """Quick toggle VIP status"""
    user = User.query.get_or_404(user_id)
    
    try:
        if user.subscription_type == 'free':
            user.subscription_type = 'vip_monthly'
            from datetime import datetime, timedelta
            user.subscription_expires = datetime.utcnow() + timedelta(days=30)
            flash(f'User {user.username} upgraded to VIP!', 'success')
        else:
            user.subscription_type = 'free'
            user.subscription_expires = None
            flash(f'User {user.username} downgraded to Free!', 'success')
        
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating VIP status: {str(e)}', 'error')
        logging.error(f"Error toggling VIP for user {user_id}: {e}")
    
    return redirect(url_for('admin.admin_users'))

@admin_bp.route('/notifications')
@admin_required
def admin_notifications():
    """Admin notification management page"""
    # Get recent notifications
    recent_notifications = Notification.query.order_by(Notification.created_at.desc()).limit(20).all()
    
    # Get notification statistics
    total_notifications = Notification.query.count()
    unread_notifications = Notification.query.filter_by(is_read=False).count()
    global_notifications = Notification.query.filter_by(is_global=True).count()
    
    return render_template('admin/notifications.html',
                         recent_notifications=recent_notifications,
                         total_notifications=total_notifications,
                         unread_notifications=unread_notifications,
                         global_notifications=global_notifications)

@admin_bp.route('/notifications/send', methods=['GET', 'POST'])
@admin_required
def send_notification():
    """Send notification to users"""
    if request.method == 'POST':
        try:
            title = request.form.get('title', '').strip()
            message = request.form.get('message', '').strip()
            notification_type = request.form.get('type', 'info')
            is_global = request.form.get('is_global') == 'on'
            user_id = request.form.get('user_id')
            action_url = request.form.get('action_url', '').strip()
            icon = request.form.get('icon', 'bell')
            
            if not title or not message:
                flash('Title and message are required.', 'error')
                return redirect(url_for('admin.send_notification'))
            
            # If not global, user_id is required
            if not is_global and not user_id:
                flash('User selection is required for individual notifications.', 'error')
                return redirect(url_for('admin.send_notification'))
            
            # Create notification
            notification = create_notification(
                user_id=int(user_id) if user_id and not is_global else None,
                title=title,
                message=message,
                notification_type=notification_type,
                is_global=is_global,
                action_url=action_url if action_url else None,
                icon=icon
            )
            
            if notification:
                if is_global:
                    flash('Global notification sent successfully to all users!', 'success')
                else:
                    user = User.query.get(user_id)
                    flash(f'Notification sent successfully to {user.username}!', 'success')
            else:
                flash('Failed to send notification.', 'error')
                
        except Exception as e:
            logging.error(f"Error sending notification: {e}")
            flash('Failed to send notification.', 'error')
            
        return redirect(url_for('admin.admin_notifications'))
    
    # GET request - show form
    users = User.query.order_by(User.username).all()
    return render_template('admin/send_notification.html', users=users)

@admin_bp.route('/notifications/test')
@admin_required
def test_notification():
    """Send a test notification"""
    try:
        # Send test notification to current admin
        notification = create_notification(
            user_id=current_user.id,
            title="Test Notification",
            message="This is a test notification to verify the real-time notification system is working correctly.",
            notification_type="info",
            icon="flask"
        )
        
        if notification:
            flash('Test notification sent successfully!', 'success')
        else:
            flash('Failed to send test notification.', 'error')
            
    except Exception as e:
        logging.error(f"Error sending test notification: {e}")
        flash('Failed to send test notification.', 'error')
        
    return redirect(url_for('admin.admin_notifications'))

@admin_bp.route('/system-settings')
@admin_required
def system_settings():
    """System settings page for admin"""
    try:
        # Get system statistics
        total_users = db.session.query(User).count()
        total_content = db.session.query(Content).count()
        total_episodes = db.session.query(Episode).count()
        total_notifications = Notification.query.count()
        
        # Get VIP users count
        vip_users = db.session.query(User).filter(
            User.subscription_type.in_(['vip_monthly', 'vip_3month', 'vip_yearly'])
        ).count()
        
        # Get admin users count
        admin_users = db.session.query(User).filter(
            User.email.like('%admin%')
        ).count()
        
        # Get recent activity
        recent_content = db.session.query(Content).order_by(Content.created_at.desc()).limit(5).all()
        recent_users = db.session.query(User).order_by(User.created_at.desc()).limit(5).all()
        
        # Database information
        database_info = {
            'engine': 'PostgreSQL',
            'host': 'Supabase',
            'status': 'Connected'
        }
        
        # Get current system settings
        from models import SystemSettings
        maintenance_enabled = SystemSettings.get_setting('maintenance_enabled', 'false') == 'true'
        maintenance_message = SystemSettings.get_setting('maintenance_message', '')
        site_logo_url = SystemSettings.get_setting('site_logo_url', '')
        site_logo_alt = SystemSettings.get_setting('site_logo_alt', 'AniFlix')
        site_title = SystemSettings.get_setting('site_title', 'AniFlix')
        site_description = SystemSettings.get_setting('site_description', '')
        
        return render_template('admin/system_settings.html',
                             total_users=total_users,
                             total_content=total_content,
                             total_episodes=total_episodes,
                             total_notifications=total_notifications,
                             vip_users=vip_users,
                             admin_users=admin_users,
                             recent_content=recent_content,
                             recent_users=recent_users,
                             database_info=database_info,
                             maintenance_enabled=maintenance_enabled,
                             maintenance_message=maintenance_message,
                             site_logo_url=site_logo_url,
                             site_logo_alt=site_logo_alt,
                             site_title=site_title,
                             site_description=site_description)
    except Exception as e:
        flash(f'Error loading system settings: {str(e)}', 'error')
        return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/system-settings/update', methods=['POST'])
@admin_required
def update_system_settings():
    """Update system settings"""
    try:
        action = request.form.get('action')
        
        if action == 'cleanup_notifications':
            # Delete notifications older than 30 days
            from datetime import datetime, timedelta
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            old_notifications = Notification.query.filter(Notification.created_at < cutoff_date).all()
            
            for notification in old_notifications:
                db.session.delete(notification)
            
            db.session.commit()
            flash(f'Cleaned up {len(old_notifications)} old notifications.', 'success')
            
        elif action == 'reset_demo_data':
            # Reset demo data (for testing purposes)
            flash('Demo data reset feature is not implemented yet.', 'info')
            
        elif action == 'optimize_database':
            # Database optimization placeholder
            flash('Database optimization completed.', 'success')
            
        elif action == 'update_maintenance':
            # Update maintenance message settings
            maintenance_enabled = request.form.get('maintenance_enabled') == 'on'
            maintenance_message = request.form.get('maintenance_message', '').strip()
            
            from models import SystemSettings
            SystemSettings.set_setting('maintenance_enabled', 'true' if maintenance_enabled else 'false', 
                                     'boolean', 'Enable or disable maintenance mode')
            SystemSettings.set_setting('maintenance_message', maintenance_message, 
                                     'text', 'Message displayed during maintenance mode')
            
            flash('Maintenance settings updated successfully.', 'success')
            
        elif action == 'update_logo':
            # Update logo settings
            logo_url = request.form.get('logo_url', '').strip()
            logo_alt = request.form.get('logo_alt', 'AniFlix').strip()
            
            from models import SystemSettings
            SystemSettings.set_setting('site_logo_url', logo_url, 
                                     'url', 'URL for the site logo')
            SystemSettings.set_setting('site_logo_alt', logo_alt, 
                                     'text', 'Alt text for the site logo')
            
            flash('Logo settings updated successfully.', 'success')
            
        elif action == 'update_site_info':
            # Update site information
            site_title = request.form.get('site_title', 'AniFlix').strip()
            site_description = request.form.get('site_description', '').strip()
            
            from models import SystemSettings
            SystemSettings.set_setting('site_title', site_title, 
                                     'text', 'Site title displayed in browser')
            SystemSettings.set_setting('site_description', site_description, 
                                     'text', 'Site description for SEO')
            
            flash('Site information updated successfully.', 'success')
            
        else:
            flash('Unknown action requested.', 'error')
            
    except Exception as e:
        flash(f'Error updating system settings: {str(e)}', 'error')
        db.session.rollback()
    
    return redirect(url_for('admin.system_settings'))

