// Copyright (c) 2026, ACP and contributors
// For license information, please see license.txt

frappe.form.link_formatters["Quotage Detail"] = function (value, doc) {

    const detail = (cur_frm.doc.quotage_products || []).find(
        d => String(d.name) === String(value)
    );

    return `${detail.quotage_detail_product}`;
};

function can_edit_quotage_children() {
    return (
        frappe.user.has_role("System Manager")
        || frappe.user.has_role("Stock Manager")
    );
}

const editable = can_edit_quotage_children();

frappe.ui.form.on("Quotage", {
    refresh(frm) {
        frm.set_df_property(
            "quotage_products",
            "read_only",
            !editable
        );

        frm.set_df_property(
            "quotage_packing_list",
            "read_only",
            !editable
        );

        if (frm.is_new()) return;

        frm.add_custom_button(
            __("Assign VINs"),
            () => {
                open_assign_vins_dialog(frm);
            }
        );
    }

});

function open_assign_vins_dialog(frm) {

    const dialog = new frappe.ui.Dialog({
        title: __("Assign VINs"),
        size: "large",

        fields: [

            {
                fieldtype: "Link",
                fieldname: "quotage_detail",
                label: __("Quotage Detail"),
                options: "Quotage Detail",
                reqd: 1,

                change() {

                    const name = dialog.get_value("quotage_detail");

                    if (!name) {
                        dialog.fields_dict.selected_product.$wrapper.empty();
                        return;
                    }

                    frappe.call({
                        method:
                            "vehicle_import.vehicle_import.doctype.quotage.quotage.get_quotage_detail",

                        args: {
                            name: name,
                        },

                        callback(r) {

                            if (!r.message) return;

                            dialog.fields_dict.selected_product.$wrapper.html(`
                <div class="mb-3">
                    <b>${__("Selected Product")}:</b>
                    ${frappe.utils.escape_html(r.message.product)}
                    (${r.message.qty})
                </div>
            `);

                        },

                    });

                }

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
                    "vehicle_import.vehicle_import.doctype.quotage.quotage.assign_vins",

                freeze: true,
                freeze_message: __("Assigning VINs..."),

                args: {
                    quotage: frm.doc.name,
                    quotage_detail: values.quotage_detail,
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

    dialog.show();

    dialog.fields_dict.quotage_detail.get_query = function () {

        return {

            query: "vehicle_import.vehicle_import.doctype.quotage.quotage.quotage_detail_query",

            filters: {
                parent: frm.doc.name,
            },

        };

    };

}
