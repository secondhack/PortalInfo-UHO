import React from 'react';
import {it,expect,vi,beforeEach,afterEach} from 'vitest';
import {render,screen,fireEvent,waitFor,cleanup,act} from '@testing-library/react';
import {MemoryRouter} from 'react-router-dom';
vi.mock('../api/client',()=>({api:vi.fn(),all:vi.fn(),download:vi.fn()}));
vi.mock('../contexts/Auth',()=>({useAuth:()=>({user:{role_code:'superadmin'}})}));
vi.mock('chart.js',async importOriginal=>{
 const actual=await importOriginal();const Chart=vi.fn(function(){return {destroy:vi.fn()};});Chart.register=vi.fn();return {...actual,Chart};
});
import {api,all,download} from '../api/client';
import {Chart} from 'chart.js';
import NotificationBell from '../components/NotificationBell';
import MetricChart from '../components/MetricChart';
import ReportButtons from '../components/ReportButtons';
import Approvals from './Approvals';
import Statistics from './Statistics';
import Audit from './Audit';
beforeEach(()=>{vi.clearAllMocks();api.mockReset();all.mockReset();download.mockReset();all.mockResolvedValue([]);download.mockResolvedValue(undefined);});
afterEach(()=>{cleanup();vi.useRealTimers();});

it('la campana muestra el contador real y permite marcar la notificación propia',async()=>{
 let read=false;
 api.mockImplementation(async(path,options)=>{if(path.includes('mark_read')){read=true;return{};}if(path.includes('/unread/'))return {count:read?0:1};return{results:[{id:1,title:'Contenido aprobado',message:'La revisión fue aprobada.',kind:'content.approved',resource_id:12,read,created_at:'2026-11-14T13:00:00Z'}]};});
 render(<MemoryRouter><NotificationBell/></MemoryRouter>);
 fireEvent.click(await screen.findByLabelText('Notificaciones: 1 no leídas'));expect(await screen.findByText('La revisión fue aprobada.')).toBeInTheDocument();
 expect(screen.getByText('Ver contenido')).toHaveAttribute('href','/contents?content=12');fireEvent.click(screen.getByText('Marcar como leída'));
 await waitFor(()=>expect(api).toHaveBeenCalledWith('/api/admin/notifications/1/mark_read/',{method:'POST'}));expect(await screen.findByLabelText('Notificaciones: 0 no leídas')).toBeInTheDocument();
});

it('el polling de campana usa treinta segundos y se limpia al desmontar',async()=>{
 vi.useFakeTimers();Object.defineProperty(document,'visibilityState',{configurable:true,value:'visible'});api.mockResolvedValue({count:0});
 const view=render(<MemoryRouter><NotificationBell/></MemoryRouter>);await act(async()=>{});expect(api).toHaveBeenCalledTimes(1);
 await act(async()=>{await vi.advanceTimersByTimeAsync(30000);});expect(api).toHaveBeenCalledTimes(2);
 view.unmount();await act(async()=>{await vi.advanceTimersByTimeAsync(60000);});expect(api).toHaveBeenCalledTimes(2);
});

it('la cola compara la aprobación anterior y rechaza con motivo por la API',async()=>{
 let decided=false;
 const row={id:3,content:5,title:'Propuesta',category:'Avisos',author:'gestor@uho.edu.cu',version:2,state:'pending',created_at:'2026-11-14T13:00:00Z',proposal:{title:'Propuesta',description:'Texto nuevo',details:{}},approved_version:{title:'Aprobado anterior',description:'Texto anterior',details:{}}};
 api.mockImplementation(async(path,options)=>{if(path.includes('content-metadata'))return {categories:[{id:1,name:'Avisos'}],areas:[]};if(path.includes('/authors/'))return[{id:1,email:row.author}];if(path.includes('/summary/'))return{pending:decided?0:1};if(path.includes('/decide/')){decided=true;return{};}return{count:decided?0:1,results:decided?[]:[row],next:null,previous:null};});
 render(<Approvals/>);fireEvent.click(await screen.findByText('Ver / comparar / revisar'));expect(screen.getByText('Aprobado anterior')).toBeInTheDocument();expect(screen.getByText('Texto nuevo')).toBeInTheDocument();
 fireEvent.change(screen.getByLabelText('Motivo del rechazo'),{target:{value:'Corregir la convocatoria.'}});fireEvent.submit(screen.getByText('Rechazar con motivo').closest('form'));
 await waitFor(()=>expect(api).toHaveBeenCalledWith('/api/admin/approvals/3/decide/',{method:'POST',body:{approved:false,reason:'Corregir la convocatoria.'}}));expect(await screen.findByText('Solicitud rechazada; el motivo quedó registrado.')).toBeInTheDocument();
});

