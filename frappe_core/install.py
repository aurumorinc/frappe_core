import frappe

def after_install():
    # Preseed Model Provider records
    providers = ["Google", "Anthropic", "OpenAI"]
    for provider in providers:
        if not frappe.db.exists("Model Provider", provider):
            doc = frappe.new_doc("Model Provider")
            doc.model_provider_name = provider
            doc.insert(ignore_permissions=True)
