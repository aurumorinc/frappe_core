import frappe
from frappe.tests import IntegrationTestCase

class TestFile(IntegrationTestCase):
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
        # Delete physical files explicitly to prevent orphan files after rollback
        for file_name in self.test_files:
            if frappe.db.exists("File", file_name):
                frappe.delete_doc("File", file_name, force=1)
                
        frappe.db.rollback()
        super().tearDown()

    def test_generate_presigned_url(self):
        url = self.test_file.presigned_url
        self.assertTrue(url.startswith(frappe.utils.get_url()))
        self.assertIn("/api/method/frappe_core.file", url)
        self.assertNotIn(".download", url)
        self.assertIn(f"file_name={self.test_file.file_name}", url)
        self.assertIn("token=", url)
        
    def test_public_file_bypass(self):
        public_file = frappe.get_doc({
            "doctype": "File",
            "file_name": "_test_public_presigned.txt",
            "content": b"public content",
            "is_private": 0
        }).insert()
        
        self.test_files.append(public_file.name)
        
        url = public_file.presigned_url
        self.assertEqual(url, frappe.utils.get_url(public_file.file_url))
        self.assertNotIn("token=", url)
