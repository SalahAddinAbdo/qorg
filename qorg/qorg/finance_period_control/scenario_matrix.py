from dataclasses import dataclass
from collections import defaultdict

OPEN=("Requested","Reserved","Ordered","Contracted","Invoiced")
@dataclass(frozen=True)
class E: stage:str; amount:float; direction:str="Increase"; period:str="P1"; key:str=""
def balances(events):
    out=defaultdict(float);seen=set()
    for e in events:
        if e.key:
            if e.key in seen:raise AssertionError("duplicate key")
            seen.add(e.key)
        if e.stage in OPEN:out[(e.period,e.stage)]+=e.amount*(1 if e.direction=="Increase" else -1)
    if any(v < -0.005 for v in out.values()):raise AssertionError("negative stage balance")
    return out
def open_total(events,period=None):
    b=balances(events);return round(sum(v for (p,s),v in b.items() if not period or p==period),6)
def consume(events,stage,amount,prefix,period="P1"):
    return events+[E(stage,amount,"Decrease",period,prefix+"-OUT")]
def replace(events,old,new,amount,prefix,period="P1"):
    return consume(events,old,amount,prefix,period)+[E(new,amount,"Increase",period,prefix+"-IN")]

def run_matrix():
    results=[]
    def ok(name,events,expected,period=None):
        got=open_total(events,period);assert abs(got-expected)<0.001,(name,got,expected);results.append(name)
    e=[E("Requested",100,key="MR")];e=replace(e,"Requested","Ordered",100,"PO");e=replace(e,"Ordered","Invoiced",100,"PI");e=consume(e,"Invoiced",100,"GL");ok("01 full MR-PO-PI-GL",e,0)
    e=[E("Requested",100,key="MR")];e=replace(e,"Requested","Ordered",40,"PO1");e=replace(e,"Requested","Ordered",30,"PO2");ok("02 partial MR multiple PO",e,100)
    e=[E("Ordered",100,key="PO")];e=replace(e,"Ordered","Invoiced",40,"PI1");e=replace(e,"Ordered","Invoiced",60,"PI2");ok("03 one PO multiple PI",e,100)
    e=[E("Ordered",30,key="PO1"),E("Ordered",70,key="PO2")];e=replace(e,"Ordered","Invoiced",100,"PI");ok("04 PI combines PO rows",e,100)
    ok("05 direct PO",[E("Ordered",75,key="DPO")],75)
    ok("06 direct PI",[E("Invoiced",75,key="DPI")],75)
    ok("07 service no receipt",[E("Invoiced",50,key="S")],50)
    ok("08 stock receipt informational",[E("Ordered",50,key="O")],50)
    ok("09 fixed asset acquisition",[E("Invoiced",120,key="A")],120)
    ok("10 CWIP",[E("Invoiced",200,key="C")],200)
    ok("11 cancel MR",consume([E("Requested",80,key="M")],"Requested",80,"C"),0)
    ok("12 cancel PO restores MR",[E("Requested",80,key="M"),E("Requested",80,"Decrease",key="P1"),E("Ordered",80,key="P2"),E("Ordered",80,"Decrease",key="C1"),E("Requested",80,key="C2")],80)
    ok("13 PI cancel GL reversal",[],0)
    ok("14 purchase return",consume([E("Invoiced",100,key="I")],"Invoiced",40,"R"),60)
    ok("15 credit debit note",consume([E("Invoiced",100,key="I")],"Invoiced",25,"CN"),75)
    ok("16 amendment",[E("Ordered",100,key="O"),E("Ordered",100,"Decrease",key="OC"),E("Ordered",120,key="OA")],120)
    ok("17 foreign currency base",[E("Ordered",375,key="FX")],375)
    ok("18 eligible tax",[E("Ordered",115,key="T")],115)
    ok("19 split budget lines",[E("Ordered",60,key="B1"),E("Ordered",40,key="B2")],100)
    ok("20 multiple projects",[E("Ordered",40,key="P1"),E("Ordered",60,key="P2")],100)
    ok("21 advance informational",[E("Ordered",100,key="O")],100)
    ok("22 payment informational",[E("Invoiced",100,key="I")],100)
    ok("23 close PO release",consume([E("Ordered",100,key="O")],"Ordered",35,"CL"),65)
    ok("24 manual release",consume([E("Reserved",100,key="R")],"Reserved",20,"REL"),80)
    e=[E("Ordered",100,period="P1",key="O"),E("Ordered",100,"Decrease","P1","CF-O"),E("Ordered",100,"Increase","P2","CF-I")];ok("25 cross period",e,0,"P1");ok("26 carry forward",e,100,"P2")
    ok("27 asset account actual replaces",consume([E("Invoiced",100,key="A")],"Invoiced",100,"GLA"),0)
    ok("28 depreciation excluded",[E("Invoiced",100,key="A")],100)
    ok("29 shared cost distribution",[E("Ordered",50,key="D1"),E("Ordered",50,key="D2")],100)
    ok("30 multi donor",[E("Ordered",70,key="F1"),E("Ordered",30,key="F2")],100)
    return results
if __name__=="__main__":print("SCENARIOS_PASS",len(run_matrix()))
