import time
import threading
import os
import tempfile
from flask import Response, request, jsonify
import mimetypes
import requests
import uuid
import json
import logging
import urllib.parse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TorrentStreamer:
    def __init__(self, download_path=None):
        """Initialize Python-based torrent streaming service"""
        self.download_path = download_path or tempfile.mkdtemp()
        self.streaming_sessions = {}
        
        # Ensure download directory exists
        os.makedirs(self.download_path, exist_ok=True)
        
        logger.info(f"TorrentStreamer initialized with download path: {self.download_path}")
    
    def create_streaming_session(self, magnet_link, session_id=None):
        """Create a new streaming session"""
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Store session info
        self.streaming_sessions[session_id] = {
            'magnet': magnet_link,
            'status': 'ready',
            'created_at': time.time(),
            'streaming_urls': self._generate_streaming_urls(magnet_link)
        }
        
        logger.info(f"Created streaming session: {session_id}")
        return session_id
    
    def _generate_streaming_urls(self, magnet_link):
        """Generate streaming URLs for various services"""
        encoded_magnet = urllib.parse.quote(magnet_link, safe='')
        
        return {
            'webtor': f"https://webtor.io/embed?magnet={encoded_magnet}&controls=true&autoplay=false",
            'instant': f"https://instant.io/#{magnet_link}",
            'btorrent': f"https://btorrent.xyz/#{magnet_link}",
            'seedr': f"https://www.seedr.cc/?magnet={encoded_magnet}",
            'zbigz': f"https://zbigz.com/?magnet={encoded_magnet}"
        }
    
    def get_session_status(self, session_id):
        """Get streaming session status"""
        if session_id not in self.streaming_sessions:
            return {'error': 'Session not found'}
        
        session = self.streaming_sessions[session_id]
        return {
            'session_id': session_id,
            'status': session['status'],
            'created_at': session['created_at'],
            'streaming_urls': session['streaming_urls'],
            'age_minutes': round((time.time() - session['created_at']) / 60, 1)
        }
    
    def get_streaming_url(self, session_id, service='webtor'):
        """Get streaming URL for specific service"""
        if session_id not in self.streaming_sessions:
            return None
        
        session = self.streaming_sessions[session_id]
        return session['streaming_urls'].get(service)
    
    def cleanup_old_sessions(self, max_age_hours=2):
        """Clean up old streaming sessions"""
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        sessions_to_remove = []
        for session_id, session in self.streaming_sessions.items():
            if current_time - session['created_at'] > max_age_seconds:
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            del self.streaming_sessions[session_id]
            logger.info(f"Cleaned up old session: {session_id}")
        
        return len(sessions_to_remove)
    
    def create_proxy_stream(self, session_id, service='webtor'):
        """Create a proxy stream (for future implementation)"""
        streaming_url = self.get_streaming_url(session_id, service)
        if not streaming_url:
            return None
        
        return {
            'proxy_url': f"/torrent/proxy/{session_id}/{service}",
            'direct_url': streaming_url,
            'service': service
        }


# Global streamer instance
streamer = TorrentStreamer()

# Flask routes for torrent streaming
def create_torrent_routes(app):
    """Create Flask routes for torrent streaming"""
    
    @app.route('/torrent/create-session', methods=['POST'])
    def create_torrent_session():
        """Create new torrent streaming session"""
        try:
            data = request.get_json()
            magnet_link = data.get('magnet')
            
            if not magnet_link:
                return jsonify({'error': 'Magnet link required'}), 400
            
            # Create streaming session
            session_id = streamer.create_streaming_session(magnet_link)
            session_info = streamer.get_session_status(session_id)
            
            return jsonify({
                'success': True,
                'session_id': session_id,
                'session_info': session_info,
                'message': 'Streaming session created successfully'
            })
            
        except Exception as e:
            logger.error(f"Error creating torrent session: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/torrent/session/<session_id>')
    def get_session_info(session_id):
        """Get streaming session information"""
        try:
            session_info = streamer.get_session_status(session_id)
            return jsonify(session_info)
        except Exception as e:
            logger.error(f"Error getting session info: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/torrent/stream/<session_id>')
    @app.route('/torrent/stream/<session_id>/<service>')
    def get_streaming_info(session_id, service='webtor'):
        """Get streaming information for session"""
        try:
            streaming_url = streamer.get_streaming_url(session_id, service)
            if not streaming_url:
                return jsonify({'error': 'Streaming URL not found'}), 404
            
            proxy_info = streamer.create_proxy_stream(session_id, service)
            
            return jsonify({
                'session_id': session_id,
                'service': service,
                'streaming_url': streaming_url,
                'proxy_info': proxy_info,
                'available_services': list(streamer.streaming_sessions[session_id]['streaming_urls'].keys())
            })
            
        except Exception as e:
            logger.error(f"Error getting streaming info: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/torrent/proxy/<session_id>/<service>')
    def proxy_stream(session_id, service):
        """Proxy stream from external service (future implementation)"""
        try:
            streaming_url = streamer.get_streaming_url(session_id, service)
            if not streaming_url:
                return "Stream not found", 404
            
            # For now, redirect to external service
            # In future, could implement actual proxying
            return f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>AniFlix Torrent Stream</title>
                <style>
                    body {{ margin: 0; padding: 0; background: #000; }}
                    iframe {{ width: 100vw; height: 100vh; border: none; }}
                </style>
            </head>
            <body>
                <iframe src="{streaming_url}" allowfullscreen></iframe>
            </body>
            </html>
            """
            
        except Exception as e:
            logger.error(f"Error proxying stream: {e}")
            return str(e), 500
    
    @app.route('/torrent/cleanup', methods=['POST'])
    def cleanup_sessions():
        """Cleanup old torrent sessions"""
        try:
            max_age = request.json.get('max_age_hours', 2) if request.is_json else 2
            cleaned_count = streamer.cleanup_old_sessions(max_age)
            
            return jsonify({
                'success': True,
                'cleaned_sessions': cleaned_count,
                'message': f'Cleaned up {cleaned_count} old sessions'
            })
            
        except Exception as e:
            logger.error(f"Error cleaning up sessions: {e}")
            return jsonify({'error': str(e)}), 500


# Test function
def test_torrent_streamer():
    """Test the torrent streamer"""
    try:
        test_magnet = "magnet:?xt=urn:btih:TIVVXAOK3HWTVYJJJB3EXPEMAWEIUSGC"
        session_id = streamer.create_streaming_session(test_magnet)
        session_info = streamer.get_session_status(session_id)
        
        print("TorrentStreamer test successful:")
        print(f"Session ID: {session_id}")
        print(f"Session Info: {json.dumps(session_info, indent=2)}")
        
        return True
    except Exception as e:
        print(f"TorrentStreamer test failed: {e}")
        return False


if __name__ == '__main__':
    test_torrent_streamer()