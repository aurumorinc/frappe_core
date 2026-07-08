import os
import frappe
from frappe.tests import IntegrationTestCase

class TestFileIntegration(IntegrationTestCase):
    def setUp(self):
        super().setUp()
        self.test_files = []
        
        # Load real file from disk
        self.data_path = os.path.join(frappe.get_app_path("frappe_core"), "tests", "data", "sample_image.jpg")
        with open(self.data_path, "rb") as f:
            self.file_content = f.read()
            
        self.test_file_name = "_test_integration_image.jpg"
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

    def test_real_file_presigned_url(self):
        url = self.test_file.presigned_url
        self.assertTrue(url.startswith(frappe.utils.get_url()))
        self.assertIn("/api/method/frappe_core.file", url)
        self.assertNotIn(".download", url)
        self.assertIn(f"file_name={self.test_file.file_name}", url)
        self.assertIn("token=", url)
