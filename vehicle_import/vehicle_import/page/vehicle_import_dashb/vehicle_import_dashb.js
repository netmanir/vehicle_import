frappe.require("/assets/vehicle_import/css/vehicle_import_dashboard.css");

const COLUMN_COLORS = [
    "#1976D2", // Blue
    "#388E3C", // Green
    "#F57C00", // Orange
    "#7B1FA2", // Purple
    "#C2185B", // Pink
    "#0097A7", // Cyan
    "#5D4037", // Brown
    "#455A64", // Blue Grey
    "#D32F2F", // Red
    "#689F38", // Lime
];

function get_column_color(name) {
    let hash = 0;
    for (const c of name) {
        hash = ((hash << 5) - hash) + c.charCodeAt(0);
        hash |= 0;
    }
    return COLUMN_COLORS[Math.abs(hash) % COLUMN_COLORS.length];
}

frappe.pages["vehicle-import-dashb"].on_page_load = function (wrapper) {

	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Vehicle Import Dashboard"),
		single_column: true
	});

	const board = $(`
		<div id="vi-dashboard-board"></div>
	`);

	$(page.body).append(board);

	frappe.call({
		method: "vehicle_import.vehicle_import.services.vehicle_import_dashboard.get_dashboard_data",
		callback: function (r) {

			const warehouses = r.message || [];

			warehouses.forEach(warehouse => {
				const color = get_column_color(warehouse.name);
				const column = $(`
					<div class="vi-column"
						data-warehouse="${warehouse.name}"
						style="
							--vi-column-color: ${color};
							--vi-column-bg: ${color}1A;
						">

						<div class="vi-column-header"
							title="${warehouse.warehouse_name}">
							${warehouse.warehouse_name}
						</div>
						<div class="vi-column-body"></div>
					</div>
				`);

				const body = column.find(".vi-column-body");
				(warehouse.holders || []).forEach(holder => {
					body.append(`
						<div class="vi-card" 
							draggable="true"
							data-holder="${holder.name}">
							<div class="vi-card-title">
								${holder.vehicle_holder_title || ""}
							</div>
							<div class="vi-card-doc">
								${holder.vehicle_holder_doc_nr || ""}
							</div>
						</div>
					`);
				});

				board.append(column);

				let dragged_card = null;
				// Start Drag
				board.on("dragstart", ".vi-card", function (e) {
					dragged_card = this;
					e.originalEvent.dataTransfer.effectAllowed = "move";
				});

				// Allow Drop
				board.on("dragover", ".vi-column-body", function (e) {
					e.preventDefault();
				});

				// Drop
				board.on("drop", ".vi-column-body", function (e) {
					e.preventDefault();
					if (!dragged_card)
						return;
					
					const body = this;
					const old_body = dragged_card.parentElement;
					if (old_body === body)
						return;

					body.appendChild(dragged_card);
					frappe.call({
						method: "vehicle_import.vehicle_import.services.vehicle_import_dashboard.move_holder",
						args: {
							holder: dragged_card.dataset.holder,
							warehouse: body.parentElement.dataset.warehouse
						},
						callback() {

							frappe.show_alert(__("Moved"));

						},
						error() {
							old_body.appendChild(dragged_card);
							frappe.msgprint(__("Unable to move!"));
						}
					});
				});
			});
		}
	});
};