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

function format_money(amount) {
    amount = amount || 0;
    if (amount >= 1000000000)
        return (amount / 1000000000).toFixed(1) + ` ${__("B")}`;
    if (amount >= 1000000)
        return (amount / 1000000).toFixed(1) + ` ${__("M")}`;
    if (amount >= 1000)
        return (amount / 1000).toFixed(1) + ` ${__("K")}`;
    return Number(amount).toLocaleString();
}

function update_column_summary(column, currency) {
    let items = 0;
    let cost = 0;
    $(column).find(".vi-card").each(function () {
        items += Number(this.dataset.items || 0);
        cost += Number(this.dataset.cost || 0);
    });
    $(column).find(".vi-column-items").text(items);
    $(column).find(".vi-column-cost")
        .text(format_money(cost))
        .attr(
            "title",
            `${Number(cost).toLocaleString()} ${__(currency)}`
        );
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
			const currency = r.message.currency;
			const warehouses = r.message.warehouses || [];
			warehouses.forEach(warehouse => {
				const color = get_column_color(warehouse.name);
				const column = $(`
					<div class="vi-column"
						data-warehouse="${warehouse.name}"
						style="
							--vi-column-color: ${color};
							--vi-column-bg: ${color}1A;
						">

						<div class="vi-column-header">
							<div class="vi-column-title"
								title="${warehouse.warehouse_name}">
								${warehouse.warehouse_name}
							</div>
							<div class="vi-card-summary">
								<div class="vi-card-summary-item">
									${frappe.utils.icon("package", "xs")}
									<span class="vi-column-items">0</span>
								</div>
								<div class="vi-card-summary-item" title="">
									${frappe.utils.icon("circle-dollar-sign", "xs")}
									<span class="vi-column-cost">0</span>
								</div>
							</div>
						</div>
						<div class="vi-column-body"></div>
					</div>
				`);

				const body = column.find(".vi-column-body");
				(warehouse.holders || []).forEach(holder => {
					body.append(`
						<div class="vi-card"
							draggable="true"
							data-holder="${holder.name}"
							data-items="${holder.summary.item_count}"
							data-cost="${holder.summary.total_cost}">

							<div class="vi-card-title">
								<a
									href="/app/vehicle-holder/${holder.name}"
									target="_blank"
									class="vi-holder-link"
									title="${frappe.utils.escape_html(holder.vehicle_holder_title || "")}">
									${frappe.utils.escape_html(holder.vehicle_holder_title || "")}
								</a>
							</div>

							<div class="vi-card-doc">
								${holder.vehicle_holder_doc_nr || ""}
							</div>

							<div class="vi-card-summary">

								<div class="vi-card-summary-item">
									${frappe.utils.icon("package", "xs")}
									<span class="vi-card-summary-value">
										${holder.summary.item_count}
									</span>
								</div>

								<div class="vi-card-summary-item"
									title="${Number(holder.summary.total_cost).toLocaleString()} ${__(currency)}"
									${frappe.utils.icon("circle-dollar-sign", "xs")}
									<span class="vi-card-summary-value">
										${format_money(holder.summary.total_cost)}
									</span>
								</div>
							</div>
						</div>
					`);
				});

				update_column_summary(column, currency);
				board.append(column);
			});

			// Init Tooltips
			board.find("[title]").tooltip({
				delay: {
					show: 600,
					hide: 100
				}
			});

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
				update_column_summary(old_body.parentElement, currency);
				update_column_summary(body.parentElement, currency);
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
						update_column_summary(old_body.parentElement, currency);
						update_column_summary(body.parentElement, currency);
						frappe.msgprint(__("Unable to move!"));
					}
				});
			});
		}
	});
};