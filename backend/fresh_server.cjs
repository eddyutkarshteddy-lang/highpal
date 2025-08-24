console.log('Starting server...');

const http = require('http');
const fs = require('fs');
const path = require('path');
const pdf = require('pdf-parse');
const pdfPoppler = require('pdf-poppler');

// Try to load additional PDF libraries
let pdfjsLib = null;
try {
    pdfjsLib = require('pdfjs-dist/legacy/build/pdf.js');
} catch (e) {
    console.log('pdfjs-dist not available, using basic extraction only');
}

// Enhanced PDF extraction function
async function extractTextFromPDF(pdfBuffer) {
    const results = {
        method1_pdf_parse: null,
        method2_detailed: null,
        bestText: '',
        extractionInfo: {}
    };

    // Method 1: Standard pdf-parse
    try {
        const pdfData = await pdf(pdfBuffer, {
            max: 0, // Extract all pages
            version: 'v1.10.100'
        });
        
        results.method1_pdf_parse = {
            text: pdfData.text || '',
            length: (pdfData.text || '').length,
            pages: pdfData.numpages || 0,
            info: pdfData.info || {}
        };
        
        console.log(`Method 1 (pdf-parse): ${results.method1_pdf_parse.length} characters`);
    } catch (error) {
        console.log('Method 1 failed:', error.message);
        results.method1_pdf_parse = { error: error.message };
    }

    // Method 2: Enhanced extraction with custom options
    try {
        const customOptions = {
            max: 0,
            normalizeWhitespace: false,
            disableCombineTextItems: false
        };
        
        const pdfData2 = await pdf(pdfBuffer, customOptions);
        results.method2_detailed = {
            text: pdfData2.text || '',
            length: (pdfData2.text || '').length,
            pages: pdfData2.numpages || 0
        };
        
        console.log(`Method 2 (enhanced): ${results.method2_detailed.length} characters`);
    } catch (error) {
        console.log('Method 2 failed:', error.message);
        results.method2_detailed = { error: error.message };
    }

    // Choose the best result
    let bestResult = results.method1_pdf_parse;
    if (results.method2_detailed && results.method2_detailed.text && 
        results.method2_detailed.length > (bestResult?.length || 0)) {
        bestResult = results.method2_detailed;
        console.log('Using Method 2 (enhanced) as it extracted more text');
    } else {
        console.log('Using Method 1 (pdf-parse) as the best result');
    }

    results.bestText = bestResult?.text || '';
    results.extractionInfo = {
        finalLength: results.bestText.length,
        pages: bestResult?.pages || 0,
        info: bestResult?.info || {},
        methodsAttempted: 2,
        method1Length: results.method1_pdf_parse?.length || 0,
        method2Length: results.method2_detailed?.length || 0
    };

    return results;
}

// Storage for uploaded documents
const uploadedDocuments = {};
const DATA_FILE = path.join(__dirname, 'training_data.json');

// Load existing training data on startup
function loadTrainingData() {
    try {
        if (fs.existsSync(DATA_FILE)) {
            const data = fs.readFileSync(DATA_FILE, 'utf8');
            const loadedData = JSON.parse(data);
            Object.assign(uploadedDocuments, loadedData);
            console.log(`📂 Loaded ${Object.keys(loadedData).length} training documents from storage`);
        } else {
            console.log('📂 No existing training data file found, starting fresh');
        }
    } catch (error) {
        console.error('❌ Error loading training data:', error.message);
    }
}

// Save training data to file
function saveTrainingData() {
    try {
        const dataToSave = {};
        // Only save training data (not regular uploads)
        for (const [id, doc] of Object.entries(uploadedDocuments)) {
            if (doc.source === 'training_data') {
                dataToSave[id] = doc;
            }
        }
        
        fs.writeFileSync(DATA_FILE, JSON.stringify(dataToSave, null, 2));
        console.log(`💾 Saved ${Object.keys(dataToSave).length} training documents to storage`);
        return true;
    } catch (error) {
        console.error('❌ Error saving training data:', error.message);
        return false;
    }
}

// Load training data when server starts
loadTrainingData();

