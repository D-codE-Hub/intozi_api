# Copyright (c) 2024, D-codE and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import cint
import base64


@frappe.whitelist()
def add_checkin(
	employee_field_value,
	timestamp,
	device_id=None,
	log_type=None,
	skip_auto_attendance=0,
	employee_fieldname="attendance_device_id",
):
	if not employee_field_value or not timestamp:
		frappe.throw(_("'employee_field_value' and 'timestamp' are required."))

	employee = frappe.db.get_values(
		"Employee",
		{employee_fieldname: employee_field_value},
		["name", "employee_name", employee_fieldname],
		as_dict=True,
	)
	if employee:
		employee = employee[0]
	else:
		frappe.throw(
			_("No Employee found for the given employee field value. '{}': {}").format(
				employee_fieldname, employee_field_value
			)
		)

	doc = frappe.new_doc("Employee Checkin")
	doc.employee = employee.name
	doc.employee_name = employee.employee_name
	doc.time = timestamp
	doc.device_id = device_id
	doc.log_type = log_type
	if cint(skip_auto_attendance) == 1:
		doc.skip_auto_attendance = "1"
	doc.insert()

	return doc



# login up using email id and password
@frappe.whitelist( allow_guest=True )
def login(username, password):
	try:
		login_manager = frappe.auth.LoginManager()
		login_manager.authenticate(user=username, pwd=password)
		login_manager.post_login()
	except frappe.exceptions.AuthenticationError:
		frappe.clear_messages()
		frappe.local.response["status_code"] =401
		frappe.local.response["message"] ="Invalid username/password"
		return

	api_generate = generate_keys(frappe.session.user)
	user = frappe.get_doc('User', frappe.session.user)
	token = base64.b64encode(('{}:{}'.format(user.api_key, api_generate)).encode('utf-8')).decode('utf-8')
	frappe.local.response["status_code"] =200
	frappe.local.response["data"] ={
			"session":frappe.session.user,
			"auth_key": token,
			"full_name":user.full_name,
			"mobile_no":user.mobile_no,
			"email":user.email,
			"username":username
		}

def generate_keys(user):
	user_details = frappe.get_doc('User', user)
	api_secret = frappe.generate_hash(length=15)
	if not user_details.api_key:
		api_key = frappe.generate_hash(length=15)
		user_details.api_key = api_key
	user_details.api_secret = api_secret
	user_details.flags.ignore_permissions = True
	user_details.flags.ignore_password_policy = True
	user_details.save()
	return api_secret
