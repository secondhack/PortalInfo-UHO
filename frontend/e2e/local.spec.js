import {test,expect} from '@playwright/test';
import {readFileSync,mkdirSync} from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const captures=path.join(root,'.local/capturas');mkdirSync(captures,{recursive:true});
const cms=Object.fromEntries(readFileSync(path.join(root,'.local/demo-credentials.txt'),'utf8').trim().split(/\r?\n/).map(line=>line.split('\t')));
const visitorLine=readFileSync(path.join(root,'.local/portal-demo-credentials.txt'),'utf8').split(/\r?\n/).find(line=>line.startsWith('demo.estudiante: '));
const visitor={username:visitorLine.split(': ')[0],password:visitorLine.split(': ')[1]};
test.beforeAll(async({browser})=>{console.log('Navegador local de pruebas: Chromium/Chrome '+browser.version());});

test.beforeEach(async({context})=>{
 await context.route('**/*',route=>['127.0.0.1','localhost'].includes(new URL(route.request().url()).hostname)?route.continue():route.abort());
});
async function login(page,role='superadmin'){
 await page.goto('/login');await expect(page.getByRole('button',{name:/Entrar al panel/})).toBeVisible();
 await page.evaluate(({email,password})=>{document.querySelector('[name=email]').value=email;document.querySelector('[name=password]').value=password;},
  {email:`demo.${role}@uho.edu.cu`,password:cms[`demo.${role}@uho.edu.cu`]});
 await page.getByRole('button',{name:/Entrar al panel/}).click();await expect(page.getByRole('heading',{name:'Dashboard',exact:true})).toBeVisible();
}
async function visitorLogin(page){
 await page.evaluate(value=>{document.querySelector('#username').value=value.username;document.querySelector('#password').value=value.password;},visitor);
 await page.locator('#login-submit').click();await expect(page.locator('#visitor-name')).toBeVisible();
}
async function noOverflow(page){
 const dimensions=await page.evaluate(()=>({width:innerWidth,scroll:document.documentElement.scrollWidth}));
 expect(dimensions.scroll).toBeLessThanOrEqual(dimensions.width+1);
}
async function write(context,endpoint,body={},method='POST'){
 const token=await (await context.request.get('http://127.0.0.1:8010/api/csrf/')).json();
 const response=await context.request.fetch('http://127.0.0.1:8010'+endpoint,{method,data:body,headers:{'X-CSRFToken':token.csrfToken}});
 expect(response.status()).toBeLessThan(400);return response.status()===204?null:response.json();
}

for(const width of [360,390,480,768,1280])test(`portal sin desbordamiento en ${width}px`,async({page})=>{
 await page.setViewportSize({width,height:850});await page.goto('http://127.0.0.1:8010/portal/');
 await expect(page.locator('#username')).toBeVisible();await expect(page.locator('#network-label')).toBeVisible();await expect(page.locator('[data-section]').first()).toBeVisible();await noOverflow(page);
 await page.screenshot({path:path.join(captures,`portal-${width}.png`),fullPage:true});
});

test('todas las rutas administrativas cargan sin excepciones ni API fallidas',async({page})=>{
 test.setTimeout(180000);const errors=[];page.on('pageerror',error=>errors.push(error.message));
 page.on('response',response=>{if(response.url().includes('/api/admin/')&&response.status()>=400)errors.push('HTTP '+response.status()+' '+new URL(response.url()).pathname);});
 await page.setViewportSize({width:1366,height:900});await login(page);
 for(const route of ['/','/content/noticias','/contents','/contents/pending','/contents/active','/contents/hidden','/approvals','/notifications','/users','/roles','/permissions','/categories','/catalog-types','/catalog-items','/settings','/statistics','/audit','/pending']){
  await page.goto(route);await expect(page.locator('main h1')).toBeVisible();
  await expect(page.locator('main .loading')).toHaveCount(0);await noOverflow(page);
  await page.screenshot({path:path.join(captures,'panel-'+(route==='/'?'dashboard':route.slice(1).replaceAll('/','-'))+'.png'),fullPage:true});
  if(route==='/statistics')for(const label of ['Ciberseguridad','Logs de acceso','Resultados de encuestas']){
   await page.getByRole('tab',{name:label,exact:true}).click();await expect(page.locator('main .loading')).toHaveCount(0);await noOverflow(page);
   await page.screenshot({path:path.join(captures,'panel-estadisticas-'+label.replaceAll(' ','-')+'.png'),fullPage:true});
  }
 }
 expect(errors).toEqual([]);
});

test('panel adaptable y formularios utilizables en móvil',async({page})=>{
 await login(page);
 for(const width of [360,480,768]){
  await page.setViewportSize({width,height:850});await page.goto('/users');await expect(page.getByRole('heading',{name:'Usuarios',exact:true})).toBeVisible();await noOverflow(page);
  await page.getByRole('button',{name:'+ Crear registro'}).click();await expect(page.getByRole('dialog')).toBeVisible();await noOverflow(page);
  await page.screenshot({path:path.join(captures,`panel-formulario-${width}.png`),fullPage:true});await page.keyboard.press('Escape');await expect(page.getByRole('dialog')).toHaveCount(0);
 }
});

