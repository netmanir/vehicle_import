class AssignVINs_Dialog {

    static async show(frm = {}) {

        const assign_vins_dialog = new AssignVINs_Dialog(frm);
        return await assign_vins_dialog.show();
    }

    constructor(frm) {

        this.frm = frm;
    }


    async show() {

        const dialog = new frappe.ui.Dialog({

            title: __("Assign VINs"),
            size: "large",

            fields: [

                {
                    fieldtype: "Link",
                    fieldname: "vehicle_holder_detail",
                    label: __("Vehicle Holder Detail"),
                    options: "Vehicle Holder Detail",
                    reqd: 1,

                    change: async () => {

                        const name = dialog.get_value("vehicle_holder_detail");

                        console.log("name =", name);
                        console.log("type =", typeof name);
                        console.log("field =", dialog.fields_dict.vehicle_holder_detail.value);

                        if (!name) {
                            dialog.fields_dict.selected_product.$wrapper.empty();
                            return;
                        }

                        const holder_detail_result = await frappe.call({
                            method:
                                "vehicle_import.vehicle_import.doctype.vehicle_holder.vehicle_holder.get_holder_detail",
                            args: {
                                name: name,
                            },
                        });

                        console.log("Selected:", dialog.get_value("vehicle_holder_detail"));


                        if (!holder_detail_result.message) {
                            return;
                        }

                        dialog.fields_dict.selected_product.$wrapper.html(`
                            <div class="mb-3">
                                <b>${__("Selected Product")}:</b>
                                ${frappe.utils.escape_html(holder_detail_result.message.product)}
                                (${holder_detail_result.message.qty})
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

            primary_action: async (values) => {

                const assign_vins_result = await frappe.call({

                    method:
                        "vehicle_import.vehicle_import.doctype.vehicle_holder.vehicle_holder.assign_vins",

                    freeze: true,
                    freeze_message: __("Assigning VINs..."),

                    args: {
                        vehicle_holder: this.frm.doc.name,
                        vehicle_holder_detail: values.vehicle_holder_detail,
                        vins: values.vins,
                    },
                });

                if (!assign_vins_result.message) {
                    return;
                }

                if (!assign_vins_result.message.success) {

                    frappe.msgprint({
                        title: __("Validation Errors"),
                        indicator: "red",
                        message: assign_vins_result.message.errors.join("<br>"),
                    });

                    await this.frm.reload_doc();
                    return;
                }

                dialog.hide();

                await this.frm.reload_doc();

                frappe.show_alert({
                    message: __("VINs assigned successfully."),
                    indicator: "green",
                });
            },

        });

        dialog.fields_dict.vehicle_holder_detail.get_query = () => {

            return {
                query:
                    "vehicle_import.vehicle_import.doctype.vehicle_holder.vehicle_holder.vehicle_holder_detail_query",
                filters: {
                    parent: this.frm.doc.name,
                },
            };
        };

        dialog.show();       

        return dialog;
    }
}