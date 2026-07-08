window.vehicle_import = window.vehicle_import || {};

window.vehicle_import.open_assign_vins_dialog = function (frm) {

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