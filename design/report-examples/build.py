"""Generate bounded, real-engine sample inputs, outputs and downloadable artifacts."""
from pathlib import Path
import json,requests,zipfile,io,copy,base64,sqlite3
root=Path(__file__).resolve().parents[2];src=root/'artifacts/report-source/samples';out=root/'server/wwwroot/report-examples';out.mkdir(parents=True,exist_ok=True)
api='http://127.0.0.1:5355';manifest={'samples':{},'topics':{}}
def post(route,data):
 r=requests.post(api+route,json=data,timeout=120)
 if not r.ok:raise RuntimeError(route+' '+r.text[:1200])
 return r

def save(path,value):
 p=out/path;p.parent.mkdir(parents=True,exist_ok=True)
 if isinstance(value,bytes):p.write_bytes(value)
 else:p.write_text(json.dumps(value,indent=2,ensure_ascii=False))
 return str(path)
def load(name,ext):return json.loads((src/(name+ext)).read_text())
def sample(key,label,template,data,parameters=None):
 body={'template':template,'data':data,'parameters':parameters or {},'useSnapshot':True}
 doc=post('/api/preview',body).json();directory=Path('samples')/key
 record={'label':label,'pages':len(doc['pages']),'request':save(directory/'request.json',body),'response':save(directory/'response.json',doc),'project':save(directory/'sample.nrproject.json',{'kind':'nextgen-report-project','version':1,**{k:v for k,v in body.items() if k!='useSnapshot'}}),'pdf':save(directory/'report.pdf',post('/api/render',body).content),'html':save(directory/'report.html',post('/api/export/html',body).content),'images':[],'exports':{}}
 images=post('/api/export/images',{**body,'options':{'format':'png','dpi':96,'archive':True}})
 with zipfile.ZipFile(io.BytesIO(images.content)) as z:
  for i,n in enumerate(sorted(z.namelist())):record['images'].append(save(directory/f'page-{i+1}.png',z.read(n)))
 manifest['samples'][key]=record
 print(key,record['pages'],'pages',flush=True)
 return body,record
sales=sample('sales','Sales summary',load('sales','.nrtemplate'),load('sales','.data.json'),load('sales','.parameters.json'))
charts=sample('charts','Charts and visualizations',load('chart-series','.nrtemplate'),load('chart-series','.data.json'))
# Real exporter outputs for every supported selection in the Office/image demonstrations.
for key,(body,record) in [('sales',sales),('charts',charts)]:
 for first in range(1,record['pages']+1):
  for last in range(first,record['pages']+1):
   for fmt in ['xlsx','docx']:
    for mode in ['editable','pages']:
     name=f'{fmt}-{mode}-{first}-{last}';record['exports'][name]=save(Path('samples')/key/(name+'.'+fmt),post('/api/export/office',{**body,'options':{'format':fmt,'mode':mode,'firstPage':first,'lastPage':last,'dpi':150}}).content)
   for fmt in ['png','svg']:
    for dpi in ([96,150,300] if fmt=='png' else [96]):
     name=f'{fmt}-{dpi}-{first}-{last}';record['exports'][name]=save(Path('samples')/key/(name+'.zip'),post('/api/export/images',{**body,'options':{'format':fmt,'dpi':dpi,'firstPage':first,'lastPage':last,'archive':True}}).content)
# Parameter/dialog controls: every combination has been rendered by the real engine.
items=[{'item':'Monitor','region':'East','quantity':8,'price':240},{'item':'Desk','region':'West','quantity':2,'price':450},{'item':'Chair','region':'East','quantity':12,'price':120}]
base={'version':1,'title':'Regional inventory','parameters':{'region':{'type':'string','default':'East'},'minimum':{'type':'number','default':0}},'blocks':[{'type':'text','text':'{{parameters.region}} · Inventory','style':{'size':22,'bold':True}},{'type':'text','text':'Minimum quantity: {{parameters.minimum}}'},{'type':'table','source':'items','filters':[{'field':'region','operator':'eq','parameter':'region'},{'field':'quantity','operator':'gte','parameter':'minimum'}],'columns':[{'title':'Item','field':'item'},{'title':'Region','field':'region'},{'title':'Qty','field':'quantity'},{'title':'Value','expression':'row.quantity * row.price','format':'N2'}]}]}
for region in ['East','West']:
 for minimum in [0,5,10]:sample(f'parameters-{region.lower()}-{minimum}',f'{region} · minimum {minimum}',base,{'items':items},{'region':region,'minimum':minimum})
