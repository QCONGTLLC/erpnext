import frappe
from frappe.utils import getdate

def execute(filters=None):

    columns = get_columns()
    data = get_data(filters)

    return columns, data


def get_data(filters):

    from_date = filters.get("from_date")
    to_date = filters.get("to_date")

    # PURCHASE
    purchase = frappe.db.sql("""
        SELECT
            DATE_FORMAT(pi.posting_date, '%Y-%m') AS month,
            pii.item_code,
            pii.item_name,
            pii.brand,
            pi.supplier,
            SUM(pii.qty) AS purchase_qty,
            SUM(pii.amount) AS purchase_value
        FROM `tabPurchase Invoice Item` pii
        INNER JOIN `tabPurchase Invoice` pi ON pi.name = pii.parent
        WHERE pi.docstatus = 1
        AND pi.posting_date BETWEEN %s AND %s
        GROUP BY month, pii.item_code, pi.supplier
    """, (from_date, to_date), as_dict=True)

    # SALES
    sales = frappe.db.sql("""
        SELECT
            DATE_FORMAT(si.posting_date, '%Y-%m') AS month,
            sii.item_code,
            SUM(sii.qty) AS sales_qty,
            SUM(sii.amount) AS sales_value
        FROM `tabSales Invoice Item` sii
        INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
        WHERE si.docstatus = 1
        AND si.posting_date BETWEEN %s AND %s
        GROUP BY month, sii.item_code
    """, (from_date, to_date), as_dict=True)

    result = {}

    # build purchase map
    for p in purchase:
        key = (p.month, p.item_code)
        result[key] = {
            "month": p.month,
            "item_code": p.item_code,
            "item_name": p.item_name,
            "brand": p.brand,
            "supplier": p.supplier,
            "purchase_qty": p.purchase_qty,
            "purchase_value": p.purchase_value,
            "sales_qty": 0,
            "sales_value": 0
        }

    # merge sales
    for s in sales:
        key = (s.month, s.item_code)

        if key in result:
            result[key]["sales_qty"] = s.sales_qty
            result[key]["sales_value"] = s.sales_value
        else:
            result[key] = {
                "month": s.month,
                "item_code": s.item_code,
                "item_name": "",
                "brand": "",
                "supplier": "",
                "purchase_qty": 0,
                "purchase_value": 0,
                "sales_qty": s.sales_qty,
                "sales_value": s.sales_value
            }

    return list(result.values())


def get_columns():
    return [
        {"label": "Month", "fieldname": "month", "fieldtype": "Data", "width": 120},
        {"label": "Item", "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 180},
        {"label": "Brand", "fieldname": "brand", "fieldtype": "Data", "width": 120},
        {"label": "Supplier", "fieldname": "supplier", "fieldtype": "Link", "options": "Supplier", "width": 180},
        {"label": "Purchase Qty", "fieldname": "purchase_qty", "fieldtype": "Float", "width": 120},
        {"label": "Purchase Value", "fieldname": "purchase_value", "fieldtype": "Currency", "width": 140},
        {"label": "Sales Qty", "fieldname": "sales_qty", "fieldtype": "Float", "width": 120},
        {"label": "Sales Value", "fieldname": "sales_value", "fieldtype": "Currency", "width": 140},
    ]
