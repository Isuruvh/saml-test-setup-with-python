from flask import Flask, request
import base64

app = Flask(__name__)

@app.route("/")
def home():
    return """
    <h1>My SAML SP</h1>
    <p>Waiting for SAML Response...</p>
    """

@app.route("/acs", methods=["POST"])
def acs():

    saml_response = request.form.get("SAMLResponse")

    if not saml_response:
        return "No SAML Response"

    decoded = base64.b64decode(saml_response)

    return f"""
    <h1>SAML Assertion Received</h1>
    <pre>{decoded.decode('utf-8')}</pre>
    """

app.run(host="0.0.0.0", port=8000)