// Enhanced PDF extraction function with multiple strategies
async function extractPDFTextEnhanced(pdfBuffer) {
    let bestText = '';
    let extractionInfo = { methods: [], totalLength: 0 };
    const results = [];
    
    // Strategy 1: Standard pdf-parse
    try {
        console.log('🔍 Trying standard PDF extraction...');
        const pdfData = await pdf(pdfBuffer, {
            max: 0, // Extract all pages
            version: 'v1.10.100'
        });
        
        const standardText = pdfData.text || '';
        results.push({
            method: 'standard',
            text: standardText,
            length: standardText.length,
            pages: pdfData.numpages
        });
        
        extractionInfo.methods.push('standard');
        extractionInfo.pages = pdfData.numpages;
        extractionInfo.standardLength = standardText.length;
        
        console.log(`📄 Standard extraction: ${standardText.length} characters from ${pdfData.numpages} pages`);
        
    } catch (error) {
        console.log('❌ Standard extraction failed:', error.message);
        extractionInfo.standardError = error.message;
    }
    
    // Strategy 2: pdf-poppler (most powerful)
    try {
        console.log('🔍 Trying pdf-poppler extraction...');
        
        // Write buffer to temporary file for pdf-poppler
        const tempFilePath = `./temp_${Date.now()}.pdf`;
        fs.writeFileSync(tempFilePath, pdfBuffer);
        
        const options = {
            format: 'text',
            out_dir: './temp_extraction',
            out_prefix: 'page',
            page: null // Extract all pages
        };
        
        const popplerResult = await pdfPoppler.convertToText(tempFilePath, options);
        
        // Read all extracted text files
        let popplerText = '';
        const extractionDir = './temp_extraction';
        if (fs.existsSync(extractionDir)) {
            const files = fs.readdirSync(extractionDir);
            const textFiles = files.filter(file => file.endsWith('.txt')).sort();
            
            for (const file of textFiles) {
                const content = fs.readFileSync(`${extractionDir}/${file}`, 'utf8');
                popplerText += content + '\n\n';
            }
            
            // Clean up
            for (const file of files) {
                fs.unlinkSync(`${extractionDir}/${file}`);
            }
            fs.rmdirSync(extractionDir);
        }
        
        // Clean up temp PDF
        fs.unlinkSync(tempFilePath);
        
        results.push({
            method: 'poppler',
            text: popplerText,
            length: popplerText.length
        });
        
        extractionInfo.methods.push('poppler');
        extractionInfo.popplerLength = popplerText.length;
        console.log(`🚀 Poppler extraction: ${popplerText.length} characters`);
        
    } catch (error) {
        console.log('❌ Poppler extraction failed:', error.message);
        extractionInfo.popplerError = error.message;
    }
    
    // Strategy 3: Enhanced options extraction
    try {
        console.log('🔍 Trying enhanced options extraction...');
        const pdfData = await pdf(pdfBuffer, {
            normalizeWhitespace: false,
            disableCombineTextItems: false,
            max: 0
        });
        
        const enhancedText = pdfData.text || '';
        results.push({
            method: 'enhanced',
            text: enhancedText,
            length: enhancedText.length
        });
        
        extractionInfo.methods.push('enhanced');
        extractionInfo.enhancedLength = enhancedText.length;
        console.log(`� Enhanced extraction: ${enhancedText.length} characters`);
        
    } catch (error) {
        console.log('❌ Enhanced extraction failed:', error.message);
        extractionInfo.enhancedError = error.message;
    }
    
    // Strategy 4: Raw text extraction with minimal processing
    try {
        console.log('🔍 Trying raw text extraction...');
        const pdfData = await pdf(pdfBuffer, {
            normalizeWhitespace: true,
            disableCombineTextItems: true,
            max: 0
        });
        
        const rawText = pdfData.text || '';
        results.push({
            method: 'raw',
            text: rawText,
            length: rawText.length
        });
        
        extractionInfo.methods.push('raw');
        extractionInfo.rawLength = rawText.length;
        console.log(`� Raw extraction: ${rawText.length} characters`);
        
    } catch (error) {
        console.log('❌ Raw extraction failed:', error.message);
        extractionInfo.rawError = error.message;
    }
    
    // Strategy 4: Page-by-page extraction with different options
    try {
        console.log('🔍 Trying page-by-page extraction...');
        let pageByPageText = '';
        const pdfData = await pdf(pdfBuffer);
        
        if (pdfData.numpages) {
            for (let i = 1; i <= pdfData.numpages; i++) {
                try {
                    const pageData = await pdf(pdfBuffer, {
                        first: i,
                        last: i,
                        normalizeWhitespace: false
                    });
                    pageByPageText += pageData.text + '\n';
                } catch (pageError) {
                    console.log(`⚠️ Page ${i} extraction failed:`, pageError.message);
                }
            }
        }
        
        if (pageByPageText) {
            results.push({
                method: 'page-by-page',
                text: pageByPageText,
                length: pageByPageText.length
            });
            
            extractionInfo.methods.push('page-by-page');
            extractionInfo.pageByPageLength = pageByPageText.length;
            console.log(`📖 Page-by-page extraction: ${pageByPageText.length} characters`);
        }
        
    } catch (error) {
        console.log('❌ Page-by-page extraction failed:', error.message);
        extractionInfo.pageByPageError = error.message;
    }
    
    // Strategy 5: Combined text from all successful methods
    try {
        console.log('🔍 Trying combined text strategy...');
        const validTexts = results.filter(r => r.text && r.text.length > 0);
        
        if (validTexts.length > 1) {
            // Combine unique content from all methods
            const combinedText = validTexts.map(r => r.text).join('\n\n--- METHOD SEPARATOR ---\n\n');
            
            results.push({
                method: 'combined',
                text: combinedText,
                length: combinedText.length
            });
            
            extractionInfo.methods.push('combined');
            extractionInfo.combinedLength = combinedText.length;
            console.log(`🔗 Combined extraction: ${combinedText.length} characters`);
        }
    } catch (error) {
        console.log('❌ Combined extraction failed:', error.message);
        extractionInfo.combinedError = error.message;
    }
    
    // Choose the best result (longest text)
    const bestResult = results.reduce((best, current) => {
        return current.length > best.length ? current : best;
    }, { text: '', length: 0, method: 'none' });
    
    bestText = bestResult.text;
    
    // Final processing
    extractionInfo.totalLength = bestText.length;
    extractionInfo.finalMethods = extractionInfo.methods.join(', ');
    extractionInfo.bestMethod = bestResult.method;
    
    console.log(`✅ FINAL RESULT: ${bestText.length} characters using best method: ${bestResult.method}`);
    console.log(`📊 All methods comparison: ${results.map(r => `${r.method}=${r.length}`).join(', ')}`);
    
    return {
        text: bestText,
        info: extractionInfo
    };
}

