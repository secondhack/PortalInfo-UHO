import {it,expect,vi,afterEach} from 'vitest';
afterEach(()=>{vi.unstubAllGlobals();vi.resetModules();});
const reply=(data,status=200)=>({ok:status<400,status,json:async()=>data});
it('obtiene CSRF, autentica con cookie y renueva token después del login',async()=>{
 const fetch=vi.fn().mockResolvedValueOnce(reply({csrfToken:'before'})).mockResolvedValueOnce(reply({id:1})).mockResolvedValueOnce(reply({csrfToken:'after'})).mockResolvedValueOnce(reply({detail:'Sesión cerrada'}));
 vi.stubGlobal('fetch',fetch);
 const {api}=await import('./client');
 await api('/auth/login',{method:'POST',body:{email:'test@uho.edu.cu',password:'test'}});
 expect(fetch).toHaveBeenNthCalledWith(2,'/auth/login',expect.objectContaining({credentials:'include',headers:expect.objectContaining({'X-CSRFToken':'before'})}));
 await api('/auth/logout',{method:'POST'});
 expect(fetch).toHaveBeenNthCalledWith(4,'/auth/logout',expect.objectContaining({headers:expect.objectContaining({'X-CSRFToken':'after'})}));
});
it('propaga errores de validación del servidor',async()=>{
 vi.stubGlobal('fetch',vi.fn().mockResolvedValue(reply({email:['Correo no válido']},400)));
 const {api}=await import('./client');
 await expect(api('/api/admin/users/')).rejects.toThrow('email: Correo no válido');
});
it('explica un fallo de conexión sin reintentar una escritura',async()=>{
 const fetch=vi.fn().mockRejectedValue(new TypeError('Failed to fetch'));vi.stubGlobal('fetch',fetch);
 const {api}=await import('./client');await expect(api('/api/admin/users/')).rejects.toThrow('backend esté iniciado');expect(fetch).toHaveBeenCalledTimes(1);
});
