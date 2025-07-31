from app import app  # noqa: F401

# Register VIP download blueprint
from vip_downloads import vip_downloads_bp
app.register_blueprint(vip_downloads_bp)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
