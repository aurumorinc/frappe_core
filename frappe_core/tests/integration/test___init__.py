import os
import urllib.parse
import frappe
from frappe.tests import IntegrationTestCase
from frappe_core import file

class TestPresignedUrlIntegrationAPI(IntegrationTestCase):
    def setUp(self):
        super().setUp()
        self.test_files = []
        
        # Load real file from disk
        self.data_path = os.path.join(frappe.get_app_path("frappe_core"), "tests", "data", "sample_data.bin")
        with open(self.data_path, "rb") as f:
            self.file_content = f.read()
            
        self.test_file_name = "_test_integration_api_data.bin"
        if frappe.db.exists("File", {"file_name": self.test_file_name}):
            frappe.delete_doc("File", frappe.db.get_value("File", {"file_name": self.test_file_name}, "name"), force=1)
            
        self.test_file = frappe.get_doc({
            "doctype": "File",
            "file_name": self.test_file_name,
            "content": self.file_content,
            "is_private": 1
        }).insert()
        
        self.test_files.append(self.test_file.name)
        
    def tearDown(self):
        for file_name in self.test_files:
            if frappe.db.exists("File", file_name):
                frappe.delete_doc("File", file_name, force=1)
                
        frappe.db.rollback()
        super().tearDown()

    def test_real_file_download_api(self):
        url = self.test_file.presigned_url
        parsed = urllib.parse.urlparse(url)
        params = urllib.parse.parse_qs(parsed.query)
        token = params.get("token")[0]
        
        frappe.local.response = frappe._dict()
        
        frappe.set_user("Guest")
        try:
            file(self.test_file.file_name, token)
            
            self.assertEqual(frappe.local.response.filename, self.test_file.file_name)
            self.assertEqual(frappe.local.response.filecontent, self.file_content)
            self.assertEqual(frappe.local.response.type, "download")
        finally:
            frappe.set_user("Administrator")
