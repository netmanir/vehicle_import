app_name = "vehicle_import"
app_title = "Vehicle Import"
app_publisher = "ACP"
app_description = "Vehicle Import Cost Management"
app_email = "netman@mail.ir"
app_license = "mit"

app_include_js = [
    "/assets/vehicle_import/js/cost_entry_dialog.js",
    "/assets/vehicle_import/js/explorers/vehicle_holder_explorer.js",
]

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "vehicle_import",
# 		"logo": "/assets/vehicle_import/logo.png",
# 		"title": "Vehicle Import",
# 		"route": "/vehicle_import",
# 		"has_permission": "vehicle_import.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/vehicle_import/css/vehicle_import.css"
# app_include_js = "/assets/vehicle_import/js/vehicle_import.js"

# include js, css files in header of web template
# web_include_css = "/assets/vehicle_import/css/vehicle_import.css"
# web_include_js = "/assets/vehicle_import/js/vehicle_import.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "vehicle_import/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "vehicle_import/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "vehicle_import.utils.jinja_methods",
# 	"filters": "vehicle_import.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "vehicle_import.install.before_install"
# after_install = "vehicle_import.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "vehicle_import.uninstall.before_uninstall"
# after_uninstall = "vehicle_import.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "vehicle_import.utils.before_app_install"
# after_app_install = "vehicle_import.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "vehicle_import.utils.before_app_uninstall"
# after_app_uninstall = "vehicle_import.utils.after_app_uninstall"

# Build
# ------------------
# To hook into the build process

# after_build = "vehicle_import.build.after_build"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "vehicle_import.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"vehicle_import.tasks.all"
# 	],
# 	"daily": [
# 		"vehicle_import.tasks.daily"
# 	],
# 	"hourly": [
# 		"vehicle_import.tasks.hourly"
# 	],
# 	"weekly": [
# 		"vehicle_import.tasks.weekly"
# 	],
# 	"monthly": [
# 		"vehicle_import.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "vehicle_import.install.before_tests"

# Extend DocType Class
# ------------------------------
#
# Specify custom mixins to extend the standard doctype controller.
# extend_doctype_class = {
# 	"Task": "vehicle_import.custom.task.CustomTaskMixin"
# }

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "vehicle_import.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "vehicle_import.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["vehicle_import.utils.before_request"]
# after_request = ["vehicle_import.utils.after_request"]

# Job Events
# ----------
# before_job = ["vehicle_import.utils.before_job"]
# after_job = ["vehicle_import.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"vehicle_import.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []

