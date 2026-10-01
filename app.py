from flask import Flask, request
import base64

app = Flask(__name__)

OKTA_APP_EMBED_LINK = "https://login.isurutrader.com/home/integrator-4503275_mysamlapp_1/0oa1895yciyVULFnC698/aln18965bmyzqxAbd698"

@app.route("/")
def home():

    return f"""
    <html>
    <body>

        <h1>Identity Portal</h1>

        <button onclick="window.location.href='https://login.isurutrader.com/home/integrator-4503275_mysamlapp_1/0oa1895yciyVULFnC698/aln18965bmyzqxAbd698'">
            Okta SAML Sign In
        </button>

        <br><br>

        <button onclick="window.location.href='https://entra.microsoft.com'">
            Entra Sign In
        </button>

    </body>
    </html>
    """

@app.route("/acs", methods=["POST"])
def acs():

    saml_response = request.form.get("SAMLResponse")

    if not saml_response:
        return "No SAML Response Found"

    decoded_xml = base64.b64decode(saml_response)

    return f"""
    <html>
    <body>

        <h1>SAML Assertion Received</h1>

        <pre>
{decoded_xml.decode('utf-8')}
        </pre>

    </body>
    </html>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
