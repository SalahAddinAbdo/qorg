from __future__ import annotations
def get_data(data=None):
 data=data or {};data["fieldname"]="funding_agreement";data.setdefault("transactions",[])
 data["transactions"].extend([
  {"label":"Budget and Change Control","items":["Budget Line","Project Change Request","Budget Transfer Audit"]},
  {"label":"Project Context","items":["Project"]},
 ])
 data["non_standard_fieldnames"]={"Project":"name"}
 return data