// Enhanced PDF text extraction function
async function extractTextFromPDF(pdfBuffer) {
    const results = {
        bestText: '',
        extractionInfo: {
            method1Length: 0,
            method2Length: 0,
            pages: 0,
            finalLength: 0,
            methods: []
        }
    };
    
    let method1Text = '';
    let method2Text = '';
    
    // Method 1: pdf-parse with enhanced options
    try {
        console.log('Trying Method 1: pdf-parse with enhanced options');
        const pdfData = await pdf(pdfBuffer, {
            max: 0, // Extract all pages
            version: 'v1.10.100',
            pagerender: (pageData) => {
                // Custom page rendering for better text extraction
                let render_options = {
                    normalizeWhitespace: false,
                    disableCombineTextItems: false
                };
                return pageData.getTextContent(render_options)
                    .then(textContent => {
                        let lastY, text = '';
                        for (let item of textContent.items) {
                            if (lastY == item.transform[5] || !lastY) {
                                text += item.str;
                            } else {
                                text += '\n' + item.str;
                            }
                            lastY = item.transform[5];
                        }
                        return text;
                    });
            }
        });
        
        method1Text = pdfData.text || '';
        results.extractionInfo.method1Length = method1Text.length;
        results.extractionInfo.pages = pdfData.numpages || 0;
        results.extractionInfo.methods.push('pdf-parse-enhanced');
        
        console.log(`Method 1 extracted: ${method1Text.length} characters from ${pdfData.numpages} pages`);
        
    } catch (error) {
        console.log('Method 1 failed:', error.message);
        results.extractionInfo.methods.push('pdf-parse-enhanced-failed');
    }
    
    // Method 2: Alternative extraction with different options
    try {
        console.log('Trying Method 2: pdf-parse with alternative settings');
        const pdfData2 = await pdf(pdfBuffer, {
            max: 0,
            normalizeWhitespace: true,
            disableCombineTextItems: true
        });
        
        method2Text = pdfData2.text || '';
        results.extractionInfo.method2Length = method2Text.length;
        results.extractionInfo.methods.push('pdf-parse-alternative');
        
        console.log(`Method 2 extracted: ${method2Text.length} characters`);
        
    } catch (error) {
        console.log('Method 2 failed:', error.message);
        results.extractionInfo.methods.push('pdf-parse-alternative-failed');
    }
    
    // Method 3: PDF.js extraction (if available)
    if (pdfjsLib) {
        try {
            console.log('Trying Method 3: PDF.js direct extraction');
            const loadingTask = pdfjsLib.getDocument({data: pdfBuffer});
            const pdfDoc = await loadingTask.promise;
            
            let pdfJsText = '';
            const numPages = pdfDoc.numPages;
            
            for (let i = 1; i <= numPages; i++) {
                const page = await pdfDoc.getPage(i);
                const textContent = await page.getTextContent();
                
                let pageText = '';
                let lastY = null;
                
                for (const item of textContent.items) {
                    if (lastY !== null && Math.abs(item.transform[5] - lastY) > 5) {
                        pageText += '\n';
                    }
                    pageText += item.str + ' ';
                    lastY = item.transform[5];
                }
                
                pdfJsText += pageText + '\n\n';
            }
            
            if (pdfJsText.length > Math.max(method1Text.length, method2Text.length)) {
                method2Text = pdfJsText;
                results.extractionInfo.method2Length = pdfJsText.length;
                results.extractionInfo.methods.push('pdfjs-direct');
                console.log(`Method 3 (PDF.js) extracted: ${pdfJsText.length} characters`);
            }
            
        } catch (error) {
            console.log('Method 3 (PDF.js) failed:', error.message);
            results.extractionInfo.methods.push('pdfjs-direct-failed');
        }
    }
    
    // Choose the best result (longest text)
    if (method1Text.length > method2Text.length) {
        results.bestText = method1Text;
        results.extractionInfo.finalLength = method1Text.length;
        results.extractionInfo.bestMethod = 'method1';
    } else {
        results.bestText = method2Text;
        results.extractionInfo.finalLength = method2Text.length;
        results.extractionInfo.bestMethod = 'method2';
    }
    
    // If still getting poor results, try cleaning and combining
    if (results.bestText.length < 1000 && (method1Text.length > 0 || method2Text.length > 0)) {
        const combinedText = method1Text + '\n\n' + method2Text;
        const cleanedText = combinedText
            .replace(/\s+/g, ' ')
            .replace(/\n\s*\n/g, '\n')
            .trim();
            
        if (cleanedText.length > results.bestText.length) {
            results.bestText = cleanedText;
            results.extractionInfo.finalLength = cleanedText.length;
            results.extractionInfo.bestMethod = 'combined-cleaned';
        }
    }
    
    return results;
}

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
            const adminHtml = fs.readFileSync(path.join(__dirname, 'admin.html'), 'utf8');
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
                
                // Extract text from PDF with multiple methods
                let extractedText = '';
                let extractionInfo = {};
                try {
                    console.log(`🚀 Starting enhanced PDF extraction for ${totalLength} bytes...`);
                    const extractionResults = await extractPDFTextEnhanced(pdfBuffer);
                    
                    extractedText = extractionResults.text;
                    extractionInfo = extractionResults.info;
                    
                    console.log(`📊 Enhanced PDF Extraction Complete:`);
                    console.log(`- Final extracted text: ${extractedText.length} characters`);
                    console.log(`- Methods used: ${extractionInfo.finalMethods}`);
                    console.log(`- PDF file size: ${totalLength} bytes`);
                    
                } catch (pdfError) {
                    console.log('❌ Enhanced PDF extraction failed:', pdfError.message);
                    extractedText = `PDF content (${totalLength} bytes) - Enhanced extraction failed: ${pdfError.message}`;
                    extractionInfo = { error: pdfError.message, fallback: true };
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
                    upload_date: new Date().toISOString(),
                    extraction_info: extractionInfo
                };
                
                console.log(`Stored document ID: ${fileId}`);
                
                // Save training data to persistent storage
                try {
                    saveTrainingData();
                    console.log('✅ Training data saved to persistent storage');
                } catch (saveError) {
                    console.error('❌ Failed to save training data:', saveError);
                }
                
                const response = {
                    message: 'Upload successful!',
                    filename: filename,
                    size: totalLength,
                    file_id: fileId,
                    category: 'academic',
                    extracted_text_length: extractedText.length,
                    extraction_info: extractionInfo
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
