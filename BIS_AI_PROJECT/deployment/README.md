# Hosting the React + Python application

The Docker image includes compiled UI and the authenticated API, not project data,
credentials, memory events, local backups or the old config containing fallback values.
Set BIS_ACCESS_PIN in the host secret store. Serve HTTPS through the host reverse proxy.
Run one worker. Mount persistent storage at /app/Google_Drive_Storage and import the
owner's approved product drafts/assets there. Do not publish that directory as static files.

Build from the BIS_AI_PROJECT directory: `docker build -t bis-workspace .`
Expose container port 8765 through the hosting platform's HTTPS service.
Without provisioned persistent storage this is not an acceptable production memory store.
No hosting account was created, paid plan selected, or project data uploaded in this update.

The current Streamlit Cloud deployment cannot run this separate container via a normal
git push. A container-capable hosting account or VPS must be connected to deploy it.
