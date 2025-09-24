from fastapi import FastAPI

app = FastAPI(
    title="AI Web Scraper API - Simple",
    description="Simplified version for Lambda deployment",
    version="1.0.0",
)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "1.0.0"}
