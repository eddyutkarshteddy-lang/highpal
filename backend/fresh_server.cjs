console.log('Starting server...');

const http = require('http');
const fs = require('fs');
const pdf = require('pdf-parse');

// Storage for uploaded documents
const uploadedDocuments = {};

const server = http.createServer((req, res) => {
    console.log(`${req.method} ${req.url}`);
    
    // CORS headers
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, DELETE');
    res.setHeader('Access-Control-Allow-Headers', '*');
    
    if (req.method === 'OPTIONS') {
        res.writeHead(200);
        res.end();
        return;
    }
    
    const urlPath = req.url.split('?')[0];
    
    if (req.method === 'GET' && urlPath === '/health') {
        const response = {
            status: "healthy", 
            message: "Node.js server running properly",
            time: new Date().toISOString()
        };
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify(response));
        console.log('Health check sent');
        
    } else if (req.method === 'GET' && urlPath === '/admin') {
        try {
            const adminHtml = fs.readFileSync('./admin.html', 'utf8');
            res.writeHead(200, { 'Content-Type': 'text/html' });
            res.end(adminHtml);
            console.log('Admin page served');
        } catch (error) {
            res.writeHead(404);
            res.end('Admin page not found');
        }
        
    } else if (req.method === 'GET' && urlPath === '/admin/training_data/') {
        const query = new URL(req.url, `http://${req.headers.host}`).searchParams;
        const adminKey = query.get('admin_key');
        
        if (adminKey !== 'admin123') {
            res.writeHead(403, { 'Content-Type': 'application/json' });
            res.end('{"error": "Invalid admin key"}');
            return;
        }
        
        // Get training documents
        const trainingDocs = [];
        const categories = {};
        
        for (const [docId, docData] of Object.entries(uploadedDocuments)) {
            if (docData.source === 'training_data') {
                const category = docData.category || 'unknown';
                categories[category] = (categories[category] || 0) + 1;
                
                trainingDocs.push({
                    doc_id: docId,
                    filename: docData.filename,
                    category: category,
                    content_length: docData.content ? docData.content.length : 0,
                    title: docData.title,
                    storage: 'memory',
                    size: docData.size
                });
            }
        }
        
        const response = {
            training_documents: trainingDocs,
            categories: categories,
            total_training_docs: trainingDocs.length
        };
        
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify(response, null, 2));
        console.log(`Training data sent: ${trainingDocs.length} documents`);
        
    } else if (req.method === 'POST' && urlPath.includes('/upload_training_pdf/')) {
        let body = [];
        req.on('data', chunk => {
            body.push(chunk);
        });
        req.on('end', async () => {
            try {
                const pdfBuffer = Buffer.concat(body);
                const totalLength = pdfBuffer.length;
                console.log(`Upload received: ${totalLength} bytes`);
                
                // Extract text from PDF
                let extractedText = '';
                try {
                    const pdfData = await pdf(pdfBuffer);
                    extractedText = pdfData.text || '';
                    console.log(`Extracted ${extractedText.length} characters from PDF`);
                } catch (pdfError) {
                    console.log('PDF parsing failed, using fallback:', pdfError.message);
                    extractedText = `PDF content (${totalLength} bytes) - Text extraction failed: ${pdfError.message}`;
                }
                
                const fileId = Math.random().toString(36).substr(2, 9);
                const filename = 'training.pdf';
                
                uploadedDocuments[fileId] = {
                    filename: filename,
                    size: totalLength,
                    content: extractedText,
                    category: 'academic',
                    source: 'training_data',
                    title: 'Uploaded Training Document',
                    upload_date: new Date().toISOString()
                };
                
                console.log(`Stored document ID: ${fileId}`);
                
                const response = {
                    message: 'Upload successful!',
                    filename: filename,
                    size: totalLength,
                    file_id: fileId,
                    category: 'academic',
                    extracted_text_length: extractedText.length
                };
                
                res.writeHead(200, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify(response));
            } catch (error) {
                console.error('Upload processing error:', error);
                res.writeHead(500, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({ error: 'Upload processing failed: ' + error.message }));
            }
        });
        
    } else {
        res.writeHead(404);
        res.end('Not found');
    }
});

const PORT = 8001;
server.listen(PORT, '0.0.0.0', (err) => {
    if (err) {
        console.error('Server failed to start:', err);
        return;
    }
    console.log('='.repeat(50));
    console.log(`🚀 Node.js server running on http://localhost:${PORT}`);
    console.log(`🎛️ Admin interface: http://localhost:${PORT}/admin`);
    console.log(`📊 Health check: http://localhost:${PORT}/health`);
    console.log('='.repeat(50));
});

server.on('error', (err) => {
    console.error('Server error:', err);
});
