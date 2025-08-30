import uvicorn


def main():
    """Main entry point - starts the FastAPI server."""
    print("🚀 Starting Joyce server...")
    uvicorn.run(
        "joyce.server:app",
        host="127.0.0.1",  # Bind to localhost only for security
        port=3000,
        reload=True,
        log_level="info",
    )


if __name__ == "__main__":
    main()
