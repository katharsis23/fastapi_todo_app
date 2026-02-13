# 🛡️ Nginx Reverse Proxy Setup

This directory contains the Nginx configuration for the FastAPI Todo & Notes application reverse proxy.

## 📁 Files

- `nginx.conf` - Main Nginx configuration with security features
- `Dockerfile` - Docker image for Nginx
- `README.md` - This documentation

## 🚀 Quick Start

### Using Docker Compose (Recommended)

```bash
# Start all services including Nginx
docker-compose up -d

# Check Nginx logs
docker-compose logs -f nginx

# Test the proxy
curl http://localhost/api/health
```

### Manual Nginx Setup

```bash
# Copy configuration to Nginx
sudo cp nginx.conf /etc/nginx/sites-available/fastapi-app
sudo ln -s /etc/nginx/sites-available/fastapi-app /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

## 🔧 Configuration Details

### Security Features

#### HTTP Headers
- **X-Frame-Options**: Prevents clickjacking
- **X-Content-Type-Options**: Prevents MIME-type sniffing
- **X-XSS-Protection**: Enables XSS protection
- **Content-Security-Policy**: Controls resource loading
- **Server Tokens**: Hides Nginx version

#### Rate Limiting
- **General API**: 10 requests/second
- **Authentication**: 5 requests/second
- **File Upload**: 5 requests/second

#### Request Limits
- **Max Body Size**: 10MB for file uploads
- **Timeouts**: 30s for most requests, 60s for uploads

### URL Mapping

| Path | Backend | Rate Limit | Notes |
|------|---------|------------|-------|
| `/api/` | FastAPI `/` | 10r/s | General API endpoints |
| `/api/auth/` | FastAPI `/auth/` | 5r/s | Authentication endpoints |
| `/api/user/login` | FastAPI `/user/login` | 5r/s | Login endpoint |
| `/api/user/register` | FastAPI `/user/register` | 5r/s | Registration endpoint |
| `/api/user/avatar` | FastAPI `/user/avatar` | 5r/s | File upload (10MB) |
| `/health` | FastAPI `/health` | None | Health checks |
| `/docs` | FastAPI `/docs` | None | API documentation |
| `/redoc` | FastAPI `/redoc` | None | Alternative docs |

## 🔒 Security Considerations

### Production Recommendations

1. **Restrict Documentation Access**
   ```nginx
   location /docs {
       allow 127.0.0.1;
       allow 10.0.0.0/8;  # Your internal network
       deny all;
       
       proxy_pass http://fastapi_backend/docs;
       # ... other proxy settings
   }
   ```

2. **Enable HTTPS**
   ```nginx
   server {
       listen 443 ssl http2;
       server_name yourdomain.com;
       
       ssl_certificate /path/to/cert.pem;
       ssl_certificate_key /path/to/key.pem;
       
       # SSL configuration
       ssl_protocols TLSv1.2 TLSv1.3;
       ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
       ssl_prefer_server_ciphers off;
       
       # ... other configuration
   }
   
   # Redirect HTTP to HTTPS
   server {
       listen 80;
       server_name yourdomain.com;
       return 301 https://$server_name$request_uri;
   }
   ```

3. **Add Fail2Ban Integration**
   ```bash
   # Create Nginx log pattern for Fail2Ban
   sudo nano /etc/fail2ban/filter.d/nginx-api.conf
   ```

4. **Monitor Logs**
   ```bash
   # Real-time monitoring
   tail -f /var/log/nginx/access.log | grep -E "(POST|PUT|DELETE)"
   
   # Error monitoring
   tail -f /var/log/nginx/error.log
   ```

## 📊 Monitoring

### Health Checks

Nginx includes built-in health checks:

```bash
# Check if Nginx is running
docker-compose exec nginx wget --quiet --tries=1 --spider http://localhost/health

# Check backend health through proxy
curl http://localhost/api/health
```

### Log Analysis

```bash
# View access logs
docker-compose logs nginx

# View error logs
docker-compose logs nginx | grep ERROR

# Monitor rate limiting
docker-compose logs nginx | grep "limiting"
```

## 🚨 Troubleshooting

### Common Issues

#### 502 Bad Gateway
```bash
# Check if backend is running
docker-compose ps backend

# Check backend logs
docker-compose logs backend

# Check Nginx configuration
docker-compose exec nginx nginx -t
```

#### 504 Gateway Timeout
```bash
# Increase timeout in nginx.conf
proxy_read_timeout 60s;
proxy_send_timeout 60s;
```

#### Rate Limiting Issues
```bash
# Check rate limiting logs
docker-compose logs nginx | grep "limiting requests"

# Adjust rate limits in nginx.conf
limit_req_zone $binary_remote_addr zone=api:10m rate=20r/s;
```

### Performance Tuning

#### Worker Connections
```nginx
events {
    worker_connections 2048;  # Increase from 1024
}
```

#### Gzip Compression
```nginx
gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_types text/plain application/json application/javascript;
```

#### Caching
```nginx
location /static/ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

## 🔄 Updates

### Updating Nginx Configuration

```bash
# Edit configuration
nano nginx/nginx.conf

# Test configuration
docker-compose exec nginx nginx -t

# Restart Nginx
docker-compose restart nginx
```

### Rebuilding Docker Image

```bash
# Rebuild Nginx image
docker-compose build nginx

# Restart with new image
docker-compose up -d nginx
```

## 📚 Additional Resources

- [Nginx Documentation](https://nginx.org/en/docs/)
- [Rate Limiting Guide](https://nginx.org/en/docs/http/ngx_http_limit_req_module.html)
- [Security Best Practices](https://nginx.org/en/docs/http/request_processing.html)

## 🆘 Support

For issues with the Nginx configuration:

1. Check the logs: `docker-compose logs nginx`
2. Verify configuration: `docker-compose exec nginx nginx -t`
3. Test backend connectivity: `curl http://localhost:8000/health`
4. Create an issue with detailed error information
