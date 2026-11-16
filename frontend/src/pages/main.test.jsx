import React from 'react';
import {describe,it,expect,vi,beforeEach,afterEach} from 'vitest';
import {render,screen,fireEvent,waitFor,cleanup,act} from '@testing-library/react';
import {MemoryRouter} from 'react-router-dom';
import Login from './Login';
import Dashboard from './Dashboard';
import Resource from './Resource';
import {resources} from './resources';
import Settings from './Settings';
const login=vi.fn();
vi.mock('../contexts/Auth',()=>({useAuth:()=>({user:currentUser,login})}));
vi.mock('../api/client',()=>({api:vi.fn(),all:vi.fn().mockResolvedValue([])}));
import {api} from '../api/client';
let currentUser=null;
beforeEach(()=>{currentUser=null;vi.clearAllMocks();});
afterEach(cleanup);
describe('Administración',()=>{
 it('un fallo de carga muestra el error y termina el indicador de espera',async()=>{
  currentUser={role_code:'superadmin'};api.mockRejectedValue(new Error('Servicio no disponible'));
  render(<Resource config={resources.users}/>);
  expect(await screen.findByRole('alert')).toHaveTextContent('Servicio no disponible');
  expect(screen.queryByText('Cargando información…')).not.toBeInTheDocument();
 });
 it('ignora una búsqueda anterior que termina después de la actual',async()=>{
  currentUser={role_code:'superadmin'};let resolveFirst;
  api.mockImplementation(path=>path.includes('search=actual')?Promise.resolve({count:1,results:[{id:2,email:'actual@uho.edu.cu',categories:[]}]}):new Promise(resolve=>{resolveFirst=resolve;}));
  render(<Resource config={resources.users}/>);
  fireEvent.change(screen.getByLabelText('Buscar'),{target:{value:'actual'}});
  expect(await screen.findByText('actual@uho.edu.cu')).toBeInTheDocument();
  await act(async()=>{resolveFirst({count:1,results:[{id:1,email:'anterior@uho.edu.cu',categories:[]}]});});
  expect(screen.queryByText('anterior@uho.edu.cu')).not.toBeInTheDocument();expect(screen.getByText('actual@uho.edu.cu')).toBeInTheDocument();
 });
 it('envía las credenciales y muestra el error del servidor',async()=>{login.mockRejectedValueOnce(new Error('No tiene acceso a este sistema'));render(<MemoryRouter><Login/></MemoryRouter>);fireEvent.change(screen.getByLabelText('Correo institucional'),{target:{value:'demo@uho.edu.cu'}});fireEvent.change(screen.getByLabelText('Contraseña de demostración'),{target:{value:'secret'}});fireEvent.click(screen.getByRole('button',{name:/Entrar/}));expect(await screen.findByRole('alert')).toHaveTextContent('No tiene acceso');expect(login).toHaveBeenCalledWith('demo@uho.edu.cu','secret');});
 it('muestra contadores recibidos del backend',async()=>{currentUser={role_code:'admin'};api.mockResolvedValueOnce({users:3,categories:5,contents:0,pending:0,portal_analytics:'Pendiente'});render(<MemoryRouter><Dashboard/></MemoryRouter>);expect(await screen.findByText('3')).toBeInTheDocument();expect(screen.getByText('5')).toBeInTheDocument();expect(screen.getByText('No se muestran métricas simuladas.')).toBeInTheDocument();});
 it('crea usuarios mediante la API y refresca el listado',async()=>{currentUser={role_code:'superadmin'};api.mockResolvedValue({count:0,results:[],next:null,previous:null});render(<Resource config={resources.users}/>);await screen.findByText('No hay registros que coincidan.');fireEvent.click(screen.getByText('+ Crear registro'));fireEvent.change(screen.getByLabelText('Correo @uho.edu.cu'),{target:{value:'new@uho.edu.cu'}});fireEvent.submit(screen.getByRole('button',{name:'Guardar'}).closest('form'));await waitFor(()=>expect(api).toHaveBeenCalledWith('/api/admin/users/',expect.objectContaining({method:'POST',body:expect.objectContaining({email:'new@uho.edu.cu'})})));});
 it('guarda configuración persistente',async()=>{currentUser={role_code:'superadmin'};api.mockResolvedValue({max_questions:10,max_options:6,allow_open_questions:true,vote_requires_auth:false,default_validity_days:3,portal_url:'',login_attempts:5,lockout_seconds:300,session_seconds:1800,retention_days:90});render(<Settings/>);fireEvent.change(await screen.findByLabelText('Máximo de preguntas'),{target:{value:'12'}});fireEvent.click(screen.getByText('Guardar cambios'));await waitFor(()=>expect(api).toHaveBeenCalledWith('/api/admin/settings/',expect.objectContaining({method:'PATCH',body:expect.objectContaining({max_questions:12})})));});
});
