from pathlib import Path
from html import escape
out=Path(__file__).resolve().parents[1]/'server/wwwroot/images'
def rect(x,y,w,h,fill='#fff',r=14):return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}"/>'
def text(x,y,t,size=18,fill='#192441',weight=500):return f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" font-weight="{weight}">{escape(t)}</text>'
def base(title):return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 760" role="img"><title>'+title+'</title><defs><linearGradient id="bg" x2="1" y2="1"><stop stop-color="#e5eaff"/><stop offset="1" stop-color="#f5f0ff"/></linearGradient><filter id="shadow" x="-25%" y="-25%" width="150%" height="160%"><feDropShadow dy="14" stdDeviation="18" flood-color="#243575" flood-opacity=".12"/></filter></defs><g font-family="Inter,Arial,sans-serif">'+rect(0,0,960,760,'url(#bg)',0)+'<circle cx="890" cy="70" r="180" fill="#d6d5ff" opacity=".55"/>'+text(52,58,'NEXTGEN / PRODUCT COLLECTION',14,'#5865a5',700)
def card(x,y,w,h):return '<g filter="url(#shadow)">'+rect(x,y,w,h)+'</g>'
s=base('NextgenComponents interface collection')+text(52,111,'Small details. Endless possibilities.',32,weight=650)
s+=card(52,148,530,280)+text(78,185,'Workspace overview',19,weight=650)+rect(454,166,100,27,'#eef0ff',7)+text(471,185,'This month',12,'#5a5f96')
s+=rect(76,209,482,35,'#f3f5fb',6)
for x,t in [(90,'PROJECT'),(298,'STATUS'),(451,'PROGRESS')]:s+=text(x,231,t,11,'#78809a',700)
for i,(name,status,progress) in enumerate([('Product design','In progress',105),('Customer portal','Review',75),('Analytics workspace','Complete',120)]):
 y=273+i*51;s+=rect(89,y-15,24,24,['#e8e5ff','#e0edff','#e9e6fb'][i],7)+text(124,y+2,name,13)+rect(294,y-17,100,25,'#eeefff',12)+text(306,y,status,11,'#5c56c6')+rect(432,y-7,120,6,'#edf0f8',3)+rect(432,y-7,progress,6,'#7875ef',3)
s+=card(606,148,302,280)+text(631,186,'Audience growth',18,weight=650)+text(631,227,'24,680',32,weight=650)+text(793,225,'+18.4%',13,'#635bce')
for i,h in enumerate([40,65,52,90,75,115,105,145]):s+=rect(633+i*32,394-h,18,h,'#a8a6f6' if i<7 else '#5f5bde',5)
s+=card(52,453,287,247)+text(77,490,'Make it yours',18,weight=650)+text(77,526,'Workspace name',12,'#7a8298')+rect(76,541,239,40,'#f4f6fb',8)+text(89,567,'Design studio',14)+rect(77,603,42,23,'#6963e2',12)+'<circle cx="107" cy="614" r="8" fill="white"/>'+text(131,620,'Notifications enabled',12)+rect(76,646,147,34,'#625de0',8)+text(95,668,'Save changes',13,'#fff',600)
s+=card(363,453,272,247)+text(389,490,'Navigation & flow',18,weight=650)+text(389,527,'Workspace  /  Projects',12,'#747e98')+rect(387,548,222,37,'#f0efff',8)+text(402,572,'Overview     Files     Team',12,'#655ed3')
for i,t in enumerate(['Design','Develop','Deliver']):
 x=404+i*85;s+='<circle cx="'+str(x)+'" cy="622" r="14" fill="'+('#6e67e5' if i<2 else '#e8e8f6')+'"/>'+text(x-4,627,str(i+1),12,'#fff' if i<2 else '#777d98')+text(x-18,660,t,11,'#68728b')
s+=card(659,453,249,247)+text(684,490,'At a glance',18,weight=650)+'<circle cx="782" cy="578" r="56" fill="none" stroke="#ececfa" stroke-width="15"/><circle cx="782" cy="578" r="56" fill="none" stroke="#8278e9" stroke-width="15" stroke-dasharray="263 352" transform="rotate(-90 782 578)" stroke-linecap="round"/>'+text(747,587,'75%',28,weight=650)+text(710,674,'Clear. Consistent. Connected.',11,'#7a8298')
(out/'components-overview.svg').write_text(s+'</g></svg>')
s=base('NextgenReportEngine report illustration')+text(52,111,'Your data. A clearer perspective.',32,weight=650)
s+='<g transform="rotate(-6 480 440)">'+card(236,175,535,520)+'</g>'+card(173,149,607,562)
s+=rect(173,149,607,10,'#6963df',0)+text(210,199,'NORTHSTAR',13,'#6963df',750)+text(210,239,'Quarterly performance',27,weight=650)+text(210,264,'BUSINESS OVERVIEW   /   Q3 2026',11,'#7e879b',600)+text(682,201,'REPORT 01',10,'#7e879b')
for x,label,value in [(210,'REVENUE','$248,600'),(392,'ORDERS','1,842'),(574,'GROWTH','+18.4%')]:
 s+=rect(x,286,162,75,'#f3f4fc',9)+text(x+14,310,label,10,'#7d83a3',650)+text(x+14,342,value,23,'#263556',650)
s+=text(210,397,'Revenue by month',14,weight=650)
for y in [423,455,487]:s+=f'<path d="M210 {y} H735" stroke="#eceff7"/>'
s+='<path d="M210 495 L285 471 L360 478 L435 449 L510 460 L585 423 L660 434 L735 405 L735 510 L210 510Z" fill="#eeecff"/><path d="M210 495 L285 471 L360 478 L435 449 L510 460 L585 423 L660 434 L735 405" stroke="#7c70e4" stroke-width="4" stroke-linejoin="round" fill="none"/>'
for x,t in [(210,'APR'),(310,'MAY'),(410,'JUN'),(510,'JUL'),(610,'AUG'),(710,'SEP')]:s+=text(x,529,t,9,'#8a90a7')
s+=rect(210,551,526,28,'#f3f4fa',4)+text(223,569,'BUSINESS UNIT',10,'#777e98',650)+text(520,569,'REVENUE',10,'#777e98',650)+text(661,569,'CHANGE',10,'#777e98',650)
for i,(a,b,c) in enumerate([('Digital products','$142,400','+21.6%'),('Professional services','$106,200','+14.3%')]):
 y=602+i*30;s+=text(223,y,a,12)+text(520,y,b,12)+text(661,y,c,12,'#7065d4')
s+=text(210,682,'Confidential · Demonstration data',9,'#9299ab')+text(693,682,'01 / 03',9,'#9299ab')
s+=card(55,393,158,87)+text(74,426,'READY TO SHARE',10,'#7b829c',650)+text(74,457,'PDF export ↗',17,'#5d58c6',650)+card(729,566,177,80)+text(749,597,'DESIGNED FOR CLARITY',9,'#7b829c',650)+text(749,625,'Every detail counts.',13,'#3d4964',600)
(out/'reports-overview.svg').write_text(s+'</g></svg>')
