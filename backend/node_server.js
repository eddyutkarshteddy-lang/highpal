const http = require('http');
const fs = require('fs');
const path = require('path');

const server = http.createServer((req, res) => {
    console.log(`${req.method} ${req.url}`);
    
    // CORS headers
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', '*');
    
    if (req.method === 'OPTIONS') {
        res.writeHead(200);
        res.end();
        return;
    }
    
    const urlPath = req.url.split('?')[0];
    
    if (req.method === 'GET') {
        if (urlPath === '/health') {
            res.writeHead(200, { 'Content-Type': 'application/json' });
            res.end('{"status": "healthy", "message": "Node.js server running"}');
        } else if (urlPath === '/admin') {
            try {
                const adminHtml = fs.readFileSync('./admin.html', 'utf8');
                res.writeHead(200, { 'Content-Type': 'text/html' });
                res.end(adminHtml);
            } catch (error) {
                res.writeHead(404);
                res.end('Admin page not found');
            }
        } else {
            res.writeHead(404);
            res.end('Not found');
        }
    } else if (req.method === 'POST' && urlPath.includes('/upload_training_pdf/')) {
        let body = [];
        req.on('data', chunk => {
            body.push(chunk);
        });
        req.on('end', () => {
            const totalLength = body.reduce((acc, chunk) => acc + chunk.length, 0);
            console.log(`Upload received: ${totalLength} bytes`);
            
            const response = {
                message: 'Upload successful!',
                filename: 'training.pdf',
                size: totalLength,
                file_id: Math.random().toString(36),
                category: 'academic'
            };
            
            res.writeHead(200, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify(response));
        });
    } else {
        res.writeHead(404);
        res.end('Not found');
    }
});

const PORT = 8000;
server.listen(PORT, '0.0.0.0', () => {
    console.log(`🚀 Node.js server running on http://localhost:${PORT}`);
    console.log(`🎛️ Admin interface: http://localhost:${PORT}/admin`);
});

server.on('error', (err) => {
    console.error('Server error:', err);
});
