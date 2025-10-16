#!/bin/bash
# Deployment script for DigitalOcean Ubuntu 22.04 Droplet
# Run this on your DigitalOcean server after SSH'ing in

set -e  # Exit on any error

echo "=========================================="
echo "Universal Video Downloader - DigitalOcean Deployment"
echo "=========================================="

# Update system
echo "[1/8] Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Install Python and dependencies
echo "[2/8] Installing Python and build tools..."
sudo apt-get install -y python3 python3-pip python3-venv git nginx supervisor

# Install FFmpeg (required for audio conversion)
echo "[3/8] Installing FFmpeg..."
sudo apt-get install -y ffmpeg

# Clone repository
echo "[4/8] Cloning repository..."
cd /opt
sudo git clone https://github.com/smith505/VideoDownloader.git
sudo chown -R $USER:$USER /opt/VideoDownloader
cd /opt/VideoDownloader

# Create virtual environment
echo "[5/8] Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "[6/8] Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn

# Create systemd service
echo "[7/8] Creating systemd service..."
sudo tee /etc/systemd/system/videodownloader.service > /dev/null <<EOF
[Unit]
Description=Universal Video Downloader
After=network.target

[Service]
Type=notify
User=$USER
WorkingDirectory=/opt/VideoDownloader
Environment="PATH=/opt/VideoDownloader/venv/bin"
Environment="PORT=5000"
ExecStart=/opt/VideoDownloader/venv/bin/gunicorn --workers 3 --bind 0.0.0.0:5000 --timeout 300 app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Configure Nginx
echo "[8/8] Configuring Nginx..."
sudo tee /etc/nginx/sites-available/videodownloader > /dev/null <<'EOF'
server {
    listen 80;
    server_name universalvideodownloader.org www.universalvideodownloader.org;

    client_max_body_size 500M;
    proxy_read_timeout 300;
    proxy_connect_timeout 300;
    proxy_send_timeout 300;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/videodownloader /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

# Start service
sudo systemctl daemon-reload
sudo systemctl enable videodownloader
sudo systemctl start videodownloader

echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "Your app is now running on port 5000"
echo "Nginx is proxying traffic from port 80"
echo ""
echo "Useful commands:"
echo "  - Check status: sudo systemctl status videodownloader"
echo "  - View logs: sudo journalctl -u videodownloader -f"
echo "  - Restart app: sudo systemctl restart videodownloader"
echo "  - Update code: cd /opt/VideoDownloader && git pull && sudo systemctl restart videodownloader"
echo ""
echo "Next steps:"
echo "1. Point your domain DNS to this server's IP"
echo "2. Set up SSL certificate: sudo apt install certbot python3-certbot-nginx && sudo certbot --nginx -d universalvideodownloader.org -d www.universalvideodownloader.org"
echo ""
