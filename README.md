# Python SAML Test Lab

A compact, all-in-one SAML test service provider (SP) built with Flask. It provides a simple identity-provider portal and separate Okta and Microsoft Entra test paths. Use it to observe SAML redirects, configure an ACS endpoint, and exercise an SP-initiated Entra flow without building a full application.

This repository is an integration and learning tool, **not a production identity service**. Read [Security and Limitations](#security-and-limitations) before using it with real accounts or identity data.

## What It Does

- Presents Okta and Microsoft Entra sign-in buttons from one Flask page.
- Sends the Okta button to the configured Okta app URL.
- Starts an Entra SP-initiated SAML flow by generating an `AuthnRequest` and redirecting to the tenant's SAML endpoint.
- Receives Entra's HTTP-POST response at a dedicated ACS route.
- Provides a local logout button on each response page that clears the Flask session and returns to the portal.
- Keeps the minimal HTML and alternate Python server examples available for experimentation.

## Request Flow

### Okta

1. Open the Flask portal and select **Okta SAML Sign In**.
2. The browser navigates to the Okta URL hard-coded in `app.py`.
3. Okta posts its `SAMLResponse` to the configured ACS. In this project, `/acs` base64-decodes and displays the XML for inspection; it does not validate that response.

Configure the Okta app's ACS/Single sign-on URL to the public `/acs` URL if you intend to use this demo route. Update `OKTA_APP_EMBED_LINK` in `app.py` to your Okta application launch URL.

### Microsoft Entra ID

1. Open the portal on the public HTTPS ngrok URL and select **Entra SAML Sign In**.
2. `/login/entra` creates a SAML `AuthnRequest` and redirects the browser to `https://login.microsoftonline.com/<tenant-id>/saml2`.
3. Entra authenticates the user and posts a `SAMLResponse` to `/acs/entra`.
4. The handler passes the response to `python3-saml` and shows a result page. Use **Log out** to clear this app's Flask session and return to the portal.

The Entra flow is SP-initiated. The configured Entra **Sign-on URL** must start the flow at `/login/entra`; the ACS URL is only for receiving the response and must not be used as the sign-on URL.

## Routes

| Route | Method | Purpose |
| --- | --- | --- |
| `/` | GET | Identity portal with Okta and Entra buttons |
| `/login/entra` | GET | Creates and sends an Entra SAML AuthnRequest |
| `/acs/entra` | POST | Entra SAML assertion consumer endpoint |
| `/acs` | POST | Okta/demo ACS that decodes and displays the submitted XML |
| `/logout` | POST | Clears the local Flask session and redirects to `/` |

## Repository Layout

| File | Purpose |
| --- | --- |
| `app.py` | Primary Flask portal, Entra SAML flow, Okta demo flow, and logout |
| `requirements.txt` | Flask and `python3-saml` dependencies |
| `index.html` | Separate static portal experiment; it is not served by the Flask app |
| `saml_sp.py` | Older standalone Flask ACS example; it is not the primary app |
| `server.py` | Static file server alternative; it uses port 8000 like `app.py` |

Run `app.py` for the combined portal. Do not run `server.py` or `saml_sp.py` at the same time on port 8000.

## Requirements

- Python 3.9 or newer
- The packages listed in `requirements.txt`
- An Okta SAML application for the Okta demo, and/or an Entra enterprise application configured for SAML
- ngrok or another public HTTPS tunnel when an identity provider must reach the local ACS

## Install

From the repository directory, create and activate a virtual environment and install dependencies:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

The `python3-saml` package installs its XML and XML-signature dependencies as well.

## Configure Entra

Start ngrok in one terminal and copy its current HTTPS forwarding hostname:

```powershell
ngrok http 8000
```

In Entra, open the enterprise application and configure **Single sign-on > SAML**. Set the fields to match the Flask app:

| Entra field | Value |
| --- | --- |
| Identifier (Entity ID) | Exactly the value of `SAML_SP_ENTITY_ID` |
| Reply URL (Assertion Consumer Service URL) | Exactly the value of `SAML_ACS_URL`; path must be `/acs/entra` |
| Sign-on URL | `https://<current-ngrok-host>/login/entra` |
| Relay State | Leave blank unless you have a specific use for it |
| Logout URL | Leave blank; SAML Single Logout is not implemented |
| Signing option | **Sign SAML response and assertion** is supported; the app requires the assertion to be signed |

Assign the test user to the enterprise application. Copy the Entra **Issuer**, **Login URL**, and active **Certificate (Base64)** from the SAML configuration or federation metadata. The tenant-based defaults in `app.py` should be checked against the values Entra displays.

## Run the App

Set the environment variables in the PowerShell terminal where Flask will run. Replace the placeholders with your tenant values and current ngrok hostname:

```powershell
$env:ENTRA_TENANT_ID = "<your-tenant-guid>"
$env:ENTRA_IDP_ENTITY_ID = "https://sts.windows.net/<your-tenant-guid>/"
$env:ENTRA_SAML_SSO_URL = "https://login.microsoftonline.com/<your-tenant-guid>/saml2"
$env:ENTRA_IDP_CERT = "<Base64 signing certificate from Entra>"
$env:SAML_SP_ENTITY_ID = "<same Identifier configured in Entra>"
$env:SAML_ACS_URL = "https://<current-ngrok-host>/acs/entra"
$env:FLASK_SECRET_KEY = (& .\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(32))")
```

Set `ENTRA_IDP_CERT` using either of these approaches:

- Put the Base64 certificate body on **one line**, removing PEM header/footer lines and all line breaks.
- Save the complete PEM certificate (including its `BEGIN CERTIFICATE` and `END CERTIFICATE` lines) to a file, then load the file contents into the variable with PowerShell: `$env:ENTRA_IDP_CERT = Get-Content -Raw .\entra-signing-cert.pem`.

The variable must contain the certificate text, not the file path. Loading the complete PEM with `Get-Content -Raw` avoids manually pasting multiline text into a quoted PowerShell assignment. The SAML library normalizes PEM headers and line breaks. This is Entra's public signing certificate, not a private key. Do not paste private keys into environment variables or commit credentials/certificates to source control.

`ENTRA_TENANT_ID` has a project default. `ENTRA_IDP_ENTITY_ID` and `ENTRA_SAML_SSO_URL` are derived from that tenant if not set, but should match Entra's displayed SAML values. `ENTRA_IDP_CERT`, `SAML_SP_ENTITY_ID`, and `SAML_ACS_URL` are required for Entra login. Set the environment before launching Python because the app reads these values at startup.

Start the Flask app in that same terminal:

```powershell
python app.py
```

For Entra, browse to `https://<current-ngrok-host>/` rather than `http://localhost:8000/`. The SAML request is correlated using the Flask session cookie; starting on localhost and returning to the ngrok hostname would split the session across different browser hosts. The local address can still be used for basic portal checks.

When ngrok changes its hostname, update `SAML_ACS_URL`, the Entra Reply URL, and the Entra Sign-on URL together. Keep `SAML_SP_ENTITY_ID` identical to the Entra Identifier. A stable Entity ID can be used if you prefer not to change the identifier when a temporary tunnel hostname changes.

## Logout Behavior

The **Log out** buttons submit to `/logout`, which clears the local Flask session and returns the browser to `/`. This is not an Entra or Okta Single Logout flow. The identity provider's own browser session may remain active, so a subsequent sign-in can happen without prompting for credentials.

## Security and Limitations

This project is intended for controlled testing only. Do not rely on its result pages to authenticate users or authorize access to protected resources.

The Entra browser flow has been verified end to end with the configured tenant. One implementation limitation remains: the Entra route calls `auth.process_response(request_id)`, but the follow-up `auth.get_errors()` and `auth.is_authenticated()` checks are currently commented out in `app.py`. The success page therefore should not be treated as proof that every assertion-validation check passed until those checks are enabled and tested.

Other limitations:

- The Okta `/acs` route only base64-decodes and displays XML. It does not verify signatures, issuer, audience, destination, timestamps, or replay.
- The app has no user database, authorization policy, or protected application area.
- The Flask session is client-side signed session data, not a server-side session store. A generated fallback secret changes on restart; set `FLASK_SECRET_KEY` to a stable random value for a test session.
- SAML Single Logout, IdP-initiated Entra login, and SP metadata publishing are not implemented.
- The session cookie is configured as Secure and SameSite=None, with a Partitioned attribute. Test SAML through HTTPS, such as the ngrok URL.
- SAML assertions can contain personal information. Do not share raw SAML responses, browser traces, or logs containing identity data.

### Browser Diagnostics

Install the **SAML-tracer** browser extension when investigating a SAML flow. It is a diagnostic aid, not a runtime requirement. Start a capture, reproduce the sign-in, and inspect the redirects plus the SAML request/response entries and their HTTP status codes. This helps confirm whether Entra sent a SAML response to `/acs/entra` and what the browser received from Entra.

SAML-tracer captures browser traffic; it does not expose Flask's internal exception details. When the app displays its generic SAML-processing error, also inspect the terminal running `python app.py`, where the exception is logged. Entra-side sign-in errors may be shown directly in the browser. Redact assertions, identifiers, cookies, and other personal or session data before sharing a trace.

Never use this project as-is for production authentication or authorization.

## Troubleshooting

| Symptom | Checks |
| --- | --- |
| `/login/entra` returns 503 | Confirm `ENTRA_IDP_CERT`, `SAML_SP_ENTITY_ID`, and `SAML_ACS_URL` were set in the same terminal before starting Flask |
| Entra reports Reply URL mismatch | The Entra Reply URL must exactly match `SAML_ACS_URL`, including HTTPS, hostname, path, and trailing slash behavior; the path is `/acs/entra` |
| Entra returns an error before posting a response | Check Identifier, Sign-on URL (`/login/entra`), tenant SAML configuration, and user assignment |
| ACS says the login request is missing or expired | Start login and callback on the same ngrok HTTPS hostname; check that browser cookies are enabled and `FLASK_SECRET_KEY` stays unchanged during the flow |
| SAML response processing fails | Check the Flask terminal for the exception, and verify the Entra Issuer and active signing certificate match the values configured in the environment |
| Certificate/signature errors | Confirm `ENTRA_IDP_CERT` contains the active Entra signing certificate as one continuous Base64 line, then capture the flow with SAML-tracer to check the browser's SAML response and status |
| Port 8000 is already in use | Stop the other local server or configure both Flask and ngrok to use a different matching port |

There is no dedicated automated test suite in this repository. The Flask test client can be used for route-level checks, but a real SAML round trip requires matching Entra configuration, certificate, and a reachable HTTPS ACS.

