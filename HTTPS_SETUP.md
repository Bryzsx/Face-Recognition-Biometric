# HTTPS Setup Guide - Fix Camera Access Issue

## Problem
Modern browsers (Chrome, Firefox, Edge) **require HTTPS** for camera access when accessing via IP address (not localhost). This is a security feature.

When employees access `http://192.168.1.14:5000/attendance`, the browser blocks camera access.

## Solution Options

### Option 1: Quick Test - Use Chrome Flag (Development Only)

**⚠️ WARNING: Only for testing/development. Not secure for production.**

1. On employee laptops, open Chrome
2. Go to: `chrome://flags/#unsafely-treat-insecure-origin-as-secure`
3. Add your server IP: `http://192.168.1.14:5000`
4. Set the flag to **Enabled**
5. Restart Chrome
6. Now camera should work

**Note:** This is NOT recommended for production. Use only for testing.

---

### Option 2: Set Up HTTPS with Self-Signed Certificate (Recommended for Local Network)

#### Step 1: Generate Self-Signed Certificate

On your Ubuntu server, run:

```bash
# Install openssl if not already installed
sudo apt-get update
sudo apt-get install openssl

# Create a directory for certificates
mkdir -p /home/zupteddy/Documents/Face-Recognition-Biometric/certs
cd /home/zupteddy/Documents/Face-Recognition-Biometric/certs

# Generate private key
openssl genrsa -out server.key 2048

# Generate certificate (valid for 365 days)
openssl req -new -x509 -key server.key -out server.crt -days 365 -subj "/CN=192.168.1.14"
```

#### Step 2: Update Flask App to Use HTTPS

Update `app.py` at the bottom:

```python
if __name__ == "__main__":
    # Run with HTTPS
    app.run(
        host="0.0.0.0", 
        port=5000, 
        debug=True, 
        threaded=True,
        ssl_context=('certs/server.crt', 'certs/server.key')
    )
```

#### Step 3: Access via HTTPS

Employees should now access:
```
https://192.168.1.14:5000/attendance
```

**Note:** Browser will show a security warning (because it's self-signed). Click "Advanced" → "Proceed to 192.168.1.14 (unsafe)" to continue.

---

### Option 3: Use ngrok (Easiest for Testing)

ngrok creates a secure HTTPS tunnel to your local server.

#### Step 1: Install ngrok

```bash
# Download ngrok
wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz
tar xvzf ngrok-v3-stable-linux-amd64.tgz
sudo mv ngrok /usr/local/bin/

# Or use snap
sudo snap install ngrok
```

#### Step 2: Start Flask App

```bash
python app.py
```

#### Step 3: In another terminal, start ngrok

```bash
ngrok http 5000
```

This will give you an HTTPS URL like:
```
https://abc123.ngrok.io
```

#### Step 4: Access via ngrok URL

Employees access:
```
https://abc123.ngrok.io/attendance
```

**Note:** Free ngrok URLs change each time you restart. For permanent URL, you need a paid plan.

---

### Option 4: Use Reverse Proxy (Nginx) with Let's Encrypt (Production)

For production use, set up Nginx with Let's Encrypt SSL certificate.

#### Step 1: Install Nginx

```bash
sudo apt-get install nginx
```

#### Step 2: Configure Nginx

Create `/etc/nginx/sites-available/face-recognition`:

```nginx
server {
    listen 80;
    server_name 192.168.1.14;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable it:
```bash
sudo ln -s /etc/nginx/sites-available/face-recognition /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### Step 3: Install Certbot and Get SSL Certificate

```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d 192.168.1.14
```

**Note:** Let's Encrypt requires a public domain name. For local network, use Option 2 (self-signed) instead.

---

## Quick Fix Summary

**For immediate testing:**
1. Use Chrome flag (Option 1) - Quick but not secure
2. Use ngrok (Option 3) - Easy and secure, but URL changes

**For production/local network:**
1. Use self-signed certificate (Option 2) - Best for local network
2. Set up Nginx with SSL (Option 4) - Best for production with domain

---

## After Setting Up HTTPS

1. Update employee access URL to use `https://` instead of `http://`
2. If using self-signed certificate, employees need to accept the security warning once
3. Camera should now work!
