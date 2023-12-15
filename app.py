from Server import Flaskserver

server: Flaskserver = Flaskserver()
app = server.server_run()

# def create_app():
#     return app.server_run()


# if __name__ == "__main__":
#     server = create_app()
#     server.run(debug=True)
#     # server.serve_forever()