# CSV/TSV/XLSX import uses the engine parsers, not a visual-only table.
rows='Item,Region,Quantity,Price\nMonitor,East,8,240\nDesk,West,2,450\nChair,East,12,120\n'
imports={}
for kind,text,delimiter in [('csv',rows,','),('tsv',rows.replace(',','\t'),'\t')]:
 result=post('/api/data/import',{'text':text,'delimiter':delimiter,'typing':'infer'}).json();imports[kind]={'input':save(Path('inputs')/('inventory.'+kind),text.encode()),'result':save(Path('inputs')/(kind+'-result.json'),result)}
# Write a small valid workbook fixture, then import it through the engine.
from xml.sax.saxutils import escape
buf=io.BytesIO()
with zipfile.ZipFile(buf,'w',zipfile.ZIP_DEFLATED) as z:
 z.writestr('[Content_Types].xml','<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>')
 z.writestr('_rels/.rels','<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>')
 z.writestr('xl/workbook.xml','<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Inventory" sheetId="1" r:id="rId1"/></sheets></workbook>')
 z.writestr('xl/_rels/workbook.xml.rels','<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>')
 body=''
 for i,line in enumerate(rows.strip().splitlines(),1):
  cells=''.join(f'<c r="{chr(65+j)}{i}" t="inlineStr"><is><t>{escape(value)}</t></is></c>' for j,value in enumerate(line.split(',')))
  body+=f'<row r="{i}">{cells}</row>'
 z.writestr('xl/worksheets/sheet1.xml','<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>'+body+'</sheetData></worksheet>')
xlsx=buf.getvalue();imports['xlsx']={'input':save(Path('inputs')/'inventory.xlsx',xlsx),'result':save(Path('inputs')/'xlsx-result.json',post('/api/data/xlsx',{'contentBase64':base64.b64encode(xlsx).decode(),'sheet':'Inventory','typing':'infer'}).json())};manifest['imports']=imports
import_template={'version':1,'title':'Imported inventory','blocks':[{'type':'text','text':'Imported inventory','style':{'size':22,'bold':True}},{'type':'table','source':'items','columns':[{'title':col['header'],'field':col['field']} for col in result['columns']]}]}
sample('imported','Imported inventory',import_template,{'items':result['rows']})
# Derived tables and TypeScript event results.
for minimum in [10,60,100]:
 body,record=sample('prepared-'+str(minimum),'Regional revenue · minimum '+str(minimum),load('data-preparation','.nrtemplate'),load('data-preparation','.data.json'),{'minimum':minimum})
 record['prepared']=save(Path('samples')/('prepared-'+str(minimum))/'prepared.json',post('/api/data/prepare',body).json())
for minimum in [0,5,10]:sample('logic-'+str(minimum),'Inventory script · minimum '+str(minimum),load('inventory','.nrtemplate'),load('inventory','.data.json'),{'minimumQuantity':minimum})
logic=sales[0].copy();logic.update(template=load('inventory','.nrtemplate'),data=load('inventory','.data.json'),parameters={'minimumQuantity':-1})
r=requests.post(api+'/api/preview',json=logic);assert r.status_code==400;manifest['logicError']=save(Path('inputs')/'logic-validation.json',r.json())
# Drill-down carries the selected row into the actual nested report template.
template=load('drill-down','.nrtemplate');data=load('drill-down','.data.json');data['orders']=data['orders'][:3]
sample('orders','Order summary',template,data,{'company':'Northstar Demo'})
manifest['orders']=[]
for row in data['orders']:
 key='order-'+row['id'].lower();sample(key,row['id']+' · '+row['customer'],template['blocks'][1]['drillDown']['template'],{'row':row,'source':data},{'company':'Northstar Demo'});manifest['orders'].append({**row,'sample':key})
# HTTP snapshots are explicit included fixtures, with independent render outputs.
for revision in [1,2]:
 data=load('data-preparation','.data.json');data['items'][0]['quantity']*=revision
 sample('http-'+str(revision),'HTTP snapshot '+str(revision),load('data-preparation','.nrtemplate'),data,{'minimum':10})
 save(Path('inputs')/f'http-snapshot-{revision}.json',{'revision':revision,'payload':{'rows':data['items']}})
