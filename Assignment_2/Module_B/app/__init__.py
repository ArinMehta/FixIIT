"""Application package for Module B."""
from flask import Flask
import os
from app.database import initialize_module_b_tables, DatabaseError


def create_app():
    """
    Factory function to create and configure the Flask application.
    Initializes the app with database, blueprints, and error handlers.
    """
    # Get the base directory (Module_B)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Create Flask app with templates and static folders
    app = Flask(
        __name__,
        template_folder=os.path.join(base_dir, 'templates'),
        static_folder=os.path.join(base_dir, 'static'),
        static_url_path='/static'
    )

    # Ensure coordinator and shard-local Module B tables exist for local/dev usage.
    try:
        initialize_module_b_tables()
    except DatabaseError as exc:
        # Do not crash app startup; endpoints will still show explicit DB errors.
        print(f"[WARN] Module B coordinator/shard initialization failed: {exc}")
    
    # Import and register API blueprint
    from app.api import api
    app.register_blueprint(api)
    
    return app
