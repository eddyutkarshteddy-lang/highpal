const http = require('http');

console.log('Starting simple test server...');

const server = http.createServer((req, res) => {
    console.log(`Request: ${req.method} ${req.url}`);
    res.writeHead(200, { 'Content-Type': 'text/plain' });
    res.end('Hello World');
});

server.listen(8001, () => {
    console.log('Test server running on port 8001');
});

console.log('Server setup complete');
