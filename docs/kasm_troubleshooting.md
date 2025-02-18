# Kasm Integration Troubleshooting Guide

Below is a step-by-step guide to embedding Kasm into an iframe based on the common issues identified. We'll walk through the main configuration points—correct endpoint setup, authentication, cookie/domain management, and recommended Kasm settings.

## 1. Confirm Kasm Server Configuration

### 1.1 Check the Running Port
- **Default Ports**: In many Kasm deployments, the service might be listening on port `8443` (default) or `443` (if using a reverse proxy or if you've reconfigured Kasm).  
- **Avoid Using 8000**: If you see `:8000` in your logs, confirm whether that port is actually running and publicly accessible.  
- **Firewall and Network Configuration**: Ensure there are no firewalls or security group rules blocking the port you've configured.

> **Tip**: Try to open `https://<your_kasm_server>:8443` or `https://<your_kasm_server>:443` in your browser. If Kasm responds, that's likely your correct port.

### 1.2 Verify Certificates (If Using HTTPS)
- If you're using **self-signed certificates**, your browser or proxy might block or distrust them. Either import the self-signed cert into your local trust store or consider using valid certificates through Let's Encrypt or another CA.  
- For more details, see the [Kasm Certificate Management Docs](https://www.kasmweb.com/docs/latest/how_to/certificates.html).

## 2. Generate / Verify Kasm Credentials

If you plan to authenticate via API (e.g., calling `/api/authenticate` to get a token):

1. **Create a Kasm User**  
   - Go to your Kasm Admin Panel → "Users" → "Create New User" (or confirm an existing user).  
   - Make sure you have a valid username and password that you can test in your authentication script.

2. **(Optional) API Keys**  
   - If you want to use API Keys instead of username/password, you must:
     1. Go to Kasm Admin → "Users" → Click on the user → "API Keys".  
     2. Generate a new API key and secret.  
   - In your application, you'll send `api_key` and `api_secret` in the JSON body to `/api/authenticate`.

3. **Confirm the Credentials**  
   - Use a tool like `curl` or [Postman](https://www.postman.com/) to test authentication directly:  
     ```bash
     curl -k -X POST "https://<your_kasm_server>:443/api/authenticate" \
          -H "Content-Type: application/json" \
          -d '{
                "username":"<your_kasm_username>",
                "password":"<your_kasm_password>"
              }'
     ```
   - If you receive a `200` JSON response with a token, your credentials and port are correct.  
   - If `403 Forbidden`, there's a mismatch in credentials or you need to check logs in Kasm.

## 3. Configure the Auth Domain (Crucial for Iframe Embedding)

By default, Kasm sets the `Auth Cookie` domain to the server's hostname. When embedding Kasm in an iframe served from a different subdomain, the cookie might be rejected unless you adjust the **Kasm Auth Domain**.

1. **Open Kasm Admin Panel**  
   - Navigate to "Settings" → "Global Settings" → "Auth Settings".

2. **Set the Auth Domain**  
   - If your parent app is at `app.example.com` and Kasm is at `kasm.example.com`, set the Auth Domain to `.example.com` (leading `.` to allow subdomains).  
   - Save changes and restart Kasm if prompted.

3. **Result**: Kasm now issues cookies valid for `*.example.com`, allowing the parent domain to share cookies with the iframe domain.

## 4. Set Up Your External Reverse Proxy (Development)

For local development using Vite as a proxy to forward requests to Kasm:

1. **Proxy Pass Configuration in `vite.config.js`**:  
   ```javascript
   server: {
     proxy: {
       '/kasm-proxy': {
         target: 'https://34.136.51.93:443',
         changeOrigin: true,
         secure: false, // if using self-signed SSL
         ws: true,
         rewrite: (path) => path.replace(/^\/kasm-proxy/, ''),
         headers: {
           'Origin': 'http://localhost:5173',
           'Referer': 'http://localhost:5173/'
         },
         configure: (proxy, _options) => {
           proxy.on('proxyReq', (proxyReq, req, _res) => {
             proxyReq.setHeader('Host', '34.136.51.93');
           });
         }
       }
     }
   }
   ```

2. **Check Host Headers**  
   - Make sure you're passing the `Host` header correctly. Kasm uses the host to validate the cookie domain.  
   - If you notice authentication issues, confirm that your proxy isn't stripping or altering auth headers.

3. **Test the Proxy**  
   - Open `http://localhost:5173/kasm-proxy/api/authenticate` in your browser.  
   - You should see either a JSON body or be able to successfully post credentials.

## 5. Frontend Code Configuration

### 5.1 Kasm API Client (`kasm-api.js`)

```javascript
class KasmAPI {
    constructor(config = {}) {
        const isDevelopment = window.location.hostname === 'localhost';
        this.baseUrl = isDevelopment ? '/kasm-proxy' : 'https://34.136.51.93:443';
        this.authDomain = config.authDomain || '34.136.51.93';
        this.credentials = {
            username: config.username || '',
            password: config.password || '',
            apiKey: config.apiKey || '',
            apiKeySecret: config.apiKeySecret || ''
        };
    }

    async authenticate() {
        try {
            const headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Origin': window.location.origin,
                'Host': window.location.host
            };

            const response = await fetch(`${this.baseUrl}/api/authenticate`, {
                method: 'POST',
                headers: headers,
                body: JSON.stringify({
                    username: this.credentials.username,
                    password: this.credentials.password
                }),
                credentials: 'include'
            });

            if (!response.ok) {
                throw new Error('Authentication failed');
            }

            return await response.json();
        } catch (error) {
            console.error('Authentication error:', error);
            throw error;
        }
    }
}
```

### 5.2 Kasm Initialization (`kasm.js`)

```javascript
const isDevelopment = window.location.hostname === 'localhost';
const kasmBaseUrl = isDevelopment ? '/kasm-proxy' : 'https://34.136.51.93:443';

const kasmApi = new KasmAPI({
    baseUrl: kasmBaseUrl,
    authDomain: isDevelopment ? `localhost:5173` : '34.136.51.93',
    username: 'user@kasm.com',
    password: 'Zigral@3.0',
    apiKey: 'Z3F7mSYzOx8B',
    apiKeySecret: 'fLYL0c5qG8OPPS5N55cbW65JvOsGYWqH'
});

// Set required iframe permissions
kasmIframe.allow = [
    'autoplay',
    'clipboard-read',
    'clipboard-write',
    'camera',
    'microphone'
].join('; ');

// Set sandbox attributes
kasmIframe.sandbox = [
    'allow-scripts',
    'allow-forms',
    'allow-popups',
    'allow-modals',
    'allow-downloads',
    'allow-same-origin',
    'allow-top-navigation-by-user-activation'
].join(' ');
```

## 6. Troubleshooting Common Issues

### 6.1 Authentication Errors (403 Forbidden)

If you see a 403 Forbidden response when trying to authenticate:

1. **Check Credentials**
   - Verify username/password or API key/secret are correct
   - Test credentials directly against Kasm server using curl/Postman

2. **Check Headers**
   - Ensure all required headers are being sent:
     - Content-Type: application/json
     - Accept: application/json
     - Origin: (your frontend origin)
     - Host: (your Kasm server host)

3. **Check Proxy Configuration**
   - Verify the proxy is correctly forwarding requests
   - Check that headers aren't being stripped
   - Ensure the Host header is set correctly

### 6.2 Connection Timeouts

If you're seeing connection timeouts:

1. **Port Configuration**
   - Verify Kasm is actually running on port 443
   - Check firewall rules allow access to port 443
   - Try accessing Kasm directly in browser

2. **SSL/TLS Issues**
   - If using self-signed certificates, ensure they're trusted
   - Check if secure: false is needed in proxy config
   - Verify SSL certificate is valid for the domain

### 6.3 Iframe Loading Issues

If the iframe fails to load or shows errors:

1. **Cookie Problems**
   - Check Auth Domain configuration in Kasm
   - Verify cookies are being set correctly
   - Check browser's cookie settings

2. **Sandbox Permissions**
   - Ensure all required sandbox attributes are set
   - Check if browser is blocking features
   - Verify allow attributes for camera/mic if needed

## 7. Useful Commands for Debugging

### 7.1 Test Kasm Authentication
```bash
curl -k -X POST "https://34.136.51.93:443/api/authenticate" \
     -H "Content-Type: application/json" \
     -d '{
           "username":"user@kasm.com",
           "password":"Zigral@3.0"
         }'
```

### 7.2 Check Kasm Server Status
```bash
curl -k -I https://34.136.51.93:443
```

### 7.3 Test WebSocket Connection
```bash
wscat -c "wss://34.136.51.93:443/api/ws"
```

## 8. Reference Documentation

- [Embedding in an Iframe](https://www.kasmweb.com/docs/latest/how_to/embed_kasm_in_iframe.html)
- [External Proxy Setup](https://www.kasmweb.com/docs/latest/how_to/external_proxy.html)
- [Kasm Developer API](https://www.kasmweb.com/docs/latest/developers/developer_api.html)
- [Certificate Management](https://www.kasmweb.com/docs/latest/how_to/certificates.html)

## Final Checklist

1. **Server Configuration**
   - [ ] Correct port (443) is being used
   - [ ] SSL certificates are valid
   - [ ] Firewall allows access

2. **Authentication**
   - [ ] Credentials are correct
   - [ ] API keys are valid
   - [ ] Headers are properly set

3. **Proxy Setup**
   - [ ] Vite proxy is configured correctly
   - [ ] Headers are being forwarded
   - [ ] WebSocket support is enabled

4. **Iframe Configuration**
   - [ ] Sandbox attributes are set
   - [ ] Allow attributes are configured
   - [ ] Auth domain is properly set

5. **Browser Settings**
   - [ ] Third-party cookies are allowed
   - [ ] Mixed content is not blocked
   - [ ] Certificates are trusted 