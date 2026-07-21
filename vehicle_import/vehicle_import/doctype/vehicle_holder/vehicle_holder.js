// Copyright (c) 2026, ACP and contributors
// For license information, please see license.txt

frappe.ui.form.on("Vehicle Holder", {
    
    setup(frm) {
        frm.set_query("vehicle_holder_warehouse", function () {
            return {
                filters: {
                    is_group: 0
                }
            };
        });
    },

    refresh(frm) {
        
        // Make "Vehicle Holder Detail" read-only if "Vehicle Holder" is not "Independent"
        frm.set_df_property(
            "vehicle_holder_detail", 
            "read_only", 
            !frm.doc.vehicle_holder_type_independent);
        frm.refresh_field("vehicle_holder_detail");

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
                        vehicles: result.vehicles,
                        reference: result.holder.name
                    }
                });

                await frm.reload_doc();
                
                frappe.show_alert({
                    message: __("Imported successfully."),
                    indicator: "green",
                });
                frappe.utils.play_sound("submit");
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
        
        // Add "Add Cost" button to Form
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
                        reference_date: frm.doc.vehicle_holder_posting_date,

                        callback() {
                            frm.reload_doc();
                        },
                    });
                }
            );
        }

        // Add "Add Cost" button to Vehicle Detial Grid
        setup_cost_entry_button_in_detail_grid(frm);
        
        // Vehicle Holder Costs
        vehicle_import.bind_tab_refresh(
            frm,
            "vehicle_holder_costs_tab",
            "vehicle_holder_costs",
            () => vehicle_import.load_vehicle_holder_costs(frm)
        );
        
        // Vehicle Holder Cost Report
        vehicle_import.bind_tab_refresh(
            frm,
            "vehicle_holder_costs_report_tab",
            "vehicle_holder_report",
            () => vehicle_import.load_vehicle_holder_cost_report(frm)
        );

        // Add "Submit Vehicle Holder" button
        if (frm.doc.docstatus === 0) {
            frm.add_custom_button(
                __("Submit Vehicle Holder"),
                async () => {
                    let message = __("This documents will submitted permanently!");
                    message += "<br>" + __("Do you want to continue?");

                    frappe.confirm(message, async () => {
                        await frappe.call({
                            method: "vehicle_import.vehicle_import.doctype.vehicle_holder.vehicle_holder.submit_vehicle_holder  ",
                            args: {
                                holder: frm.doc.name
                            }
                        });

                        frm.reload_doc();

                        frappe.show_alert({
                            message: __("Submitted successfully."),
                            indicator: "green",
                        });
                        frappe.utils.play_sound("submit");
                    });

                }, __("Actions"));
        } 

        // Add "Cancel Vehicle Holder" button
        if (frm.doc.docstatus === 1) {
            frm.add_custom_button(
                __("Cancel Vehicle Holder"),
                async () => {
                    const { message: links } = await frappe.call({
                        method: "vehicle_import.vehicle_import.doctype.vehicle_holder.vehicle_holder.get_cancel_preview",
                        args: {
                            holder: frm.doc.name
                        }
                    });

                    let message = __("The following related documents will also be cancelled:");

                    if (links.length) {

                        message += "<hr>";

                        links.forEach(link => {
                            message +=
                                `<span> • ${frappe.utils.get_form_link(
                                    link.reference_doctype,
                                    link.reference_docname,
                                    true
                                )}  </span>`;
                        });
                    }

                    message += "<hr>" + __("Do you want to continue?");

                    frappe.confirm(message, async () => {
                        await frappe.call({
                            method: "vehicle_import.vehicle_import.doctype.vehicle_holder.vehicle_holder.cancel_vehicle_holder",
                            args: {
                                holder: frm.doc.name
                            }
                        });

                        frm.reload_doc();

                        frappe.show_alert({
                            message: __("Cancelled successfully."),
                            indicator: "green",
                        });
						frappe.utils.play_sound("delete");
                    });

                }, __("Actions"));
        }
        
        show_detail_names(frm);
    },
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

function setup_cost_entry_button_in_detail_grid(frm) {
    if (frm.doc.docstatus !== 1) {
        return;
    }
    const grid = frm.fields_dict.vehicle_holder_detail.grid;
    grid.grid_rows.forEach(row => {
        if (!row.open_form_button) {
            row.add_open_form_button();
        }
        if (!row.open_form_button) {
            return;
        }

        // قبلاً اضافه شده؟
        if (row.open_form_button.find(".btn-cost-entry").length) {
            return;
        }

        const header = frm.fields_dict.vehicle_holder_detail.grid.wrapper.find(
            ".grid-heading-row .col:last"
        );
        header.css({
            minWidth: "45px",
            display: "flex",
            justifyContent: "center"
        });        
        row.open_form_button.parent().css({
            display: "flex",
            justifyContent: "center",
            minWidth: "45px",
        });
        row.open_form_button.css({
            display: "flex",
            alignItems: "center",
            gap: "6px"
        });
        const button = $(`
            <a class="btn-cost-entry"
               title="${__("Add Cost")}">
                ${frappe.utils.icon("circle-dollar-sign", "xs")}
            </a>
        `);
        button.tooltip({
            delay: {
                show: 600,
                hide: 100
            }
        });
        button.on("click", function (e) {
            e.preventDefault();
            e.stopPropagation();
            vehicle_import.open_cost_entry_dialog({
                reference_doctype: row.doc.doctype,
                reference_name: row.doc.name,
                reference_date: frm.doc.vehicle_holder_posting_date,
                callback() {
                    frm.reload_doc();
                }
            });
        });
        row.open_form_button.append(button);
    });
}

function show_detail_names(frm) {

    const grid = frm.fields_dict.vehicle_holder_detail.grid;

    grid.grid_rows.forEach(row => {

        const index = row.wrapper.find(".row-index span");

        if (index.length) {
            index.text(row.doc.name);
        }

    });

}

