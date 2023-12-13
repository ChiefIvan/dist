from Server import Flaskserver

app: Flaskserver = Flaskserver()


def create_app():
    return app.server_run()


if __name__ == "__main__":
    server = create_app()
    server.run(debug=True)
    # server.serve_forever()
