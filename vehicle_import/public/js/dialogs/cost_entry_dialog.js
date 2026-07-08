window.vehicle_import = window.vehicle_import || {};

window.vehicle_import.open_cost_entry_dialog = function (options) {

    const dialog = new frappe.ui.Dialog({

        title: __("Add Cost"),

        size: "large",

        fields: [

            {
                fieldtype: "Date",
                fieldname: "cost_date",
                label: __("Cost Date"),
                default: frappe.datetime.nowdate(),
                reqd: 1,
            },
            {
                fieldtype: "Column Break",
            },
            {
                fieldtype: "Link",
                fieldname: "cost_category",
                label: __("Cost Category"),
                options: "Cost Category",
                reqd: 1,
            },

            {
                fieldtype: "Section Break",
            },

            {
                fieldtype: "Link",
                fieldname: "currency",
                label: __("Currency"),
                options: "Currency",
                default: frappe.defaults.get_default("currency"),
                reqd: 1,
            },
            {
                fieldtype: "Column Break",
            },
            {
                fieldtype: "Float",
                fieldname: "exchange_rate",
                label: __("Exchange Rate"),
                default: 1,
                reqd: 1,
            },
            {
                fieldtype: "Column Break",
            },
            {
                fieldtype: "Currency",
                fieldname: "foreign_amount",
                label: __("Amount"),
                reqd: 1,
            },

            {
                fieldtype: "Section Break",
            },

            {
                fieldtype: "Small Text",
                fieldname: "description",
                label: __("Description"),
            },

        ],

        primary_action_label: __("Save"),

        primary_action(values) {

            frappe.call({

                method:
                    "vehicle_import.vehicle_import.services.cost_entry_service.create_cost_entry",

                freeze: true,

                freeze_message: __("Saving..."),

                args: {

                    reference_doctype:
                        options.reference_doctype,
                    reference_name:
                        options.reference_name,

                    cost_date:
                        values.cost_date,
                    cost_category:
                        values.cost_category,

                    currency:
                        values.currency,
                    exchange_rate:
                        values.exchange_rate,
                    foreign_amount:
                        values.foreign_amount,

                    description:
                        values.description,

                },

                callback(r) {
                    
                    dialog.hide();

                    frappe.show_alert({
                        message: __("Cost Entry created."),
                        indicator: "green",
                    });

                    if (options.callback) {
                        options.callback(r.message);
                    }

                },

            });

        },

    });

    dialog.show();

};