it('el gráfico recibe valores de la API y conserva una alternativa tabular',()=>{
 const view=render(<MetricChart title="Visitas reales" rows={[{label:'Hoy',count:3},{label:'Ayer',count:2}]}/>);
 expect(Chart).toHaveBeenCalledWith(expect.anything(),expect.objectContaining({data:expect.objectContaining({datasets:[expect.objectContaining({data:[3,2]})]})}));
 expect(screen.getByRole('img',{name:'Visitas reales'})).toBeInTheDocument();expect(screen.getByText('Consultar datos en tabla')).toBeInTheDocument();const instance=Chart.mock.results.at(-1).value;view.unmount();expect(instance.destroy).toHaveBeenCalled();
});

it('los botones descargan CSV/PDF con los filtros y muestran errores',async()=>{
 const error=vi.fn();download.mockRejectedValueOnce(new Error('Acceso denegado'));
 render(<ReportButtons kind="accesses" query="period=custom&date_from=2026-11-01&date_to=2026-11-02&device=mobile" onError={error}/>);
 fireEvent.click(screen.getByText('Descargar CSV'));await waitFor(()=>expect(error).toHaveBeenCalledWith('Acceso denegado'));
 fireEvent.click(screen.getByText('Descargar PDF'));await waitFor(()=>expect(download).toHaveBeenLastCalledWith('/api/admin/reports/accesses/?period=custom&date_from=2026-11-01&date_to=2026-11-02&device=mobile&file_format=pdf'));
});

it('estadísticas cambia a ciberseguridad y permite revisar una señal sin bloquear cuentas',async()=>{
 let reviewed=false;
 const stats={accesses:0,views:0,identified_accounts:0,by_day:[],by_device:[],by_user_type:[],by_hour:[],top_contents:[],by_section:[],by_week:[],by_month:[],by_category:[]};
 const alert={id:8,uid:'seudónimo',kind:'multiple_ips',priority:'medium',window_start:'2026-11-14T13:00:00Z',window_end:'2026-11-14T13:30:00Z',reviewed_at:null,evidence:{distinct_ips:3}};
 api.mockImplementation(async(path,options)=>{if(path==='/api/categorias')return [];if(path.includes('estadisticas?'))return stats;if(path.includes('/mark_reviewed/')){reviewed=true;return{};}return{count:1,results:[{...alert,reviewed_at:reviewed?'2026-11-14T13:31:00Z':null}],next:null,previous:null};});
 render(<Statistics/>);await screen.findByText('Comprobar registro de actividad');fireEvent.click(screen.getByRole('tab',{name:'Ciberseguridad'}));fireEvent.click(await screen.findByText('Marcar revisada'));
 await waitFor(()=>expect(api).toHaveBeenCalledWith(expect.stringContaining('/security-alerts/8/mark_reviewed/'),{method:'POST'}));expect(screen.getByText(/No demuestran uso compartido de cuentas/)).toBeInTheDocument();expect(screen.queryByText('Bloquear cuenta')).not.toBeInTheDocument();
});

it('la auditoría filtra por entidad y muestra el resumen antes y después',async()=>{
 all.mockResolvedValue([{id:1,email:'superadmin@uho.edu.cu'}]);
 api.mockResolvedValue({count:1,results:[{id:1,actor:1,action:'configuration.update',entity:'configuration',resource:'1',created_at:'2026-11-14T13:00:00Z',metadata:{before:{retention_days:90},after:{retention_days:120}}}],next:null,previous:null});
 render(<Audit/>);await screen.findByText('configuration.update');fireEvent.change(screen.getByLabelText('Entidad'),{target:{value:'configuration'}});
 await waitFor(()=>expect(api).toHaveBeenCalledWith(expect.stringContaining('entity=configuration')));fireEvent.click(screen.getByText('Ver resumen antes/después'));expect(screen.getByText(/"retention_days": 120/)).toBeInTheDocument();expect(screen.queryByText('Eliminar')).not.toBeInTheDocument();
});

it('los resultados distinguen envíos e identidades y restringen la consulta abierta a su API',async()=>{
 all.mockResolvedValue([{id:10,title:'Encuesta real'}]);
 api.mockImplementation(async path=>{if(path==='/api/categorias')return [];if(path.includes('estadisticas?'))return {accesses:0,views:0,identified_accounts:0};if(path.includes('/open_answers/'))return{count:1,results:[{id:1,value:'Respuesta registrada',created_at:'2026-11-14T13:00:00Z',submission__publication__version:1}],next:null,previous:null};if(path.includes('/results/'))return{total:2,participants:1,answers_total:2,demo_submissions:0,percentage_basis:'Base: respuestas',versions:[{version:1,total:2,questions:[{id:9,text:'Comentario',kind:'open',answered:2,options:[]}]}]};return{};});
 render(<Statistics/>);await screen.findByText('Comprobar registro de actividad');fireEvent.click(screen.getByRole('tab',{name:'Resultados de encuestas'}));fireEvent.change(await screen.findByLabelText('Encuesta'),{target:{value:'10'}});
 expect(await screen.findByText(/2 envíos · 1 identidades seudónimas distintas/)).toBeInTheDocument();fireEvent.click(screen.getByText('Consultar respuestas abiertas (2)'));
 expect(await screen.findByText('Respuesta registrada')).toBeInTheDocument();expect(api).toHaveBeenCalledWith(expect.stringContaining('/contents/10/open_answers/'));
});
