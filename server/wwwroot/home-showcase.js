const showcases=[...document.querySelectorAll('[data-home-showcase]')];
for(const showcase of showcases){
 const image=showcase.querySelector('[data-showcase-image]'),screen=showcase.querySelector('[data-showcase-screen]'),play=showcase.querySelector('[data-showcase-play]'),open=showcase.querySelector('[data-showcase-open]'),guide=showcase.querySelector('[data-showcase-guide]'),status=showcase.querySelector('[data-showcase-status]'),mode=showcase.querySelector('[data-showcase-mode]');
 let timer;
 function close(){clearTimeout(timer);screen.querySelector('iframe')?.remove();image.hidden=false;play.innerHTML='Try live demo <span aria-hidden="true">↗</span>';play.setAttribute('aria-expanded','false');mode.textContent='PRODUCT PREVIEW';status.textContent='';}
 showcase.closeDemo=close;
 const select=showcase.querySelector('[data-showcase-select]'),options=[...select.options].map(o=>o.cloneNode(true)),choices=[...showcase.querySelectorAll('[data-showcase-category]')],remembered=new Map();
 function choose(){
  close();const option=select.selectedOptions[0];remembered.set(option.dataset.category,option.value);
  image.src=option.dataset.image;image.alt=showcase.querySelector('.showcase-product').textContent+': '+option.textContent+' working example';open.href=option.dataset.demo;guide.href=option.dataset.guide;showcase.querySelector('[data-showcase-description]').textContent=option.dataset.description;
 }
 function category(button){
  for(const b of choices)b.setAttribute('aria-pressed',String(b===button));
  const group=button.dataset.showcaseCategory;select.replaceChildren(...options.filter(o=>o.dataset.category===group).map(o=>o.cloneNode(true)));
  if(remembered.has(group))select.value=remembered.get(group);
  showcase.querySelector('[data-showcase-count]').textContent=select.options.length+(showcase.classList.contains('showcase-components')?' components':' examples');choose();
 }
 for(const button of choices)button.addEventListener('click',()=>category(button));
 select.addEventListener('change',choose);category(choices.find(b=>b.getAttribute('aria-pressed')==='true'));
 play.addEventListener('click',()=>{
  if(screen.querySelector('iframe')){close();return;}
  for(const other of showcases)other.closeDemo();
  const frame=document.createElement('iframe');frame.title=showcase.querySelector('.showcase-product').textContent+' — '+select.selectedOptions[0].textContent+' live demo';frame.src=open.getAttribute('href');frame.referrerPolicy='same-origin';
  status.textContent='Loading the live example…';frame.addEventListener('load',()=>{clearTimeout(timer);status.textContent='Live example ready. Use its controls or open it in a full window.';},{once:true});
  image.hidden=true;screen.append(frame);play.textContent='Close live demo';play.setAttribute('aria-expanded','true');mode.textContent='LIVE EXAMPLE';
  timer=setTimeout(()=>{status.textContent='Taking longer to load. You can also use Open demo to open the example in a full window.';},15000);
 });
}
