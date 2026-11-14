import frappe
from frappe.model.document import Document
from frappe.utils import flt
class ParticipationEvaluation(Document):
    def validate(self):
        values=[flt(self.performance_rating),flt(self.attendance_rating),flt(self.learning_rating)]
        self.overall_rating=flt(sum(values)/len(values),2)
    def on_update(self):
        if self.status=="Completed":
            field="latest_midterm_evaluation" if self.evaluation_type=="Midterm" else "latest_final_evaluation"
            frappe.db.set_value("Participation Engagement",self.engagement,field,self.name,update_modified=False)
