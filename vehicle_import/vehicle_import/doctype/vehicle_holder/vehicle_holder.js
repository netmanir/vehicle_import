// Copyright (c) 2026, ACP and contributors
// For license information, please see license.txt

frappe.ui.form.on("Vehicle Holder", {
    refresh(frm) {

        // Add "Import Vehicles" button
        const can_import =
            !frm.is_new() &&
            frm.doc.docstatus === 0 &&
            !frm.doc.vehicle_holder_type_independent;
        if (can_import) {
            frm.add_custom_button(__("Import Vehicles"), async () => {

                const result = await ImportVehicles_Dialog.show({
                    current_holder: frm.doc.name || null
                });
                if (!result?.vehicles?.length) {
                    return;
                }

                await frappe.call({
                    method: "vehicle_import.vehicle_import.doctype.vehicle_holder.vehicle_holder.import_vehicles",
                    args: {
                        holder: frm.doc.name,
                        vehicles: result.vehicles
                    }
                });

                await frm.reload_doc();
            });
        }

        // Add "Assign VINs" button
        const can_assign_vin =
            !frm.is_new() &&
            frm.doc.docstatus === 0 &&
            !!frm.doc.vehicle_holder_history.length;
        if (can_assign_vin) {
            frm.add_custom_button(
                __("Assign VINs"),
                () => {
                    vehicle_import.open_assign_vins_dialog(frm);
                }
            );
        }
        
        // Add "Add Cost" button
        const can_add_cost =
            !frm.is_new() &&
            frm.doc.docstatus === 1;
        if (can_add_cost) {
            frm.add_custom_button(
                __("Add Cost"),
                () => {
                    vehicle_import.open_cost_entry_dialog({
                        reference_doctype: "Vehicle Holder",
                        reference_name: frm.doc.name,

                        callback() {
                            frm.reload_doc();
                        },
                    });
                }
            );
        }
        
        // Make "Vehicle Holder Dewtail" read-only if "Vehicle Holder" is not "Independent"
        frm.set_df_property(
            "vehicle_holder_detail", 
            "read_only", 
            !frm.doc.vehicle_holder_type_independent);
        frm.refresh_field("vehicle_holder_detail");
    }
});

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

