@echo off
cd /d "C:\Users\eddyu\Documents\Projects\highpal"
echo "Adding files to git..."
git add .
echo "Committing changes..."
git commit -m "feat: Enhanced PDF extraction with 40x improvement and persistent storage - Implemented 6-strategy PDF extraction using pdf-poppler achieving 1.66M characters vs 41K - Added automatic persistent storage via training_data.json preventing data loss - Enhanced extractPDFTextEnhanced() with multiple extraction strategies - Added comprehensive error handling and extraction logging - Integrated pdf-parse, pdf-poppler, and pdf2pic libraries for maximum extraction capability - Fixed duplicate path declarations and improved server stability"
echo "Pushing to GitHub..."
git push origin main
echo "Done!"
pause
