"""
Flask application factory for the AIRI chatbot API.
"""
import os
import socket
from typing import Dict
from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS

from .routes.chat import chat_bp, init_chat_routes
from .routes.health import health_bp, init_health_routes
from .routes.snippets import snippets_bp, init_snippet_routes
from .routes.get_file_content import file_content_bp
from .routes.language import language_bp, init_language_routes
from .routes.features import features_bp, init_features_routes
from .routes.metrics import metrics_bp
from .routes.session import session_bp
from .routes.document_preview import document_preview_bp, init_preview_routes
from .routes.excel_viewer import excel_viewer_bp, init_excel_routes
from .routes.word_viewer import word_viewer_bp, init_word_routes
from .routes.gallery import gallery_bp
from ..core.services.chat_service import ChatService
from ..core.models.gemini import GeminiModel
from ..core.storage.vector_store import VectorStore
from ..config.logging import setup_logging, get_logger
from ..config.settings import settings

def create_app(config=None):
    """
    Application factory for creating Flask app instances.
    
    Args:
        config: Optional configuration overrides
        
    Returns:
        Flask application instance
    """
    # Set up logging
    setup_logging()
    logger = get_logger(__name__)
    
    # Create Flask app
    app = Flask(__name__)
    
    # Enable CORS with production settings + Webflow integration
    CORS(app, 
         origins=[
             "*",  # Allow all origins for testing
             "https://futuretech.mit.edu",  # Production Webflow site
             "https://futuretech.webflow.io",  # Webflow staging
             "https://*.webflow.io",  # Webflow preview domains
             "https://davidturturean.github.io",  # GitHub Pages hosting
             "https://*.github.io"  # Any GitHub Pages domain
         ],
         methods=["GET", "POST", "OPTIONS"],
         allow_headers=["Content-Type", "Authorization"],
         supports_credentials=True)
    
    # Apply configuration
    if config:
        app.config.update(config)
    
    # Initialize services
    chat_service = _initialize_services(logger)
    
    # Initialize route blueprints with dependencies
    init_chat_routes(chat_service)
    init_health_routes(chat_service)
    init_snippet_routes(chat_service)
    init_language_routes(chat_service)
    init_preview_routes(chat_service)
    init_excel_routes(chat_service)
    init_word_routes(chat_service)
    init_features_routes()  # Features don't need chat_service

    # Register blueprints
    app.register_blueprint(chat_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(snippets_bp)
    app.register_blueprint(file_content_bp)
    app.register_blueprint(language_bp)
    app.register_blueprint(features_bp)
    app.register_blueprint(metrics_bp)
    app.register_blueprint(session_bp)
    app.register_blueprint(document_preview_bp)
    app.register_blueprint(excel_viewer_bp)
    app.register_blueprint(word_viewer_bp)
    app.register_blueprint(gallery_bp)
    
    # Add frontend routes
    _add_frontend_routes(app, logger)
    
    # Add error handlers
    _add_error_handlers(app, logger)
    
    logger.info("Flask application created successfully")
    return app

def _initialize_services(logger):
    """Initialize all services and components."""
    try:
        # Defer metadata service initialization for faster startup (lazy loading)
        logger.info("Metadata service will initialize on first query (lazy loading)")
        try:
            from ..core.metadata import metadata_service
            # Do NOT call initialize() - let ensure_initialized() handle it on first query
            logger.info("Metadata service ready for lazy initialization")
        except Exception as e:
            logger.warning(f"Metadata service import failed: {str(e)}")
        
        # Initialize vector store
        logger.info("Initializing vector store...")
        vector_store = VectorStore(
            embedding_provider=settings.EMBEDDING_PROVIDER,
            api_key=settings.GEMINI_API_KEY,
            repository_path=settings.get_repository_path(),
            persist_directory=str(settings.CHROMA_DB_DIR),
            use_hybrid_search=settings.USE_HYBRID_SEARCH
        )
        
        # Initialize vector store - unified approach
        logger.info("Starting vector store initialization...")
        try:
            success = vector_store.initialize()
            if not success:
                logger.error("Vector store initialization failed completely")
                vector_store = None
            else:
                logger.info("Vector store initialization successful")
        except Exception as e:
            logger.error(f"Vector store initialization threw exception: {str(e)}")
            vector_store = None
        
        # Initialize query monitor (optional)
        query_monitor = None
        try:
            from ..core.query.monitor import Monitor as QueryMonitor
            query_monitor = QueryMonitor(api_key=settings.GEMINI_API_KEY)
            logger.info("Query monitor initialized")
        except ImportError:
            logger.warning("Query monitor not available")
        except Exception as e:
            logger.warning(f"Query monitor initialization failed: {str(e)}")
        
        # Initialize Gemini model
        logger.info("Initializing Gemini model...")
        gemini_model = GeminiModel(
            api_key=settings.GEMINI_API_KEY,
            model_name=settings.GEMINI_MODEL_NAME
        )
        
        # Initialize chat service
        logger.info("Initializing chat service...")
        chat_service = ChatService(
            gemini_model=gemini_model,
            vector_store=vector_store,
            query_monitor=query_monitor
        )
        
        # Validate system readiness
        readiness_status = _validate_system_readiness(chat_service)
        logger.info(f"System readiness: {readiness_status}")
        
        # Validate and log current configuration
        _log_system_configuration(logger, chat_service)
        
        logger.info("All services initialized successfully")
        return chat_service
        
    except Exception as e:
        logger.error(f"Error initializing services: {str(e)}")
        # Return a minimal chat service even if initialization fails
        return ChatService()

def _validate_system_readiness(chat_service) -> Dict[str, str]:
    """
    Validate system component readiness with deep checks and log status.
    This function now performs actual service calls to confirm components are operational.
    """
    status = {
        "vector_store": "✗ Unavailable",
        "gemini_model": "✗ Unavailable",
        "query_monitor": "✗ Unavailable",
        "overall": "Degraded"
    }

    # Deep check for vector store
    if hasattr(chat_service, 'vector_store') and chat_service.vector_store:
        try:
            # A simple query to test responsiveness and data presence
            test_docs = chat_service.vector_store.get_relevant_documents("test", k=1)
            if test_docs:
                status["vector_store"] = f"✓ Ready ({len(test_docs)} test docs found)"
            else:
                status["vector_store"] = "✓ Ready (No test docs, but responsive)"
        except Exception as e:
            status["vector_store"] = f"✗ Error: {str(e)[:100]}"

    # Deep check for Gemini model
    if hasattr(chat_service, 'gemini_model') and chat_service.gemini_model:
        try:
            # Test content generation to confirm API and model access
            test_response = chat_service.gemini_model.generate("Test")
            status["gemini_model"] = "✓ Ready" if test_response else "✗ No response from model"
        except Exception as e:
            status["gemini_model"] = f"✗ Error: {str(e)[:100]}"

    # Deep check for query monitor
    if (hasattr(chat_service, 'query_processor') and
            hasattr(chat_service.query_processor, 'query_monitor') and
            chat_service.query_processor.query_monitor):
        try:
            # Test inquiry type determination
            test_analysis = chat_service.query_processor.query_monitor.determine_inquiry_type("test")
            status["query_monitor"] = "✓ Ready" if test_analysis else "✗ No response from monitor"
        except Exception as e:
            status["query_monitor"] = f"✗ Error: {str(e)[:100]}"

    # Determine overall status based on deep checks
    ready_count = sum(1 for s in status.values() if s.startswith("✓"))
    total_components = 3

    if ready_count == total_components:
        status["overall"] = "Fully Operational"
    elif ready_count > 0:
        status["overall"] = f"Partially Operational ({ready_count}/{total_components})"
    else:
        status["overall"] = "Degraded - All components failed checks"

    return status

def _log_system_configuration(logger, chat_service):
    """Log current system configuration to guarantee we're using the latest version."""
    logger.info("🔧 SYSTEM CONFIGURATION VERIFICATION")
    logger.info(f"📊 USE_HYBRID_SEARCH: {settings.USE_HYBRID_SEARCH}")
    logger.info(f"📊 USE_FIELD_AWARE_HYBRID: {settings.USE_FIELD_AWARE_HYBRID}")
    
    # Check actual retriever type in use
    if chat_service.vector_store and hasattr(chat_service.vector_store, 'hybrid_retriever'):
        if chat_service.vector_store.hybrid_retriever:
            retriever_class = chat_service.vector_store.hybrid_retriever.__class__.__name__
            logger.info(f"🎯 ACTIVE RETRIEVER: {retriever_class}")
            
            # Validate it's the correct type
            if retriever_class == "FieldAwareHybridRetriever":
                logger.info("✅ CONFIRMED: Using Field-Aware Hybrid Retrieval")
            else:
                logger.warning(f"⚠️  UNEXPECTED RETRIEVER TYPE: {retriever_class}")
        else:
            logger.warning("⚠️  NO HYBRID RETRIEVER ACTIVE")
    
    # Check model configuration
    if chat_service.gemini_model:
        model_chain = getattr(chat_service.gemini_model, 'model_chain', ['unknown'])
        logger.info(f"🤖 MODEL CHAIN: {model_chain}")
        logger.info(f"🔄 MULTI-MODEL FALLBACK: {hasattr(chat_service.gemini_model, 'model_chain')}")
    
    logger.info("🔧 CONFIGURATION VERIFICATION COMPLETE")

def _add_frontend_routes(app, logger):
    """Add routes for serving the frontend."""
    
    # Dashboard route
    @app.route('/dashboard')
    @app.route('/dashboard/')
    @app.route('/dashboard/<path:filename>')
    def serve_dashboard(filename=None):
        """Serve the metrics dashboard."""
        from pathlib import Path
        dashboard_dir = Path(__file__).parent.parent.parent / 'dashboard'
        
        if filename:
            # Serve specific file (dashboard.js, etc)
            if (dashboard_dir / filename).exists():
                return send_from_directory(str(dashboard_dir), filename)
            else:
                return f"Dashboard file not found: {filename}", 404
        else:
            # Serve index.html
            if (dashboard_dir / 'index.html').exists():
                return send_from_directory(str(dashboard_dir), 'index.html')
            else:
                return "Dashboard not found", 404
    
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_frontend(path):
        """Serve the React app (GitHub frontend)."""
        logger.debug(f"Serving path: {path}")
        
        # Special route for source snippets
        if path.startswith('snippet/'):
            snippet_id = path.split('/')[-1]
            return _get_snippet_page(snippet_id)
        
        try:
            # Look for built files in frontend/dist directory
            frontend_dist_path = settings.FRONTEND_DIR / 'dist'
            frontend_path = settings.FRONTEND_DIR
            
            # Try built files first (production mode)
            if frontend_dist_path.exists():
                if path and (frontend_dist_path / path).exists():
                    logger.debug(f"Serving built file: {path}")
                    return send_from_directory(str(frontend_dist_path), path)
                elif path and '.' in path:  # File with extension that doesn't exist
                    logger.warning(f"Built file not found: {path}")
                    return f"File not found: {path}", 404
                else:
                    # Try to serve index.html for all other routes (SPA routing)
                    logger.debug(f"Serving built index.html for path: {path}")
                    index_path = frontend_dist_path / 'index.html'
                    if index_path.exists():
                        return send_from_directory(str(frontend_dist_path), 'index.html')
            
            # Fallback to development files
            if path and (frontend_path / path).exists():
                logger.debug(f"Serving dev file: {path}")
                return send_from_directory(str(frontend_path), path)
            elif path and '.' in path:  # File with extension that doesn't exist
                logger.warning(f"File not found: {path}")
                return f"File not found: {path}", 404
            else:
                # Try to serve index.html for all other routes (SPA routing)
                logger.debug(f"Serving dev index.html for path: {path}")
                index_path = frontend_path / 'index.html'
                if index_path.exists():
                    return send_from_directory(str(frontend_path), 'index.html')
                else:
                    return "Frontend not found. Please build the frontend first.", 404
        except Exception as e:
            logger.error(f"Error serving file: {str(e)}")
            return f"Error: {str(e)}", 500

def _get_snippet_page(snippet_id):
    """Generate an HTML page for viewing a document snippet."""
    # This could be enhanced to use the citation service
    snippet_path = settings.DOC_SNIPPETS_DIR / f"doc_{snippet_id}.txt"
    
    if snippet_path.exists():
        try:
            return send_file(snippet_path, as_attachment=True)
        except Exception as e:
            return f"Error reading snippet: {str(e)}", 500
    else:
        return "Snippet not found", 404

def _add_error_handlers(app, logger):
    """Add error handlers to the app."""
    
    @app.errorhandler(404)
    def not_found(error):
        logger.warning(f"404 error: {error}")
        return jsonify({"error": "Not found"}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"500 error: {error}")
        return jsonify({"error": "Internal server error"}), 500

def get_available_port(preferred_port=None):
    """Find an available port to run the server on."""
    preferred_port = preferred_port or settings.get_port()
    
    def is_port_available(port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        available = False
        try:
            sock.bind(('0.0.0.0', port))
            available = True
        except:
            pass
        finally:
            sock.close()
        return available
    
    # Try preferred port first
    if is_port_available(preferred_port):
        return preferred_port
    
    # Try alternative ports
    for alt_port in settings.ALLOWED_PORTS:
        if is_port_available(alt_port):
            return alt_port
    
    # Return preferred port anyway and let it fail if needed
    return preferred_port