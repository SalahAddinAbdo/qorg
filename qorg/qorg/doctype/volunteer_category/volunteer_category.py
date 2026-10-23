from frappe.utils.nestedset import NestedSet


class VolunteerCategory(NestedSet):
    nsm_parent_field = "parent_volunteer_category"
