from microservice import app

if __name__ == "__main__":
    from waitress import serve

    from lib.config import APP_PORT

    serve(app, host="0.0.0.0", port=APP_PORT or 5000)
