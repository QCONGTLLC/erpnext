# Copyright (c) 2015, Frappe Technologies Pvt. Ltd.
# License: GNU General Public License v3

from collections.abc import Iterator
from operator import itemgetter

import frappe
from frappe import _
from frappe.utils import cint, date_diff, flt, get_datetime

from erpnext.stock.doctype.serial_no.serial_no import get_serial_nos

Filters = frappe._dict


def execute(filters: Filters = None) -> tuple:
	to_date = filters["to_date"]
	filters.ranges = [num.strip() for num in filters.range.split(",") if num.strip().isdigit()]

	columns = get_columns(filters)
	item_details = FIFOSlots(filters).generate()
	data = format_report_data(filters, item_details, to_date)
	chart_data = get_chart_data(data, filters)

	return columns, data, None, chart_data


def format_report_data(filters: Filters, item_details: dict, to_date: str) -> list:
	data = []
	precision = cint(frappe.db.get_single_value("System Settings", "float_precision", cache=True))

	for _item, item_dict in item_details.items():
		if not flt(item_dict.get("total_qty"), precision):
			continue

		details = item_dict["details"]
		fifo_queue = sorted(filter(itemgetter(1), item_dict["fifo_queue"]), key=itemgetter(1))

		if not fifo_queue:
			continue

		average_age = get_average_age(fifo_queue, to_date)
		earliest_age = date_diff(to_date, fifo_queue[0][1])
		latest_age = date_diff(to_date, fifo_queue[-1][1])

		range_values = get_range_age(filters, fifo_queue, to_date, item_dict)

		row = [
			details.name,
			details.item_name,
			details.description,
			details.item_group,
			details.brand,
		]

		if filters.get("show_warehouse_wise_stock"):
			row.append(details.warehouse)

		row.extend(
			[
				flt(item_dict.get("total_qty"), precision),
				details.valuation_rate,
				average_age,
				*range_values,
				earliest_age,
				latest_age,
				details.stock_uom,
			]
		)

		data.append(row)

	return data


def get_average_age(fifo_queue: list, to_date: str) -> float:
	age_qty = total_qty = 0.0

	for batch in fifo_queue:
		batch_age = date_diff(to_date, batch[1])
		qty = batch[0] if isinstance(batch[0], (int, float)) else 1

		age_qty += batch_age * qty
		total_qty += qty

	return flt(age_qty / total_qty, 2) if total_qty else 0.0


def get_range_age(filters: Filters, fifo_queue: list, to_date: str, item_dict: dict) -> list:
	precision = cint(frappe.db.get_single_value("System Settings", "float_precision", cache=True))
	range_values = [0.0] * (len(filters.ranges) + 1)

	for item in fifo_queue:
		age = flt(date_diff(to_date, item[1]))
		qty = flt(item[0]) if not item_dict["has_serial_no"] else 1.0

		for i, age_limit in enumerate(filters.ranges):
			if age <= flt(age_limit):
				range_values[i] = flt(range_values[i] + qty, precision)
				break
		else:
			range_values[-1] = flt(range_values[-1] + qty, precision)

	return range_values


def get_columns(filters: Filters) -> list:
	range_columns = []
	setup_ageing_columns(filters, range_columns)

	columns = [
		{"label": _("Item Code"), "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 120},
		{"label": _("Item Name"), "fieldname": "item_name", "width": 150},
		{"label": _("Description"), "fieldname": "description", "width": 200},
		{"label": _("Item Group"), "fieldname": "item_group", "fieldtype": "Link", "options": "Item Group", "width": 120},
		{"label": _("Brand"), "fieldname": "brand", "fieldtype": "Link", "options": "Brand", "width": 120},
	]

	if filters.get("show_warehouse_wise_stock"):
		columns.append(
			{"label": _("Warehouse"), "fieldname": "warehouse", "fieldtype": "Link", "options": "Warehouse", "width": 140}
		)

	columns.extend(
		[
			{"label": _("Available Qty"), "fieldname": "qty", "fieldtype": "Float", "width": 110},
			{"label": _("Valuation Rate"), "fieldname": "valuation_rate", "fieldtype": "Currency", "width": 120},
			{"label": _("Average Age"), "fieldname": "average_age", "fieldtype": "Float", "width": 110},
		]
	)

	columns.extend(range_columns)

	columns.extend(
		[
			{"label": _("Earliest"), "fieldname": "earliest", "fieldtype": "Int", "width": 80},
			{"label": _("Latest"), "fieldname": "latest", "fieldtype": "Int", "width": 80},
			{"label": _("UOM"), "fieldname": "uom", "fieldtype": "Link", "options": "UOM", "width": 90},
		]
	)

	return columns


def setup_ageing_columns(filters: Filters, range_columns: list):
	prev = 0
	ranges = []

	for r in filters.ranges:
		ranges.append(f"{prev} - {r}")
		prev = cint(r) + 1

	ranges.append(f"{prev} - Above")

	for i, label in enumerate(ranges):
		add_column(range_columns, _("Age ({0})").format(label), f"range{i + 1}")


def add_column(cols, label, fieldname, fieldtype="Float", width=140):
	cols.append(dict(label=label, fieldname=fieldname, fieldtype=fieldtype, width=width))


def get_chart_data(data: list, filters: Filters) -> dict:
	if not data or filters.get("show_warehouse_wise_stock"):
		return {}

	data.sort(key=lambda r: r[7], reverse=True)
	data = data[:10]

	return {
		"data": {
			"labels": [d[0] for d in data],
			"datasets": [{"name": _("Average Age"), "values": [d[7] for d in data]}],
		},
		"type": "bar",
	}


# ================= FIFO ENGINE (UNCHANGED) =================

class FIFOSlots:
	"""FIFO logic untouched"""

	# 🔹 FULL FIFO CLASS CONTENT REMAINS EXACTLY THE SAME AS YOUR ORIGINAL
	# 🔹 NO CHANGES NEEDED BELOW THIS POINT

	# (keep your existing FIFOSlots class exactly as-is)
