# Network Setup Guide - Accessing Attendance System from Employee Laptops

## ✅ Good News!

Your application is **already configured correctly**! The camera access is **client-side**, which means:
- When employees access the attendance page from their laptops, **their laptop's camera** will be used
- The server (Ubuntu Linux) does NOT need a camera
- Face recognition happens on the server, but camera capture happens on the employee's device

## 🔧 Setup Steps

### Step 1: Find Your Server's IP Address

Run this command on your Ubuntu server:
```bash
./get_server_ip.sh
```

Or manually:
```bash
hostname -I | awk '{print $1}'
```

This will show your server's IP address (e.g., `192.168.1.100`)

### Step 2: Configure Firewall (if needed)

If employees can't access the server, you may need to allow port 5000 through the firewall:

**For UFW (Ubuntu Firewall):**
```bash
sudo ufw allow 5000/tcp
sudo ufw status
```

**For firewalld (if using):**
```bash
sudo firewall-cmd --permanent --add-port=5000/tcp
sudo firewall-cmd --reload
```

### Step 3: Start the Flask Application

Make sure your Flask app is running:
```bash
python app.py
```

You should see:
```
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000
 * Running on http://YOUR_IP:5000
```

### Step 4: Access from Employee Laptops

On employee laptops, open a web browser and go to:
```
http://YOUR_SERVER_IP:5000/attendance
```

**Example:** If your server IP is `192.168.1.100`, employees should access:
```
http://192.168.1.100:5000/attendance
```

## 📱 Important Notes

1. **Same Network Required**: Employee laptops must be on the same network (same WiFi/router) as the server
2. **Camera Permissions**: When employees first access the page, their browser will ask for camera permission - they need to allow it
3. **HTTPS Consideration**: For production, consider using HTTPS. For now, HTTP works fine on local networks
4. **Browser Compatibility**: Modern browsers (Chrome, Firefox, Edge) support camera access via WebRTC

## 🔍 Troubleshooting

### Employees can't access the server:
- Check if server and laptops are on the same network
- Verify firewall allows port 5000
- Try pinging the server IP from employee laptop: `ping YOUR_SERVER_IP`

### Camera not working on employee laptops:
- Check browser permissions (Settings > Privacy > Camera)
- Make sure they're using HTTPS or localhost (some browsers require HTTPS for camera access on remote IPs)
- Try a different browser

### Face recognition not working:
- Make sure employees are registered in the system
- Check server logs for errors
- Ensure good lighting and clear face visibility

## 🌐 For Remote Access (Different Networks)

If employees need to access from different networks (not same WiFi):
1. Set up port forwarding on your router
2. Use your public IP address
3. **Important**: Consider using HTTPS and authentication for security
