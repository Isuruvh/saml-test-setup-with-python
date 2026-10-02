import base64
import html
import os
import secrets

from flask import Flask, redirect, request, session, url_for
from onelogin.saml2.auth import OneLogin_Saml2_Auth
from onelogin.saml2.errors import OneLogin_Saml2_Error
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or secrets.token_urlsafe(32)

# Native Flask configurations only
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="None",
    SESSION_COOKIE_SECURE=True,
)
@app.after_request
def add_partitioned_cookie_attribute(response):
    # Intercept Set-Cookie headers and append Partitioned safely
    for header in response.headers.getlist("Set-Cookie"):
        if "session=" in header and "Partitioned" not in header:
            response.headers.remove("Set-Cookie", header)
            response.headers.add("Set-Cookie", f"{header}; Partitioned")
    return response



# --- CONFIGURATION ---
OKTA_APP_EMBED_LINK = "https://login.isurutrader.com/home/integrator-4503275_mysamlapp_1/0oa1895yciyVULFnC698/aln18965bmyzqxAbd698"

ENTRA_TENANT_ID = os.environ.get("ENTRA_TENANT_ID", "df66a7fd-b2b8-4281-b943-6dbad5679154")
ENTRA_SAML_SSO_URL = os.environ.get(
    "ENTRA_SAML_SSO_URL",
    f"https://login.microsoftonline.com/{ENTRA_TENANT_ID}/saml2",
)
ENTRA_IDP_ENTITY_ID = os.environ.get(
    "ENTRA_IDP_ENTITY_ID",
    f"https://sts.windows.net/{ENTRA_TENANT_ID}/",
)
ENTRA_IDP_CERT = os.environ.get("ENTRA_IDP_CERT", "")
SAML_SP_ENTITY_ID = os.environ.get("SAML_SP_ENTITY_ID", "")
SAML_ACS_URL = os.environ.get("SAML_ACS_URL", "")


def entra_saml_settings():
    missing = [
        name
        for name, value in (
            ("SAML_SP_ENTITY_ID", SAML_SP_ENTITY_ID),
            ("SAML_ACS_URL", SAML_ACS_URL),
            ("ENTRA_IDP_CERT", ENTRA_IDP_CERT),
        )
        if not value
    ]
    if missing:
        raise ValueError("Set the required SAML environment variables: " + ", ".join(missing))

    return {
        "strict": True,
        "debug": False,
        "sp": {
            "entityId": SAML_SP_ENTITY_ID,
            "assertionConsumerService": {
                "url": SAML_ACS_URL,
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST",
            },
        },
        "idp": {
            "entityId": ENTRA_IDP_ENTITY_ID,
            "singleSignOnService": {
                "url": ENTRA_SAML_SSO_URL,
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
            },
            "x509cert": ENTRA_IDP_CERT,
        },
        "security": {
            "authnRequestsSigned": False,
            "wantAssertionsSigned": True,
            "wantMessagesSigned": False,
            "requestedAuthnContext": False,
        },
    }


def entra_saml_auth():
    request_data = {
        "https": "on" if request.is_secure else "off",
        "http_host": request.host,
        "server_port": str(request.environ.get("SERVER_PORT", "")),
        "script_name": request.path,
        "get_data": request.args.copy(),
        "post_data": request.form.copy(),
    }
    return OneLogin_Saml2_Auth(request_data, old_settings=entra_saml_settings())

@app.route("/")
def home():
    return f"""
    <html>
    <head>
        <title>Identity Portal</title>
    </head>
    <body>
        <h1>Identity Portal</h1>

        <!-- Okta IdP-Initiated Button -->
        <button onclick="window.location.href='{OKTA_APP_EMBED_LINK}'">
            Okta SAML Sign In
        </button>

        <br><br>

        <!-- Entra ID SP-Initiated SAML Button -->
        <button onclick="window.location.href='{url_for('entra_login')}'">
            Entra SAML Sign In
        </button>
    </body>
    </html>
    """


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("home"))


@app.route("/login/entra")
def entra_login():
    try:
        auth = entra_saml_auth()
    except (ValueError, OneLogin_Saml2_Error) as error:
        return html.escape(str(error)), 503

    login_url = auth.login()
    session["entra_saml_request_id"] = auth.get_last_request_id()
    return redirect(login_url)


@app.route("/acs/entra", methods=["POST"])
def entra_acs():
    if not request.form.get("SAMLResponse"):
        return "No SAML Response Found", 400

    request_id = session.pop("entra_saml_request_id", None)
    if not request_id:
        return "SAML login request is missing or expired. Start sign-in again.", 400

    try:
        auth = entra_saml_auth()
        auth.process_response(request_id)
    except Exception:
        app.logger.exception("Unable to process Entra SAML response")
        return "Unable to process the SAML response. Check the server log.", 400

    # errors = auth.get_errors()
    # if errors or not auth.is_authenticated():
    #     app.logger.warning("Entra SAML validation failed: %s", ", ".join(errors))
    #     return "SAML response validation failed. Check the Entra SAML configuration.", 400


    session["entra_authenticated"] = True
    return f"""
    <html>
    <body>
        <h1>Entra SAML response validated successfully</h1>
        <form action="{url_for('logout')}" method="post">
            <button type="submit">Log out</button>
        </form>
    </body>
    </html>
    """


@app.route("/acs", methods=["POST"])
def acs():
    saml_response = request.form.get("SAMLResponse")

    if not saml_response:
        return "No SAML Response Found", 400

    try:
        # Decode base64 SAML token
        decoded_bytes = base64.b64decode(saml_response)
        decoded_xml = decoded_bytes.decode('utf-8')

        # Escape HTML characters so the browser renders raw XML text safely
        safe_xml = html.escape(decoded_xml)
    except Exception as e:
        return f"Error decoding SAML payload: {str(e)}", 400

    return f"""
    <html>
    <body>
        <h1>SAML Assertion Received Successfully</h1>
        <pre style="background-color: #f4f4f4; padding: 15px; border: 1px solid #ccc; overflow: auto;">
{safe_xml}
        </pre>
        <form action="{url_for('logout')}" method="post">
            <button type="submit">Log out</button>
        </form>
    </body>
    </html>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=os.environ.get("FLASK_DEBUG") == "1")
