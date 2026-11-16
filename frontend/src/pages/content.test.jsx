import React,{useState} from 'react';
import {it,expect,vi,beforeEach,afterEach} from 'vitest';
import {render,screen,fireEvent,waitFor,cleanup,within} from '@testing-library/react';
import {MemoryRouter,Routes,Route} from 'react-router-dom';
import ContentEditor from './ContentEditor';
import Contents from './Contents';
import SurveyEditor from '../components/SurveyEditor';
import {Dialog,PublicationPreview} from '../components/ContentUI';
vi.mock('../api/client',()=>({api:vi.fn()}));
vi.mock('../contexts/Auth',()=>({useAuth:()=>({user:{role_code:'admin'}})}));
import {api} from '../api/client';
const metadata={categories:[{id:1,name:'Noticias',slug:'noticias',content_type:'news',title_limit:100,description_limit:300,max_visible:5,required_fields:[],permissions:['view','create','edit','delete','submit']},{id:2,name:'Encuestas',slug:'encuestas',content_type:'survey',title_limit:100,description_limit:300,max_visible:1,required_fields:[],permissions:['view','create','edit','delete','submit']}],areas:[{id:1,name:'Área DEMO'}],service_types:[],survey:{max_questions:2,max_options:3,allow_open_questions:true,vote_requires_auth:false}};
beforeEach(()=>{vi.clearAllMocks();api.mockReset();});afterEach(cleanup);
it('usa la vigencia configurada para un contenido nuevo',async()=>{
 api.mockResolvedValue({id:50,revision:1});render(<ContentEditor metadata={metadata} initialCategory={1} onCancel={()=>{}} onSaved={()=>{}}/>);fillNews();
 fireEvent.click(screen.getByRole('button',{name:'Guardar borrador'}));
 await waitFor(()=>expect(api).toHaveBeenCalledWith('/api/admin/contents/',expect.objectContaining({body:expect.objectContaining({validity:'default'})})));
});
it('Escape utiliza el cierre vigente del diálogo',()=>{
 const first=vi.fn(),current=vi.fn();const view=render(<Dialog title="Prueba" onClose={first}><button>Acción</button></Dialog>);
 view.rerender(<Dialog title="Prueba" onClose={current}><button>Acción</button></Dialog>);fireEvent.keyDown(document,{key:'Escape'});expect(current).toHaveBeenCalledTimes(1);expect(first).not.toHaveBeenCalled();
});
function fillNews(){fireEvent.change(screen.getByLabelText('Título'),{target:{value:'Noticia de prueba'}});fireEvent.change(screen.getByLabelText('Descripción / contenido'),{target:{value:'Descripción válida'}});fireEvent.change(screen.getByLabelText('Área responsable'),{target:{value:'1'}});}
it('guarda y envía una noticia a la API y muestra su advertencia',async()=>{
 api.mockResolvedValueOnce({id:42,revision:1}).mockResolvedValueOnce({warning:'Se alcanzó el límite visible'});const saved=vi.fn();
 render(<ContentEditor metadata={metadata} initialCategory={1} onCancel={()=>{}} onSaved={saved}/>);fillNews();
 const submit=screen.getByRole('button',{name:'Enviar para aprobación'});fireEvent.click(submit);
 await waitFor(()=>expect(api).toHaveBeenCalledWith('/api/admin/contents/42/submit/',{method:'POST'}));
 expect(api).toHaveBeenCalledWith('/api/admin/contents/',expect.objectContaining({method:'POST',body:expect.objectContaining({category:1,title:'Noticia de prueba',details:expect.objectContaining({area:1})})}));expect(saved).toHaveBeenCalledWith('Se alcanzó el límite visible');
});
it('conserva el formulario cuando el servidor rechaza guardar',async()=>{
 api.mockRejectedValueOnce(new Error('El título supera el límite'));render(<ContentEditor metadata={metadata} initialCategory={1} onCancel={()=>{}} onSaved={()=>{}}/>);fillNews();fireEvent.submit(screen.getByText('Guardar borrador').closest('form'));
 expect(await screen.findByRole('alert')).toHaveTextContent('El título supera el límite');expect(screen.getByLabelText('Título')).toHaveValue('Noticia de prueba');
});
it('bloquea envíos duplicados mientras guarda',async()=>{
 let resolve;api.mockReturnValue(new Promise(r=>resolve=r));render(<ContentEditor metadata={metadata} initialCategory={1} onCancel={()=>{}} onSaved={()=>{}}/>);fillNews();const form=screen.getByText('Guardar borrador').closest('form');fireEvent.submit(form);fireEvent.submit(form);expect(api).toHaveBeenCalledTimes(1);resolve({id:1});await waitFor(()=>expect(screen.getByText('Guardar borrador')).toBeEnabled());
});
it('edita y reordena preguntas, opciones y obligatoriedad con límites configurables',()=>{
 function Harness(){const [value,set]=useState({questions:[],external_url:''});return <SurveyEditor value={value} onChange={set} config={metadata.survey}/>;}
 render(<Harness/>);fireEvent.click(screen.getByText('+ Añadir pregunta'));fireEvent.change(screen.getByLabelText('Texto de pregunta 1'),{target:{value:'Primera'}});fireEvent.click(screen.getByText('+ Añadir opción'));expect(screen.getByText('+ Añadir opción')).toBeDisabled();fireEvent.click(screen.getByLabelText('Eliminar opción 3 de pregunta 1'));fireEvent.click(screen.getByText('+ Añadir pregunta'));fireEvent.change(screen.getByLabelText('Texto de pregunta 2'),{target:{value:'Segunda'}});expect(screen.getByText('+ Añadir pregunta')).toBeDisabled();fireEvent.click(screen.getByText('Subir pregunta 2'));expect(screen.getByLabelText('Texto de pregunta 1')).toHaveValue('Segunda');fireEvent.change(screen.getByLabelText('Tipo de pregunta 1'),{target:{value:'open'}});expect(screen.queryByLabelText('Opción 1 de pregunta 1')).not.toBeInTheDocument();fireEvent.click(screen.getAllByLabelText('Obligatoria')[0]);expect(screen.getAllByLabelText('Obligatoria')[0]).not.toBeChecked();
});
it('el listado filtra, cambia visibilidad y confirma eliminación mediante la API',async()=>{
 const row={id:9,category:1,category_name:'Noticias',content_type:'news',title:'Noticia visible',state:'approved',revision:1,starts_at:'2026-11-14T10:00:00Z',ends_at:null,manual_active:true,public_visible:true,has_published_version:true,details:{area_name:'Área DEMO'},permissions:['view','edit','delete']};
 api.mockImplementation(async(path,options)=>path.includes('content-metadata')?metadata:options?{...row}: {count:1,results:[row],next:null,previous:null});
 render(<MemoryRouter initialEntries={['/content/noticias']}><Routes><Route path="/content/:slug" element={<Contents/>}/></Routes></MemoryRouter>);
 await screen.findByText('Noticia visible');fireEvent.change(screen.getByLabelText('Buscar'),{target:{value:'visible'}});await waitFor(()=>expect(api).toHaveBeenCalledWith(expect.stringContaining('search=visible')));
 fireEvent.click(screen.getByRole('switch'));await waitFor(()=>expect(api).toHaveBeenCalledWith('/api/admin/contents/9/visibility/',{method:'POST',body:{manual_active:false}}));
 fireEvent.click(screen.getByText('Eliminar'));expect(api).not.toHaveBeenCalledWith('/api/admin/contents/9/',{method:'DELETE'});fireEvent.click(screen.getByText('Confirmar eliminación'));await waitFor(()=>expect(api).toHaveBeenCalledWith('/api/admin/contents/9/',{method:'DELETE'}));
});
it('el diálogo cierra con Escape y devuelve el foco al origen',()=>{
 function Harness(){const [open,set]=useState(false);return <><button onClick={()=>set(true)}>Abrir</button>{open&&<Dialog title="Prueba" onClose={()=>set(false)}><input aria-label="Campo"/></Dialog>}</>;}
 render(<Harness/>);const trigger=screen.getByText('Abrir');trigger.focus();fireEvent.click(trigger);expect(screen.getByRole('dialog')).toBeInTheDocument();fireEvent.keyDown(document,{key:'Escape'});expect(screen.queryByRole('dialog')).not.toBeInTheDocument();expect(trigger).toHaveFocus();
});
it('la vista previa muestra texto sin interpretar HTML ni enlaces peligrosos',()=>{
 const {container}=render(<PublicationPreview content={{title:'<script>alert(1)</script>',description:'<img src=x onerror=alert(1)>',details:{access_url:'javascript:alert(1)'}}} category={metadata.categories[0]}/>);
 expect(container.querySelector('script')).toBeNull();expect(container.querySelector('img')).toBeNull();expect(screen.queryByText('Abrir enlace →')).not.toBeInTheDocument();expect(screen.getByText('<script>alert(1)</script>')).toBeInTheDocument();
});
