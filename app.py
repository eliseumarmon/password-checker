"""Start the application on loopback only: python app.py."""
import uvicorn

if __name__ == '__main__':
    uvicorn.run('backend.password_checker.api:app', host='127.0.0.1', port=8000, access_log=False)
