import time
import jwt
import urllib.parse
import frappe
from frappe.tests import IntegrationTestCase
from frappe_core import file

class TestPresignedUrlAPI(IntegrationTestCase):
    def setUp(self):
        super().setUp()
        self.test_files = []
        
        self.test_file_name = "_test_presigned.txt"
        if frappe.db.exists("File", {"file_name": self.test_file_name}):
            frappe.delete_doc("File", frappe.db.get_value("File", {"file_name": self.test_file_name}, "name"), force=1)
            
        self.test_file = frappe.get_doc({
            "doctype": "File",
            "file_name": self.test_file_name,
            "content": b"test content",
            "is_private": 1
        }).insert()
        
        self.test_files.append(self.test_file.name)
        
    def tearDown(self):
        for file_name in self.test_files:
            if frappe.db.exists("File", file_name):
                frappe.delete_doc("File", file_name, force=1)
                
        frappe.db.rollback()
        super().tearDown()

    def test_api_success(self):
        url = self.test_file.presigned_url
        parsed = urllib.parse.urlparse(url)
        params = urllib.parse.parse_qs(parsed.query)
        token = params.get("token")[0]
        
        frappe.local.response = frappe._dict()
        
        frappe.set_user("Guest")
        try:
            file(self.test_file.file_name, token)
            
            self.assertEqual(frappe.local.response.filename, self.test_file.file_name)
            content = frappe.local.response.filecontent
            if isinstance(content, str):
                content = content.encode("utf-8")
            self.assertEqual(content, b"test content")
            self.assertEqual(frappe.local.response.type, "download")
        finally:
            frappe.set_user("Administrator")
            
    def test_api_expired_token(self):
        secret = frappe.conf.get("encryption_key") or frappe.local.site
        payload = {
            "name": self.test_file.name,
            "file_name": self.test_file.file_name,
            "file_url": self.test_file.file_url,
            "exp": int(time.time()) - 100
        }
        token = jwt.encode(payload, secret, algorithm="HS256")
        
        with self.assertRaises(frappe.PermissionError) as e:
            file(self.test_file.file_name, token)
        
        self.assertEqual(str(e.exception), "Presigned URL has expired")
        
    def test_api_tampered_token(self):
        url = self.test_file.presigned_url
        parsed = urllib.parse.urlparse(url)
        params = urllib.parse.parse_qs(parsed.query)
        token = params.get("token")[0]
        
        tampered_token = "A" + token[1:]
        
        with self.assertRaises(frappe.PermissionError) as e:
            file(self.test_file.file_name, tampered_token)
            
        self.assertEqual(str(e.exception), "Invalid signature")
