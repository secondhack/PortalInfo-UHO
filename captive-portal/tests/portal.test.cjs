const {test}=require('node:test');
const assert=require('node:assert/strict');
const {readFileSync}=require('node:fs');
const {createRequire}=require('node:module');
const path=require('node:path');
const {JSDOM}=createRequire(path.resolve('frontend/package.json'))('jsdom');
const html=readFileSync('captive-portal/dist/index.html','utf8');
const source=readFileSync('captive-portal/src/portal.js','utf8');
const kinds=['news','event','notice','service','survey','generic'];
const slugs=['noticias','eventos','avisos','servicios','encuestas','becas'];
const categories=slugs.map((slug,i)=>({id:i+1,slug,name:slug,content_type:kinds[i],contents:[]}));
function content(i){return {id:i+1,type:kinds[i],title:'Título '+slugs[i],description:'Descripción real de '+slugs[i],starts_at:'2026-11-14T12:00:00Z',version:1,details:{area_name:'Área DEMO',event_at:i===1?'2026-11-15T12:00:00Z':null,access_url:i===3?'https://example.invalid/servicio':null,questions:i===4?[
  {id:11,text:'Una opción',kind:'single',required:true,options:[{id:21,text:'A'},{id:22,text:'B'}]},
  {id:12,text:'Varias opciones',kind:'multiple',required:true,options:[{id:23,text:'C'},{id:24,text:'D'}]},
  {id:13,text:'Comentario',kind:'open',required:true,options:[]}
]:[]},extra_fields:i===5?{Responsable:'Biblioteca'}:{}};}
const pause=()=>new Promise(resolve=>setImmediate(resolve));
async function settle(){for(let i=0;i<8;i++)await pause();}
function response(body,status=200){return {ok:status>=200&&status<300,status,text:async()=>JSON.stringify(body)};}
async function setup(overrides={}){
  const dom=new JSDOM(html.replace(/<script>[\s\S]*?<\/script>/,''),{url:'http://127.0.0.1:8010/portal/',runScripts:'outside-only'});
  const w=dom.window,calls=[];
  if(overrides.prepare)overrides.prepare(w);
  w.AbortController=global.AbortController;
  w.fetch=async(url,opts)=>{
    calls.push({url,method:opts.method,data:opts.body?JSON.parse(opts.body):null,headers:opts.headers});
    if(overrides.handle){const result=await overrides.handle(url,opts,calls);if(result)return result;}
    if(url==='/portal-auth/session')return response(opts.method==='GET'?{authenticated:false,csrfToken:'test-token',mode:'demo'}:{authenticated:true,csrfToken:'new-token',identity:{full_name:'Estudiante DEMO',user_type:'estudiantes'}});
    if(url==='/portal-auth/logout')return response({authenticated:false});
    if(url==='/api/config')return response({sections:categories,survey:{max_options:2,vote_requires_auth:false}});
    if(url.startsWith('/api/categorias'))return response(categories);
    if(url==='/api/vistas')return response({detail:'Vista registrada'},201);
    if(/respuestas$/.test(url))return response({detail:'Respuesta registrada.'},201);
    const i=slugs.indexOf(url.replace('/api/',''));return i<0?response({},404):response([content(i)]);
  };
  w.eval(source);await settle();
  return {dom,w,doc:w.document,calls,close:()=>w.close()};
}
function click(ctx,selector){const target=ctx.doc.querySelector(selector);assert.ok(target,selector);target.click();}
function submit(ctx,selector){ctx.doc.querySelector(selector).dispatchEvent(new ctx.w.Event('submit',{bubbles:true,cancelable:true}));}
function fillSurvey(ctx){ctx.doc.querySelector('[value="21"]').checked=true;ctx.doc.querySelector('[value="23"]').checked=true;ctx.doc.querySelector('[value="24"]').checked=true;ctx.doc.querySelector('textarea').value='Respuesta de prueba';}
test('HTML autónomo, tamaño sin gzip y formulario estático disponible',()=>{
  assert.ok(Buffer.byteLength(html)<=204800);
  for(const pattern of [/<script[^>]+src=/i,/<link[^>]+href=/i,/@import/i,/<img|<video|<iframe/i,/localStorage|sessionStorage/])assert.doesNotMatch(html,pattern);
  assert.match(html,/id="login-form"/);assert.match(html,/for="username"/);assert.match(html,/for="password"/);
});
test('descubre seis categorías, navega y renderiza contratos reales',async()=>{
  const ctx=await setup();try{
    assert.equal(ctx.doc.querySelectorAll('[data-section]').length,6);
    for(const slug of slugs){click(ctx,`[data-section="${slug}"]`);await settle();assert.match(ctx.doc.querySelector('#content').textContent,new RegExp('Título '+slug));}
    assert.match(ctx.doc.querySelector('#content').textContent,/becas/);
    click(ctx,'.content-card button');assert.match(ctx.doc.querySelector('#content').textContent,/Biblioteca/);
  }finally{ctx.close();}
});
test('API editorial caída conserva login operativo y permite reintento',async()=>{
  let offline=true;const ctx=await setup({handle:(url)=>url==='/api/config'&&offline?Promise.reject(new Error('offline')):null});
  try{
    assert.match(ctx.doc.querySelector('#content-status').textContent,/No se pudo cargar/);
    assert.equal(ctx.doc.querySelector('#login-form').hidden,false);
    ctx.doc.querySelector('#username').value='demo.estudiante';ctx.doc.querySelector('#password').value='Fictitious-only';submit(ctx,'#login-form');await settle();
    assert.equal(ctx.doc.querySelector('#session').hidden,false);assert.match(ctx.doc.querySelector('#visitor-name').textContent,/Estudiante/);
    offline=false;click(ctx,'#refresh');await settle();assert.equal(ctx.doc.querySelectorAll('[data-section]').length,6);
  }finally{ctx.close();}
});
test('login no espera las peticiones editoriales pendientes',async()=>{
  const ctx=await setup({handle:url=>url==='/api/config'?new Promise(()=>{}):null});try{
    ctx.doc.querySelector('#username').value='demo.estudiante';ctx.doc.querySelector('#password').value='Fake';submit(ctx,'#login-form');await settle();
    assert.equal(ctx.doc.querySelector('#session').hidden,false);
    assert.equal(ctx.doc.querySelector('#password').value,'');
  }finally{ctx.close();}
});
test('configuración actualizada quita secciones y añade categorías nuevas',async()=>{
  let updated=false;const fresh={id:90,slug:'cultura-nueva',name:'Cultura nueva',content_type:'generic'};
  const ctx=await setup({handle:url=>updated&&url==='/api/config'?response({sections:[fresh],survey:{}}):updated&&url.startsWith('/api/categorias')?response([fresh]):updated&&url==='/api/cultura-nueva'?response([]):null});try{
    updated=true;click(ctx,'#refresh');await settle();
    assert.equal(ctx.doc.querySelector('[data-section="noticias"]'),null);assert.ok(ctx.doc.querySelector('[data-section="cultura-nueva"]'));
    assert.ok(ctx.doc.querySelector('#login-link'));assert.match(ctx.doc.querySelector('#content').textContent,/No hay publicaciones/);
  }finally{ctx.close();}
});
test('texto malicioso se escapa y esquemas peligrosos no generan enlaces',async()=>{
  const item={...content(0),title:'<img src=x onerror=alert(1)>',description:'<script>evil()</script>',details:{external_url:'javascript:alert(1)'}};
  const ctx=await setup({handle:url=>url==='/api/noticias'?response([item]):null});try{
    click(ctx,'.content-card button');assert.equal(ctx.doc.querySelector('#content img'),null);assert.equal(ctx.doc.querySelector('#content script'),null);
    assert.match(ctx.doc.querySelector('#content').textContent,/<img/);assert.equal(ctx.doc.querySelector('#content a'),null);
  }finally{ctx.close();}
});
test('enlace externo seguro usa noopener y aviso de otra ventana',async()=>{
  const ctx=await setup();try{click(ctx,'[data-section="servicios"]');await settle();click(ctx,'.content-card button');const a=ctx.doc.querySelector('#content a');assert.equal(a.protocol,'https:');assert.equal(a.rel,'noopener noreferrer');assert.equal(a.target,'_blank');}finally{ctx.close();}
});
test('apertura y sección registran una sola vista por carga',async()=>{
  const ctx=await setup();try{
    click(ctx,'.content-card button');click(ctx,'.content-card button');click(ctx,'.content-card button');
    click(ctx,'[data-section="noticias"]');await settle();
    const views=ctx.calls.filter(c=>c.url==='/api/vistas');
    assert.equal(views.filter(c=>c.data.section==='portal').length,1);
    assert.equal(views.filter(c=>c.data.section==='noticias'&&!c.data.content).length,1);
    assert.equal(views.filter(c=>c.data.content===1).length,1);
    assert.deepEqual(Object.keys(views.find(c=>c.data.content).data).sort(),['content','section']);
  }finally{ctx.close();}
});
test('fallo estadístico no bloquea lectura ni navegación',async()=>{
  const ctx=await setup({handle:url=>url==='/api/vistas'?Promise.reject(new Error('stats offline')):null});try{click(ctx,'.content-card button');click(ctx,'[data-section="eventos"]');await settle();assert.match(ctx.doc.querySelector('#content').textContent,/Título eventos/);}finally{ctx.close();}
});
test('encuesta simple, múltiple y abierta envía valores y evita doble clic',async()=>{
  const ctx=await setup();try{
    click(ctx,'[data-section="encuestas"]');await settle();click(ctx,'.content-card button');fillSurvey(ctx);
    submit(ctx,'.survey-form');submit(ctx,'.survey-form');await settle();
    const sent=ctx.calls.filter(c=>/respuestas$/.test(c.url));assert.equal(sent.length,1);
    assert.deepEqual(sent[0].data.answers.map(a=>a.options),[[21],[23,24],[]]);assert.equal(sent[0].data.answers[2].value,'Respuesta de prueba');
    assert.equal(ctx.doc.querySelector('.survey-form button').disabled,true);assert.match(ctx.doc.querySelector('.survey-message').textContent,/registrada/);
  }finally{ctx.close();}
});
test('encuesta inválida y error recuperable conservan respuestas',async()=>{
  const ctx=await setup({handle:url=>/respuestas$/.test(url)?response({detail:'Encuesta fuera de vigencia'},404):null});try{
    click(ctx,'[data-section="encuestas"]');await settle();click(ctx,'.content-card button');submit(ctx,'.survey-form');await settle();assert.match(ctx.doc.querySelector('.survey-message').textContent,/obligatorias/);
    fillSurvey(ctx);submit(ctx,'.survey-form');await settle();assert.match(ctx.doc.querySelector('.survey-message').textContent,/fuera de vigencia/);assert.equal(ctx.doc.querySelector('textarea').value,'Respuesta de prueba');assert.equal(ctx.doc.querySelector('.survey-form button').disabled,false);
  }finally{ctx.close();}
});
test('encuesta que requiere sesión conserva borrador antes de autenticar',async()=>{
  const ctx=await setup({handle:url=>url==='/api/config'?response({sections:categories,survey:{vote_requires_auth:true,max_options:2}}):null});try{
    click(ctx,'[data-section="encuestas"]');await settle();click(ctx,'.content-card button');fillSurvey(ctx);submit(ctx,'.survey-form');await settle();
    assert.match(ctx.doc.querySelector('.survey-message').textContent,/Inicia sesión/);assert.equal(ctx.calls.filter(c=>/respuestas$/.test(c.url)).length,0);
    ctx.doc.querySelector('#username').value='demo.estudiante';ctx.doc.querySelector('#password').value='Fake';submit(ctx,'#login-form');await settle();
    assert.equal(ctx.doc.querySelector('textarea').value,'Respuesta de prueba');submit(ctx,'.survey-form');await settle();assert.equal(ctx.calls.filter(c=>/respuestas$/.test(c.url)).length,1);
  }finally{ctx.close();}
});
test('encuesta externa abre enlace sin formulario ni iframe',async()=>{
  const item={...content(4),details:{external_url:'https://example.invalid/encuesta',questions:[]}};
  const ctx=await setup({handle:url=>url==='/api/encuestas'?response([item]):null});try{click(ctx,'[data-section="encuestas"]');await settle();click(ctx,'.content-card button');assert.equal(ctx.doc.querySelector('.survey-form'),null);assert.ok(ctx.doc.querySelector('#content a'));assert.equal(ctx.doc.querySelector('iframe'),null);}finally{ctx.close();}
});
test('errores de login y logout real se reflejan sin guardar contraseña',async()=>{
  let bad=true;const ctx=await setup({handle:(url,opts)=>url==='/portal-auth/session'&&opts.method==='POST'&&bad?response({detail:'Demasiados intentos'},429):null});try{
    ctx.doc.querySelector('#username').value='demo.estudiante';ctx.doc.querySelector('#password').value='Fake';submit(ctx,'#login-form');await settle();assert.match(ctx.doc.querySelector('#login-message').textContent,/Demasiados/);
    bad=false;ctx.doc.querySelector('#password').value='Fake';submit(ctx,'#login-form');await settle();click(ctx,'#logout');await settle();assert.equal(ctx.doc.querySelector('#login-form').hidden,false);assert.ok(ctx.calls.some(c=>c.url==='/portal-auth/logout'&&c.method==='POST'));
  }finally{ctx.close();}
});
test('alternativa XHR funciona sin fetch, Promise ni AbortController',async()=>{
  const dom=new JSDOM(html.replace(/<script>[\s\S]*?<\/script>/,''),{url:'http://127.0.0.1:8010/portal/',runScripts:'outside-only'});const w=dom.window;
  w.fetch=undefined;w.AbortController=undefined;w.Promise=undefined;
  w.XMLHttpRequest=class {open(method,url){this.url=url;}setRequestHeader(){}send(){this.status=200;this.responseText=JSON.stringify(this.url==='/portal-auth/session'?{authenticated:false,csrfToken:'fallback'}:this.url==='/api/config'?{sections:[],survey:{}}:[]);this.onload();}};
  try{w.eval(source);assert.match(w.document.querySelector('#content').textContent,/No hay secciones/);assert.equal(w.document.querySelector('#login-form').hidden,false);}finally{w.close();}
});
test('estructura adaptable y controles accesibles, sin certificar geometría JSDOM',()=>{
  assert.match(html,/@media\s*\(min-width:600px\)/);assert.match(html,/@media\s*\(min-width:980px\)/);
  assert.match(html,/minmax\(0,1fr\)/);assert.match(html,/focus-visible/);assert.match(html,/prefers-reduced-motion/);
  assert.match(html,/aria-live="polite"/);assert.match(html,/class="skip-link"/);
});
test('timeout editorial aborta petición y mantiene login visible',async()=>{
  let aborts=0;const pending=[];
  const ctx=await setup({prepare:w=>{const original=w.setTimeout.bind(w);w.setTimeout=(callback,delay)=>delay===8000?(pending.push(callback),pending.length):original(callback,delay);w.clearTimeout=()=>{};},
    handle:(url,opts)=>url==='/api/config'?new Promise(()=>{opts.signal.addEventListener('abort',()=>aborts++);}):null});
  try{pending.forEach(callback=>callback());await settle();assert.equal(aborts,1);assert.match(ctx.doc.querySelector('#content-status').textContent,/No se pudo cargar/);assert.equal(ctx.doc.querySelector('#login-form').hidden,false);assert.equal(ctx.doc.querySelector('#refresh').disabled,false);}finally{ctx.close();}
});
