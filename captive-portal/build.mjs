import {createRequire} from 'node:module';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
const root=path.dirname(fileURLToPath(import.meta.url));
const require=createRequire(path.join(root,'../frontend/package.json'));
const {transformSync}=require('esbuild');
let html=readFileSync(path.join(root,'src/index.html'),'utf8');
const origins={};
for(const key of ['PORTAL_API_BASE','PORTAL_AUTH_BASE']){
  let value=process.env[key]||'';
  if(value){const url=new URL(value);if(url.username||url.password||url.search||url.hash||url.pathname!=='/'||
    (url.protocol!=='https:'&&!(url.protocol==='http:'&&['127.0.0.1','localhost','[::1]'].includes(url.hostname))))throw new Error(key+': se requiere origen HTTPS o loopback HTTP, sin credenciales/ruta.');value=url.origin;}
  html=html.replace('__'+key+'__',()=>value);
  origins[key]=value;
}
if(origins.PORTAL_API_BASE!==origins.PORTAL_AUTH_BASE)throw new Error('La demostración requiere un origen compartido de sesión/CSRF. Configure ambas bases iguales mediante un proxy común.');
const css=transformSync(readFileSync(path.join(root,'src/portal.css'),'utf8'),{loader:'css',minify:true,target:'safari12'}).code.trim();
const js=transformSync(readFileSync(path.join(root,'src/portal.js'),'utf8'),{loader:'js',minify:true,target:'es2015',legalComments:'none'}).code.trim().replace(/<\/script/gi,'<\\/script');
html=html.replace('/* PORTAL_CSS */',()=>css).replace('/* PORTAL_JS */',()=>js).replace(/>\s+</g,'><').trim()+'\n';
mkdirSync(path.join(root,'dist'),{recursive:true});
writeFileSync(path.join(root,'dist/index.html'),html);
const bytes=Buffer.byteLength(html);
console.log(JSON.stringify({file:'captive-portal/dist/index.html',bytes,limit:204800,remaining:204800-bytes}));
if(bytes>204800)throw new Error('El HTML supera el límite de 204800 bytes.');
