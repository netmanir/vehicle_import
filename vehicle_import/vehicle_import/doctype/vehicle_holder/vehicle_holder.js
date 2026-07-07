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
        frm.add_custom_button(
            __("Assign VINs"),
            () => {
                open_assign_vins_dialog(frm);
            }
        );
        
        // frm.add_custom_button(__("Assign VINs"), async () => {
            
        //     const result = await AssignVINs_Dialog.show(frm);
        //     if (!result?.vehicles?.length) {
        //         return;
        //     }
        // });
        
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


function open_assign_vins_dialog(frm) {

    const dialog = new frappe.ui.Dialog({

        title: __("Assign VINs"),
        size: "large",

        fields: [

            {
                fieldtype: "Select",
                fieldname: "vehicle_holder_detail",
                label: __("Vehicle Holder Detail"),
                reqd: 1,

                change() {

                    const name = dialog.get_value("vehicle_holder_detail");

                    if (!name) {
                        dialog.fields_dict.selected_product.$wrapper.empty();
                        return;
                    }

                    const detail = (frm.doc.vehicle_holder_detail || []).find(
                        d => String(d.name) === String(name)
                    );

                    if (!detail) {
                        dialog.fields_dict.selected_product.$wrapper.empty();
                        return;
                    }

                    dialog.fields_dict.selected_product.$wrapper.html(`
                        <div class="mb-3">
                            <b>${__("Selected Product")}:</b>
                            ${frappe.utils.escape_html(detail.vehicle_holder_detail_item)}
                            (${detail.vehicle_holder_detail_quantity})
                        </div>
                    `);
                },
            },

            {
                fieldtype: "HTML",
                fieldname: "selected_product",
            },

            {
                fieldtype: "Section Break",
            },

            {
                fieldtype: "Code",
                fieldname: "vins",
                label: __("VINs"),
                reqd: 1,
                options: "Text",
                description: __("Enter one VIN per line."),
            },

        ],

        primary_action_label: __("Assign"),

        primary_action(values) {

            frappe.call({

                method:
                    "vehicle_import.vehicle_import.doctype.vehicle_holder.vehicle_holder.assign_vins",

                freeze: true,
                freeze_message: __("Assigning VINs..."),

                args: {
                    vehicle_holder: frm.doc.name,
                    vehicle_holder_detail: values.vehicle_holder_detail,
                    vins: values.vins,
                },

                callback(r) {

                    if (!r.message) {
                        return;
                    }

                    if (!r.message.success) {

                        frappe.msgprint({
                            title: __("Validation Errors"),
                            indicator: "red",
                            message: r.message.errors.join("<br>"),
                        });

                        frm.reload_doc();
                        return;
                    }

                    dialog.hide();

                    frm.reload_doc();

                    frappe.show_alert({
                        message: __("VINs assigned successfully."),
                        indicator: "green",
                    });
                },
            });
        },
    });

    const options = [""];

    (frm.doc.vehicle_holder_detail || []).forEach(detail => {

        options.push({
            value: detail.name,
            label:
                `${detail.vehicle_holder_detail_item} (${detail.vehicle_holder_detail_quantity})`,
        });

    });

    dialog.fields_dict.vehicle_holder_detail.df.options = options;

    dialog.refresh();

    dialog.show();
}