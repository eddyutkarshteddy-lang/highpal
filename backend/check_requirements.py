"""
Haystack Requirements Checker
Check if all requirements are fulfilled for the online service
"""

import sys
import importlib

def check_requirements():
    """Check if all required packages are installed"""
    
    required_packages = {
        'fastapi': 'FastAPI web framework',
        'uvicorn': 'ASGI server',
        'pydantic': 'Data validation',
        'requests': 'HTTP requests',
        'bs4': 'BeautifulSoup for HTML parsing',
        'PyPDF2': 'PDF processing',
        'haystack': 'Haystack AI framework',
        'sentence_transformers': 'Embeddings',
        'python_multipart': 'File upload support'
    }
    
    print("🔍 Checking Haystack Online Service Requirements\n")
    print("=" * 50)
    
    missing_packages = []
    installed_packages = []
    
    for package, description in required_packages.items():
        try:
            if package == 'bs4':
                import bs4
            elif package == 'python_multipart':
                import multipart
            else:
                importlib.import_module(package)
            
            print(f"✅ {package:<20} - {description}")
            installed_packages.append(package)
        except ImportError:
            print(f"❌ {package:<20} - {description} (MISSING)")
            missing_packages.append(package)
    
    print("\n" + "=" * 50)
    print(f"📊 Summary:")
    print(f"   Installed: {len(installed_packages)}/{len(required_packages)}")
    print(f"   Missing: {len(missing_packages)}")
    
    if missing_packages:
        print(f"\n🚨 Missing packages: {', '.join(missing_packages)}")
        print(f"💡 Install with: pip install {' '.join(missing_packages)}")
        return False
    else:
        print(f"\n✅ All requirements fulfilled!")
        return True

def check_python_version():
    """Check Python version compatibility"""
    print(f"\n🐍 Python Version: {sys.version}")
    version_info = sys.version_info
    
    if version_info.major == 3 and version_info.minor >= 8:
        print("✅ Python version is compatible")
        return True
    else:
        print("❌ Python 3.8+ required")
        return False

def check_haystack_components():
    """Check Haystack specific components"""
    print(f"\n🔧 Checking Haystack Components:")
    
    try:
        from simple_haystack_manager import get_haystack_manager
        print("✅ Haystack manager module found")
        
        manager = get_haystack_manager()
        print("✅ Haystack manager initialized")
        
        stats = manager.get_statistics()
        print(f"✅ Document store operational ({stats.get('total_documents', 0)} documents)")
        
        return True
        
    except Exception as e:
        print(f"❌ Haystack components error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Haystack Online Service Requirements Check")
    print("=" * 60)
    
    # Check Python version
    python_ok = check_python_version()
    
    # Check required packages
    packages_ok = check_requirements()
    
    # Check Haystack components
    haystack_ok = check_haystack_components()
    
    print("\n" + "=" * 60)
    print("🎯 FINAL STATUS:")
    
    if python_ok and packages_ok and haystack_ok:
        print("✅ ALL REQUIREMENTS FULFILLED!")
        print("🚀 Ready to start Haystack online service!")
        print("\n💡 Start the server with: python haystack_server.py")
    else:
        print("❌ REQUIREMENTS NOT MET")
        print("🔧 Please fix the issues above before starting the service")