test('Gestor no accede a auditoría ni estadísticas y puede abrir editor',async({page})=>{
 await login(page,'gestor');await page.goto('/audit');await expect(page.getByRole('heading',{name:'Acceso denegado'})).toBeVisible();
 await page.goto('/statistics');await expect(page.getByRole('heading',{name:'Acceso denegado'})).toBeVisible();
 await page.goto('/content/noticias');await page.getByRole('button',{name:'+ Nuevo contenido'}).click();await expect(page.getByRole('dialog')).toBeVisible();
 await expect(page.getByLabel('Título',{exact:true})).toBeVisible();await page.keyboard.press('Escape');await expect(page.getByRole('dialog')).toHaveCount(0);
});

test('fallo editorial real en navegador no bloquea login ni logout',async({page,context})=>{
 await context.route('**/api/**',route=>route.abort('failed'));
 await page.goto('http://127.0.0.1:8010/portal/');await expect(page.locator('#content-status')).toContainText('No se pudo cargar');
 await visitorLogin(page);await expect(page.locator('#session')).toContainText('Sesión de demostración activa');
 await page.locator('#logout').click();await expect(page.locator('#login-form')).toBeVisible();
 await context.unroute('**/api/**');await page.locator('#refresh').click();await expect(page.locator('[data-section]').first()).toBeVisible();
});

test('encuesta real desde formulario del portal hasta estadísticas',async({page,browser})=>{
 const adminContext=await browser.newContext();let id;
 try{
  const adminPage=await adminContext.newPage();await login(adminPage,'admin');
  const meta=await (await adminContext.request.get('http://127.0.0.1:8010/api/admin/content-metadata/')).json();
  const category=meta.categories.find(c=>c.content_type==='survey');const title='DEMO navegador B5 '+Date.now();
  const item=await write(adminContext,'/api/admin/contents/',{category:category.id,title:title.slice(0,category.title_limit),description:'Encuesta propia de comprobación visual.',validity:'always',details:{external_url:'',questions:[
   {text:'Simple DEMO',kind:'single',required:true,options:[{text:'A'},{text:'B'}]},
   {text:'Múltiple DEMO',kind:'multiple',required:true,options:[{text:'C'},{text:'D'}]},
   {text:'Abierta DEMO',kind:'open',required:false,options:[]}]}});id=item.id;
  await write(adminContext,`/api/admin/contents/${id}/submit/`);await write(adminContext,`/api/admin/contents/${id}/review/`,{approved:true});
  await page.goto('http://127.0.0.1:8010/portal/');await visitorLogin(page);await page.locator('[data-section=encuestas]').click();
  const article=page.locator('article').filter({hasText:title});await article.getByRole('button',{name:'Participar en la encuesta'}).click();
  await article.locator('input[type=radio]').first().check();for(const checkbox of await article.locator('input[type=checkbox]').all())await checkbox.check();
  await article.locator('textarea').fill('DEMO respuesta de comprobación en navegador');
  await article.getByRole('button',{name:'Enviar respuestas',exact:true}).click();await expect(article.locator('.survey-message')).toContainText('Respuesta registrada');
  await expect(article.getByRole('button',{name:'Respuesta enviada'})).toBeDisabled();
  const result=await (await adminContext.request.get(`http://127.0.0.1:8010/api/admin/contents/${id}/results/`)).json();expect(result.total).toBe(1);expect(result.answers_total).toBe(3);
  await page.screenshot({path:path.join(captures,'portal-encuesta-enviada.png'),fullPage:true});
 }finally{if(id)await write(adminContext,`/api/admin/contents/${id}/`,{},'DELETE');await adminContext.close();}
});

test('descargas CSV y PDF se reciben desde el panel',async({page})=>{
 await login(page,'admin');const buttons=page.locator('main').getByRole('button',{name:/CSV|PDF/});await expect(buttons.first()).toBeVisible();
 for(const format of ['CSV','PDF']){
  const waiting=page.waitForEvent('download');await page.locator('main').getByRole('button',{name:new RegExp(format)}).first().click();
  const download=await waiting;expect(download.suggestedFilename().toLowerCase()).toContain('.'+format.toLowerCase());expect(await download.failure()).toBeNull();
 }
});

test('teclado llega al login y foco visible',async({page})=>{
 await page.goto('http://127.0.0.1:8010/portal/');await page.keyboard.press('Tab');await expect(page.locator('.skip-link')).toBeFocused();
 await page.keyboard.press('Enter');await expect(page.locator('#login')).toBeFocused();await page.keyboard.press('Tab');await expect(page.locator('#username')).toBeFocused();
 const outline=await page.locator('#username').evaluate(input=>getComputedStyle(input).outlineStyle);expect(outline).not.toBe('none');
});
