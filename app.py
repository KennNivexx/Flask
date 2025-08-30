from flask import Flask
app = Flask (__nama__)

@app.route("/")
def hello():
    return "Hello from Flask on Railway!"
