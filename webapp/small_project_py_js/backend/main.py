from flask import Flask

app = Flask(
    __name__,
    static_url_path="/dist",
    static_folder="../frontend/dist",
    template_folder="../frontend/dist/html",
)


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def index(path: str):
    return app.send_static_file("html/index.html")


@app.route("/sample.html", defaults={"path": ""})
def sample(path: str):
    return app.send_static_file("html/sample.html")


@app.route("/hello", methods=["GET"])
def hello():
    return "hello"


if __name__ == "__main__":
    app.run()
