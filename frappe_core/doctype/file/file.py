import time
import jwt
import frappe
from frappe.core.doctype.file.file import File
from frappe.utils import get_url

class _File(File):
    def get_presigned_url(self, expires_in=3600) -> str:
        """
        Generate a presigned URL for downloading a file securely.
        Defaults to 1 hour expiration.
        """
        if not self.is_private:
            return get_url(self.file_url)

        exp = int(time.time()) + expires_in
        payload = {
            "name": self.name,
            "file_name": self.file_name,
            "file_url": self.file_url,
            "exp": exp
        }
        
        secret = frappe.conf.get("encryption_key") or frappe.local.site
        
        token = jwt.encode(payload, secret, algorithm="HS256")
        
        # Build the url
        return f"{get_url()}/api/method/frappe_core.file?file_name={self.file_name}&token={token}"

    @property
    def presigned_url(self):
        return self.get_presigned_url()
