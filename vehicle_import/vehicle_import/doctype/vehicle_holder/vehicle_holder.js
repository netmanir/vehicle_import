// Copyright (c) 2026, ACP and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Vehicle Holder", {
// 	refresh(frm) {

// 	},
// });

frappe.form.link_formatters["Vehicle Holder Detail"] = function (value) {

    if (!cur_frm?.doc) {
        return value;
    }

    const detail = (cur_frm.doc.vehicle_holder_detail || []).find(
        d => String(d.name) === String(value)
    );

    if (!detail) {
        return value;
    }

    return detail.vehicle_holder_detail_item || value;
};