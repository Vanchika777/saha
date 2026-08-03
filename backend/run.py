import os
from app import create_app
from app.config import Config

app = create_app()

if __name__ == "__main__":
    # Prioritize the live PORT variable injected by hosting environments (like Render)
    port = int(os.environ.get("PORT", getattr(Config, "PORT", 5000)))
    print(f"Starting Saha Backend on port {port}...")
    
    # Set debug=False for production deployment
    app.run(host="0.0.0.0", port=port, debug=False)