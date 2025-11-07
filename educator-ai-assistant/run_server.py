"""
Run the FastAPI application
"""

if __name__ == "__main__":
    import uvicorn
    import logging
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Run server
    uvicorn.run(
        "app.main:app", 
        host="localhost", 
        port=8003, 
        reload=False,
        log_level="info"
    )