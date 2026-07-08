import urllib.parse
import frappe
from frappe.tests import IntegrationTestCase
from werkzeug.test import Client
from werkzeug.wrappers import Response

class TestPresignedUrlE2E(IntegrationTestCase):
    def setUp(self):
        super().setUp()
        frappe.set_user("Administrator")
        self.test_files = []
        
        self.test_file_name = "_test_e2e_presigned.txt"
        if frappe.db.exists("File", {"file_name": self.test_file_name}):
            frappe.delete_doc("File", frappe.db.get_value("File", {"file_name": self.test_file_name}, "name"), force=1)
            
        self.test_file = frappe.get_doc({
            "doctype": "File",
            "file_name": self.test_file_name,
            "content": b"e2e test content",
            "is_private": 1
        }).insert()
        
        self.test_files.append(self.test_file.name)
        frappe.db.commit()
        
        from frappe.app import application
        self.client = Client(application, Response)
        
    def tearDown(self):
        frappe.set_user("Administrator")
        for file_name in self.test_files:
            if frappe.db.exists("File", file_name):
                frappe.delete_doc("File", file_name, force=1)
        frappe.db.commit()
                
        frappe.db.rollback()
        super().tearDown()

    def test_wsgi_successful_download(self):
        url = self.test_file.presigned_url
        
        # Parse the relative URL for werkzeug client
        relative_url = url.replace(frappe.utils.get_url(), "")
        
        # Test as unauthenticated user by clearing cookies/headers
        response = self.client.get(relative_url, base_url=f"http://{frappe.local.site}")
        
        print("WSGI Response status:", response.status_code)
        print("WSGI Response headers:", response.headers)
        print("WSGI Response data:", response.get_data(as_text=True))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, b"e2e test content")
        self.assertIn("attachment", response.headers.get("Content-Disposition", ""))
        self.assertIn(self.test_file.file_name, response.headers.get("Content-Disposition", ""))

    def test_wsgi_unauthorized_download(self):
        url = self.test_file.presigned_url
        relative_url = url.replace(frappe.utils.get_url(), "")
        
        # Tamper the token by replacing the last part of url (token)
        parsed = urllib.parse.urlparse(url)
        params = urllib.parse.parse_qs(parsed.query)
        token = params.get("token")[0]
        tampered_token = "A" + token[1:]
        
        # reconstruct URL with tampered token
        tampered_url = f"/api/method/frappe_core.file?file_name={self.test_file_name}&token={tampered_token}"
        
        response = self.client.get(tampered_url, base_url=f"http://{frappe.local.site}")
        
        self.assertEqual(response.status_code, 403)
