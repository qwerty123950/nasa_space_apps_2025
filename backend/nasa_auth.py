# backend/nasa_auth.py

import requests
import netrc
import os

class NasaAuth(requests.auth.AuthBase):
    """
    A custom authentication handler for NASA Earthdata login,
    which uses a multi-step redirect process.
    """
    def __init__(self, username=None, password=None):
        # Allow explicit args to override environment variables
        env_user = os.getenv("EARTHDATA_USERNAME") or os.getenv("NASA_EARTHDATA_USERNAME") or os.getenv("URS_USERNAME")
        env_pass = os.getenv("EARTHDATA_PASSWORD") or os.getenv("NASA_EARTHDATA_PASSWORD") or os.getenv("URS_PASSWORD")
        self.username = username or env_user
        self.password = password or env_pass

        # Build candidate NETRC paths
        home = os.path.expanduser("~")
        candidates = []
        if os.getenv("NETRC"):
            candidates.append(os.path.expanduser(os.getenv("NETRC")))
        # On Windows, file is commonly _netrc; also try .netrc for flexibility
        candidates.append(os.path.join(home, "_netrc"))
        candidates.append(os.path.join(home, ".netrc"))

        # Deduplicate while preserving order
        seen = set()
        self.netrc_candidates = []
        for p in candidates:
            if p and p not in seen:
                self.netrc_candidates.append(p)
                seen.add(p)

    def find_creds(self):
        """Resolve URS credentials from, in order: explicit args, env vars, or a netrc file."""
        # 1) Explicit args or environment variables
        if self.username and self.password:
            return self.username, self.password

        # 2) Try NETRC locations
        errors = []
        for candidate in getattr(self, "netrc_candidates", []):
            try:
                if not os.path.exists(candidate):
                    continue
                info = netrc.netrc(candidate)
                auth = info.authenticators("urs.earthdata.nasa.gov")
                if auth and auth[0] and auth[2]:
                    return auth[0], auth[2]  # (login, password)
            except (FileNotFoundError, netrc.NetrcParseError, KeyError, TypeError) as e:
                errors.append(f"{candidate}: {e}")

        # Nothing found
        searched = ", ".join(getattr(self, "netrc_candidates", [])) if getattr(self, "netrc_candidates", []) else "(none)"
        raise Exception(
            "Could not find URS credentials. "
            f"Searched NETRC locations: {searched}. "
            "Provide credentials via environment variables EARTHDATA_USERNAME/EARTHDATA_PASSWORD "
            "(or NASA_EARTHDATA_USERNAME/NASA_EARTHDATA_PASSWORD), "
            "set NETRC to the path of your .netrc/_netrc file, or create a _netrc/.netrc in your home directory with:\n"
            "machine urs.earthdata.nasa.gov login YOUR_USERNAME password YOUR_PASSWORD"
        )

    def handle_redirect(self, r, **kwargs):
        """
        Handles the redirect to the Earthdata login page by submitting
        the login form with the user's credentials.
        """
        # We only care about redirects to the URS login page
        if r.is_redirect and "urs.earthdata.nasa.gov" in r.headers["Location"]:
            redirect_url = r.headers["Location"]
            
            username, password = self.find_creds()
            
            # Use the same session to POST to the login form
            auth_resp = r.connection.send(
                requests.Request(
                    "POST",
                    redirect_url,
                    data={"username": username, "password": password},
                    cookies=r.cookies,
                ).prepare(),
                **kwargs,
            )
            
            auth_resp.history.append(r)
            return auth_resp
        return r

    def __call__(self, r):
        # THE FIX IS HERE: The hook must be assigned as a list.
        r.hooks["response"] = [self.handle_redirect]
        return r

def create_authenticated_session():
    """
    Create a requests.Session configured with HTTP Basic Auth for URS.
    Using Basic Auth across redirects is the recommended and most reliable
    method for GES DISC/Earthdata programmatic access.
    """
    session = requests.Session()
    # Resolve credentials (env/args/netrc)
    helper = NasaAuth()
    username, password = helper.find_creds()
    session.auth = requests.auth.HTTPBasicAuth(username, password)
    # Allow requests to send credentials when redirected to URS
    session.max_redirects = 10
    return session