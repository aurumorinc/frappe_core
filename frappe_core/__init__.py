__version__ = "0.0.1"

import time
import jwt
import frappe

@frappe.whitelist(allow_guest=True)
def file(file_name, token):
    secret = frappe.conf.get("encryption_key") or frappe.local.site
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        frappe.throw("Presigned URL has expired", frappe.PermissionError)
    except jwt.InvalidTokenError:
        frappe.throw("Invalid signature", frappe.PermissionError)
        
    file_url = payload.get("file_url")
    file_doc_name = payload.get("name")
    
    if not file_url or not file_doc_name:
        frappe.throw("Invalid payload", frappe.PermissionError)
        
    # Ignore permissions so guests can download private files with a valid token
    ignore_permissions = frappe.flags.ignore_permissions
    frappe.flags.ignore_permissions = True
    
    try:
        file_doc = frappe.get_doc("File", file_doc_name)
        
        if file_doc.file_url != file_url:
            raise frappe.PermissionError
            
        frappe.local.response.filename = payload.get("file_name") or file_name
        frappe.local.response.filecontent = file_doc.get_content()
        frappe.local.response.type = "download"
        
    except frappe.DoesNotExistError:
        raise frappe.DoesNotExistError
    finally:
        frappe.flags.ignore_permissions = ignore_permissions
