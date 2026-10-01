# SAML Identity Provider Test Lab

A small local test project for exploring identity-provider sign-in flows with a Python Flask service provider (SP) and a simple HTML identity portal. Okta is the currently configured provider. Microsoft Entra ID is a future integration; its current button only opens the Entra admin portal.

## Project Files

- `app.py` is the primary Flask application. It serves a basic portal at `/` and accepts IdP HTTP-POST responses at `/acs`.
- `index.html` is a separate static portal with Okta and Entra buttons. It is not currently served by the Flask application.
- `saml_sp.py` is another standalone Flask example with a similar `/acs` handler.
- `server.py` starts a static file server on port `8000`. It is an alternative to `app.py`, not something to run at the same time, because both use that port.

## Requirements

- Python 3.9 or later
- Flask
- An Okta SAML application configured to post to the SP's Assertion Consumer Service (ACS) URL
- For an IdP that must reach a local development machine, a public HTTPS tunnel such as ngrok

## Run Locally

From the project directory, create and activate a virtual environment, then install Flask:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install Flask
```

Start the primary Flask app:

```powershell
python app.py
```

The app listens on `http://localhost:8000`. Open that address in a browser. To expose the local app to an identity provider, start a separate terminal and run:

```powershell
ngrok http 8000
```

Use the HTTPS forwarding address ngrok provides when configuring the IdP ACS URL, with `/acs` appended (for example, `https://<your-ngrok-host>/acs`). The tunnel URL can change between sessions, so update the IdP configuration when it changes.

## Current Demo Flow

1. Open the portal and select the Okta sign-in button.
2. Okta handles the sign-in and, if the SAML app is configured for this SP, POSTs a `SAMLResponse` form field to the ACS endpoint.
3. The Flask handler base64-decodes the response and displays the XML in the browser.

The Okta application URL is currently hard-coded in `app.py` and `index.html`; update it to match your Okta configuration. The Entra button currently links to `https://entra.microsoft.com/` and does not initiate SAML authentication.

## Important Security Note

This is a learning and integration-test scaffold, not a production SAML service provider. The `/acs` handler only base64-decodes and displays the submitted response. It does not validate the XML signature, issuer, audience, recipient, destination, timestamps, or replay protection, and it does not establish an authenticated application session. Do not use it to make access-control decisions or expose it with real user data. Use a maintained SAML library and complete SP validation before relying on SAML assertions.

The decoded assertion may contain sensitive identity data. Avoid sharing or logging real SAML responses.

## Entra ID Follow-up

The Entra sign-in flow still needs to be implemented. At minimum, configure an Entra enterprise application for SAML, set its reply/ACS URL to the reachable `/acs` endpoint, and add the corresponding SP and IdP configuration and assertion validation. The current Entra portal link is only a placeholder.
