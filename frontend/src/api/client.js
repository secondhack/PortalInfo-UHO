let csrfToken;
async function request(path,options){
  try{return await fetch(path,options);}
  catch(error){throw new Error(error.name==='AbortError'?'Petición cancelada.':'No se pudo conectar al servidor. Comprueba que el backend esté iniciado y vuelve a intentarlo.');}
}
export async function api(path, options = {}) {
  const method = options.method || 'GET';
  if (!['GET','HEAD'].includes(method) && !csrfToken) {
    csrfToken = (await api('/api/csrf/')).csrfToken;
  }
  const response = await request(path, {credentials:'include', ...options,
    headers:{'Content-Type':'application/json', ...(csrfToken ? {'X-CSRFToken':csrfToken} : {}), ...options.headers},
    ...(options.body ? {body:JSON.stringify(options.body)} : {})});
  const data = response.status === 204 ? null : await response.json().catch(()=>({detail:'Respuesta inesperada del servidor.'}));
  if (!response.ok) {
    const error = new Error(data?.detail || Object.entries(data || {}).map(([k,v])=>`${k}: ${v}`).join(' · ') || 'No se pudo completar la operación.');
    error.status = response.status;
    throw error;
  }
  if (path === '/auth/login' || path === '/auth/logout') csrfToken = null;
  return data;
}
export async function all(path) {
  const rows = [];
  let next = path;
  while (next) {
    const data = await api(next);
    if (Array.isArray(data)) return data;
    rows.push(...data.results);
    next = data.next ? new URL(data.next, location.origin).pathname + new URL(data.next, location.origin).search : null;
  }
  return rows;
}

export async function download(path){
 const response=await request(path,{credentials:'include'});
 if(!response.ok){const data=await response.json().catch(()=>({detail:'No se pudo descargar el reporte.'}));throw new Error(data.detail||JSON.stringify(data));}
 const blob=await response.blob();const url=URL.createObjectURL(blob);const anchor=document.createElement('a');
 anchor.href=url;anchor.download=response.headers.get('Content-Disposition')?.match(/filename="([^"]+)"/)?.[1]||'portalinfo-reporte';
 document.body.appendChild(anchor);anchor.click();anchor.remove();URL.revokeObjectURL(url);
}
