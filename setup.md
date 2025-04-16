# Flask App with Nginx, SSL, Route 53, and Slack Setup Guide

This guide will walk you through deploying a Flask app on an EC2 instance, setting it up behind Nginx with SSL using Certbot, configuring Route 53 for domain management, and configuring the Slack app to send slash commands to your Flask API.

## Prerequisites

- EC2 instance running Amazon Linux 2 (or another Linux distribution)
- A registered domain and AWS Route 53 hosted zone
- Slack workspace with permissions to create a Slack app
- SSH access to the EC2 instance
- Domain DNS configured in Route 53

## 1. Install Dependencies

On your EC2 instance, install the necessary dependencies:

```bash
sudo yum update -y
sudo yum install -y python3 python3-pip nginx git
```

Install Flask and any other dependencies:

```bash
pip3 install flask
/usr/local/bin/python3 -m pip install --user boto3
```

## 2. Flask App Setup

Create your Flask app. For this guide, let's assume your app is simple:

```python
# /home/ec2-user/flaskapp/app.py
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/", methods=["POST"])
def handle_slash_command():
    text = request.form.get("text")
    response = {
        "response_type": "in_channel",
        "text": f"Received text: {text}"
    }
    return jsonify(response)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
```

## 3. Create a Systemd Service for the Flask App

Create a systemd service to run the Flask app automatically:

```bash
sudo nano /etc/systemd/system/flaskapp.service
```

Add the following content:

```ini
[Unit]
Description=Flask App for Slack Slash Command
After=network.target

[Service]
User=ec2-user
WorkingDirectory=/home/ec2-user/flaskapp
ExecStart=/usr/bin/python3 /home/ec2-user/flaskapp/app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable flaskapp
sudo systemctl start flaskapp
```

## 4. Install Nginx

Install Nginx:

```bash
sudo yum install -y nginx
```

Create an Nginx configuration file for the Flask app:

```bash
sudo nano /etc/nginx/conf.d/flaskapp.conf
```

Add the following configuration:

```nginx
server {
    listen 80;
    server_name sdeflaskapp.impact-ops.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 8. Set Up Route 53 DNS

1. Go to the AWS Route 53 console and select your hosted zone.
2. Add an A record for your subdomain (sdeflaskapp.impact-ops.com) pointing to your EC2 instance's public IP.

For example:
- Name: sdeflaskapp.impact-ops.com
- Type: A
- Value: 35.162.25.142 (your EC2 instance's public IP)

## 5. Obtain SSL Certificate with Certbot

Install Certbot:

```bash
sudo amazon-linux-extras install epel -y
sudo yum install -y certbot
sudo pip3 install certbot-nginx
sudo ln -s /usr/local/bin/certbot /usr/bin/certbot
```

Run Certbot to obtain an SSL certificate for your domain:

```bash
sudo certbot --nginx -d sdeflaskapp.impact-ops.com
```

Certbot will automatically configure Nginx with SSL settings and obtain the certificates. Follow the prompts to configure the SSL certificate.

## 6. Manual Certificate File Setup (if necessary)

If Certbot doesn't automatically configure Nginx or you prefer manual steps, you can add the certificate files to the proper locations:

Certbot typically stores certificates in `/etc/letsencrypt/live/sdeflaskapp.impact-ops.com/`:
- `cert.pem` (server certificate)
- `chain.pem` (intermediate certificate)
- `fullchain.pem` (combined cert)
- `privkey.pem` (private key)

Copy these files to the Nginx SSL configuration.

Update your Nginx configuration file (`/etc/nginx/conf.d/flaskapp.conf`) to use the SSL certificate:

```nginx
server {
    listen 80;
    server_name sdeflaskapp.impact-ops.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

server {
    listen 443 ssl;
    server_name sdeflaskapp.impact-ops.com;

    ssl_certificate /etc/letsencrypt/live/sdeflaskapp.impact-ops.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/sdeflaskapp.impact-ops.com/privkey.pem;
    ssl_trusted_certificate /etc/letsencrypt/live/sdeflaskapp.impact-ops.com/chain.pem;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 7. Restart Nginx

After updating the configuration, test and restart Nginx:

```bash
sudo nginx -t
sudo systemctl restart nginx
```
## 9. Set SELinux for Networking Access

If you're getting a "502 Bad Gateway" error, you may need to adjust SELinux settings to allow Nginx to connect to the Flask app:

```bash
sudo setsebool -P httpd_can_network_connect 1
```

## 10. Slack App Configuration

Now that your Flask app is live, you need to configure a Slack app to send slash commands to your Flask API. Here's how you can do that:

### Create a Slack App
1. Go to the [Slack API](https://api.slack.com/apps) and click **Create New App**.
2. Choose "From scratch" and select a workspace where the app will be installed.
3. Name your app and click **Create App**.

### Set Up Slash Command
1. In the Slack App settings, go to **Slash Commands** under the Features section.
2. Click **Create New Command**.
3. Enter the following details:
   - Command: `/your-command-name` (this is the command users will type in Slack).
   - Request URL: `https://sdeflaskapp.impact-ops.com/` (this is the endpoint where Slack will send requests).
   - Short Description: A brief description of what the command does.
   - Usage Hint: Optional instructions for users.
4. Click **Save**.

### Enable Event Subscriptions (optional)
If you want your Slack app to respond to events (such as mentions or messages), go to **Event Subscriptions** under the Features section. Enable events and provide your app's endpoint.

## 11. Test the Setup

You can test the setup by sending a POST request to your domain:

```bash
curl -X POST https://sdeflaskapp.impact-ops.com/ -d "text=start"
```

Additionally, in Slack, you can test by typing the configured slash command, for example `/your-command-name`. Your Flask app should respond with a message indicating it received the input.

## Conclusion

You've successfully deployed your Flask app on an EC2 instance with Nginx as a reverse proxy, SSL via Certbot, and DNS management using Route 53. The Flask app is running as a service, ensuring it restarts automatically. The Slack app has been configured to send slash commands to your Flask API.