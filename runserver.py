from server import app

if __name__ == '__main__':
    HOST = '0.0.0.0'
    PORT = 8090

    app.run(HOST, PORT, threaded=True) 