# Real SQLite fixture + query result for the SQL source example.
db=out/'inputs/inventory.sqlite.bin';db.unlink(missing_ok=True);conn=sqlite3.connect(db);conn.execute('create table inventory(item text,region text,quantity integer,price real)');conn.executemany('insert into inventory values(:item,:region,:quantity,:price)',items);conn.commit();conn.row_factory=sqlite3.Row;sqlrows=[dict(r) for r in conn.execute('select * from inventory order by item')];conn.close()
save(Path('inputs')/'sql-result.json',sqlrows);save(Path('inputs')/'inventory.json',{'items':items})
# Valid/invalid template diagnostics from the engine.
for name,t in [('valid',base),('invalid',{**base,'blocks':[{'type':'unknown-control'}]})]:
 save(Path('inputs')/(name+'-template.json'),t);save(Path('inputs')/(name+'-diagnostics.json'),post('/api/template/check',{'template':t,'data':{'items':items}}).json())
# Every manual has a deliberate, topic-specific demonstration contract.
topics={
'overview':('viewer','Create, preview and export a report','Choose a sample, turn its pages and download the generated report.','sales'),
'index':('tour','Choose a reporting workflow','Open a working example for the task you want to explore.','sales'),
'agent-authoring':('agent','From a template to a portable project','Inspect an actual template, inspect the engine result, and download a project to open in Studio.','parameters-east-0'),
'data-import':('import','Import CSV, TSV or Excel','Import the included inventory fixture and inspect the typed rows returned by the engine.','imported'),
'data-preparation':('prepare','Filter, calculate and group data','Choose a minimum amount and inspect input rows, derived tables and the generated regional report.','prepared-10'),
'data-sources':('sources','JSON, SQLite and object data','Inspect the same inventory dataset in three source forms, including a runnable SQLite database.','imported'),
'desktop':('desktop','Open a report in desktop Studio','Choose your platform and download the example project for the installed application.','sales'),
'developer-guide':('api','Request → engine response → report','Inspect the actual request and response for a report; download the portable project and output.','sales'),
'dotnet-integration':('dotnet','A paginated .NET / Blazor report','Inspect the .NET request contract and use the viewer controls with a generated document.','sales'),
'drill-down':('drill','Open an order detail report','Choose an order to render its actual nested detail report, then return to the summary.','orders'),
'flutter-integration':('flutter','A report for the Flutter client','Inspect the request/response contract and preview the same document consumed by the Flutter SDK.','charts'),
'http-connections':('http','Refresh a JSON source snapshot','Compare the two included HTTP-response fixtures and their independently rendered reports.','http-1'),
'image-export':('images','Export report pages as PNG or SVG','Choose format, page range and PNG resolution, then download the engine-generated image archive.','sales'),
'office-export':('office','Export to Excel and Word','Choose format, editable text or page images, and an inclusive page range. Download is a real Office document.','sales'),
'report-authoring-manual':('parameters','Generate a report from parameters','Change the region and minimum quantity. Each combination has a matching engine-generated report and project.','parameters-east-0'),
'report-library':('library','Save and restore report versions','Keep sample project versions in this browser, restore one and download its matching project.','sales'),
'report-logic-manual':('logic','Run report lifecycle examples','Choose a minimum quantity to inspect actual TypeScript results, or trigger the validation-error example.','logic-0'),
'template-format':('template','Inspect and validate a template','Compare a valid template with an invalid block type and inspect diagnostics returned by the engine.','parameters-east-0'),
'toolbox':('toolbox','A parameter dialog in action','Use the region selector and quantity control to generate the matching report.','parameters-east-0'),
'installation':('installation','Install and open your first project','Choose Linux, macOS or Windows, follow the launch steps, and open the included example project.','sales')}
for key,(mode,title,description,samp) in topics.items():manifest['topics'][key]={'mode':mode,'title':title,'description':description,'sample':samp}
expected={d['Path'] for d in json.loads((root/'server/manuals/reports/index.json').read_text())};assert set(topics)==expected
save('manifest.json',manifest)
print('DONE',len(topics),'topics',len(manifest['samples']),'real-engine samples',flush=True)
