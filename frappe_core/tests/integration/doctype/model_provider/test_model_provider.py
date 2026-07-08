import frappe
from frappe.tests import IntegrationTestCase

class TestModelProvider(IntegrationTestCase):
    def test_after_install_creates_providers(self):
        from frappe_core.install import after_install
        
        # Clean up any existing
        for p in ["Google", "Anthropic", "OpenAI"]:
            if frappe.db.exists("Model Provider", p):
                frappe.delete_doc("Model Provider", p)
                
        after_install()
        
        self.assertTrue(frappe.db.exists("Model Provider", "Google"))
        self.assertTrue(frappe.db.exists("Model Provider", "Anthropic"))
        self.assertTrue(frappe.db.exists("Model Provider", "OpenAI"))
