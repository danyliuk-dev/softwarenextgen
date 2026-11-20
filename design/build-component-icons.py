"""Generate legible, original schematic icons for the component catalog."""
from pathlib import Path
from html import escape
import json
root=Path(__file__).resolve().parents[1]
out=root/'server/wwwroot/images/components';out.mkdir(parents=True,exist_ok=True)
def path(d):return f'<path d="{d}"/>'
def rect(x,y,w,h,r=3,fill='none'):return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}"/>'
def circle(x,y,r,fill='none'):return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}"/>'
def label(x,y,t,size=16):return f'<text x="{x}" y="{y}" stroke="none" fill="#6255bf" font-family="Arial,sans-serif" font-size="{size}" font-weight="700">{escape(t)}</text>'
check=path('m23 32 6 6 13-14')
chevron=path('m40 29 5 5 5-5')
calendar=rect(12,16,40,36,5)+path('M12 27h40M22 12v9M42 12v9')
field=rect(10,20,44,25,5)
grid=rect(11,13,42,39,4)+path('M11 25h42M11 38h42M25 13v39M39 25v27')
page=path('M18 10h20l10 10v34H18zM38 10v12h10')
icons={
'NgButton':rect(10,20,44,26,7,'#e7e2ff')+path('M22 33h20m-5-5 5 5-5 5'),
'NgButtonGroup':rect(7,20,50,26,6)+path('M24 20v26M40 20v26')+circle(16,33,2,'#7866d4')+path('M29 33h6M45 33h6'),
'NgToggleButton':rect(12,16,40,32,6,'#e7e2ff')+check,
'NgChip':rect(8,23,48,22,11,'#eeeaff')+path('M18 34h15m8-4 8 8m0-8-8 8'),
'NgChipList':rect(9,13,28,16,8,'#e7e2ff')+rect(9,36,20,16,8)+rect(35,36,20,16,8)+path('M16 21h13M16 44h6M42 44h6'),
'NgTextBox':field+path('M19 28v10M24 33h16'),
'NgTextArea':rect(10,12,44,40,5)+path('M18 23h27M18 31h27M18 39h16m12 7 3-3'),
'NgNumericTextBox':field+label(17,37,'12',17)+path('M42 20v25m4-17 3-3 3 3m-6 9 3 3 3-3'),
'NgCheckBox':rect(14,14,36,36,6,'#e7e2ff')+check,
'NgSwitch':rect(8,20,48,26,13,'#e7e2ff')+circle(42,33,9,'#7866d4')+path('M18 33h5'),
'NgRadioGroup':circle(16,21,7)+circle(16,21,2,'#7866d4')+circle(16,44,7)+path('M31 21h21M31 44h15'),
'NgAutoComplete':rect(10,9,44,18,4)+path('M18 18h12')+rect(10,32,44,23,4)+path('M18 40h26M18 48h17')+path('m41 12 3 6 7 1-5 4'),
'NgComboBox':rect(10,9,44,19,4)+path('M18 19h12m11-3 4 4 4-4')+rect(10,33,44,22,4,'#eeeaff')+path('M18 41h25M18 48h16'),
'NgDropDownList':field+path('M18 33h14')+chevron,
'NgMultiSelect':rect(9,11,46,44,5)+rect(15,17,16,12,4,'#e7e2ff')+rect(36,17,12,12,4,'#e7e2ff')+path('m16 40 4 4 6-8M32 40h15'),
'NgForm':rect(13,9,38,46,5)+path('M21 19h16M21 28h22M21 37h22')+rect(21,44,14,5,2,'#7866d4'),
'NgCalendar':calendar+rect(20,33,8,8,2,'#7866d4')+path('M36 36h8M22 46h6M36 46h8'),
'NgDateInput':field+label(16,37,'24',17)+path('M40 27v12M46 27v12'),
'NgDatePicker':calendar+path('m25 38 6 6 11-12'),
'NgDateRangePicker':calendar+rect(18,33,28,11,3,'#e7e2ff')+circle(23,38.5,2,'#7866d4')+circle(41,38.5,2,'#7866d4')+path('M29 38.5h6'),
'NgDateTimePicker':calendar+circle(43,44,12,'#f5f3ff')+path('M43 37v8h5'),
'NgTimePicker':circle(32,32,21)+path('M32 18v15l10 6M32 11v3M53 32h-3M32 53v-3M11 32h3'),
'NgScheduler':calendar+path('M26 27v25M39 27v25')+rect(16,32,6,13,2,'#7866d4')+rect(30,37,5,10,2,'#b2a2eb')+rect(43,31,5,7,2,'#7866d4'),
'NgDataGrid':grid,
'NgPivotGrid':grid+path('M17 19h14m-5-4 5 4-5 4')+rect(29,41,20,7,2,'#d4c9f8'),
'NgTreeList':rect(10,11,44,43,4)+path('M10 23h44M19 30v17h8M19 34h8M34 33h12M34 46h12'),
'NgSpreadsheet':grid+label(16,23,'fx',11)+rect(27,28,10,8,1,'#d4c9f8'),
'NgEditor':page+path('M25 31h15M25 38h15M25 45h9')+path('m43 44 8-8 4 4-8 8-6 2z'),
'NgPdfViewer':page+rect(10,29,44,18,3,'#eeeaff')+label(17,42,'PDF',14),
'NgPager':rect(7,22,14,22,4)+rect(25,22,14,22,4,'#e7e2ff')+rect(43,22,14,22,4)+path('m16 28-5 5 5 5m32-10 5 5-5 5')+label(29,38,'1',14),
'NgChart':path('M11 12v41h44')+rect(18,34,7,12,1,'#b2a2eb')+rect(31,25,7,21,1,'#9280db')+rect(44,14,7,32,1,'#7866d4'),
'NgArcGauge':path('M11 45a23 23 0 0 1 46 0M17 45a17 17 0 0 1 34 0M34 43l12-18')+circle(34,43,3,'#7866d4'),
'NgLinearGauge':rect(8,24,48,16,5)+rect(12,28,27,8,2,'#b2a2eb')+path('M43 18v28M14 47v4M26 47v4M38 47v4M50 47v4'),
'NgDiagram':rect(22,8,20,13,3,'#e7e2ff')+rect(5,42,21,14,3)+rect(38,42,21,14,3)+path('M32 21v11H15v10M32 32h17v10'),
'NgMap':path('m8 17 16-7 16 7 16-7v37l-16 7-16-7-16 7zM24 10v37M40 17v37')+path('M42 26c0 8-9 15-9 15s-9-7-9-15a9 9 0 1 1 18 0Z')+circle(33,26,3),
'NgBreadcrumb':path('M9 27h11v12H9zM27 26l6 7-6 7M41 27h14M41 38h10'),
'NgMenu':rect(11,10,42,44,5)+path('M20 22h25M20 32h25M20 42h17'),
'NgDrawer':rect(8,12,48,40,5)+rect(8,12,18,40,5,'#e7e2ff')+path('M14 23h6M14 31h6M14 39h6m17-10 5 4-5 4'),
'NgTabs':rect(9,24,46,29,4)+path('M10 24V12h17v12M29 15h11v9M44 15h10v9M18 35h25M18 43h16'),
'NgTreeView':rect(10,10,15,12,3,'#e7e2ff')+rect(34,29,20,11,3)+rect(34,47,20,10,3)+path('M17 22v30h17M17 34h17'),
'NgStepper':path('M19 32h8M38 32h8')+circle(12,32,7,'#e7e2ff')+circle(32,32,7,'#e7e2ff')+circle(52,32,7)+path('m9 32 2 2 4-4M30 32h4'),
'NgWizard':rect(10,10,44,44,5)+path('M10 24h44M18 18h6M29 18h6M40 18h6M18 33h18M18 41h12m11-5 6 5-6 5'),
'NgDialog':rect(8,12,48,40,6)+path('M8 25h48M17 19h12m16-3 6 6m0-6-6 6M17 34h21')+rect(35,41,13,6,2,'#e7e2ff'),
'NgNotification':path('M17 42h30l-5-7V25a10 10 0 0 0-20 0v10zM27 48a5 5 0 0 0 10 0M32 11v4')+circle(47,17,5,'#b2a2eb'),
'NgTooltip':path('M10 12h44v25H34l-9 8v-8H10z')+path('M18 22h27M18 29h16')+circle(42,51,4,'#e7e2ff'),
'NgAIPrompt':path('M10 14h44v32H30l-10 8v-8H10zM33 20l3 7 7 3-7 3-3 7-3-7-7-3 7-3z'),
'NgPromptBox':rect(9,16,46,33,6)+path('m17 26 6 6-6 6M29 38h10m5-14 7 8-7 8'),
}
docs=json.loads((root/'server/manuals/components/index.json').read_text())
expected={d['Path'].split('/')[-1] for d in docs if d['Path'].startswith('manual/Ng')}
assert set(icons)==expected,(expected-set(icons),set(icons)-expected)
for name,body in icons.items():
 svg=f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><title>{escape(name)} schematic icon</title><g fill="none" stroke="#6255bf" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">{body}</g></svg>'
 (out/(name+'.svg')).write_text(svg)
print(f'Generated {len(icons)} component icons')
