import React,{useRef,useState} from 'react';
import {api} from '../api/client';
import {Feedback} from '../components/Feedback';
import {CharacterField,PublicationPreview,validityOptions,Status} from '../components/ContentUI';
import SurveyEditor from '../components/SurveyEditor';

function localDate(value){if(!value)return '';const date=new Date(value);return new Date(date.getTime()-date.getTimezoneOffset()*60000).toISOString().slice(0,16);}
export default function ContentEditor({item,metadata,initialCategory,onCancel,onSaved}){
 const [values,setValues]=useState(()=>({...item,category:item?.category||initialCategory||metadata.categories.find(c=>c.permissions.includes('create'))?.id,title:item?.title||'',description:item?.description||'',validity:item?.validity||'default',manual_active:item?.manual_active??true,extra_fields:item?.extra_fields||{},details:item?.details||{},starts_at:localDate(item?.starts_at),ends_at:localDate(item?.ends_at)}));
 const [error,setError]=useState(''),[busy,setBusy]=useState(false),[preview,setPreview]=useState(false);const lock=useRef(false);
 const category=metadata.categories.find(c=>c.id===Number(values.category)),kind=category?.content_type;
 const set=(key,value)=>setValues(v=>({...v,[key]:value}));
 const detail=(key,value)=>setValues(v=>({...v,details:{...v.details,[key]:value}}));
 const save=async action=>{
  if(lock.current)return;lock.current=true;setBusy(true);setError('');
  try{
   if(!category)throw new Error('Seleccione una categoría.');
   const details={...values.details};delete details.area_name;delete details.external;
   if(details.questions)details.questions=details.questions.map(q=>({text:q.text,kind:q.kind,required:q.required,options:q.options.map(o=>({text:o.text}))}));
   if(kind==='survey'&&!details.external_url&&!details.questions?.length)throw new Error('Añada al menos una pregunta a la encuesta interna.');
   if(details.questions?.length>metadata.survey.max_questions)throw new Error('Se supera el límite de preguntas.');
   if(details.questions?.some(q=>q.kind!=='open'&&(q.options.length<2||q.options.length>metadata.survey.max_options)))throw new Error('Revise la cantidad de opciones de cada pregunta.');
   let body={category:Number(values.category),title:values.title,description:values.description,manual_active:values.manual_active,extra_fields:values.extra_fields,details};
   // Unchanged validity preserves the original dates instead of extending publication on every save.
   if(!item||values.validity!==item.validity||values.validity==='custom'){
    body.validity=values.validity;
    if(values.validity==='custom'){
     if(!values.starts_at||!values.ends_at||new Date(values.ends_at)<=new Date(values.starts_at))throw new Error('El rango requiere inicio y fin, con fin posterior al inicio.');
     body.starts_at=new Date(values.starts_at).toISOString();body.ends_at=new Date(values.ends_at).toISOString();
    }
   }
   const saved=await api('/api/admin/contents/'+(item?item.id+'/':''),{method:item?'PATCH':'POST',body});
   if(action==='submit'){
    try{const result=await api(`/api/admin/contents/${saved.id}/submit/`,{method:'POST'});onSaved(result.warning||'Contenido enviado para aprobación.');}
    catch(e){onSaved(`El contenido se guardó como revisión ${saved.revision}, pero no se pudo enviar: ${e.message}`);}
   }else onSaved('Contenido guardado.');
  }catch(e){setError(e.message);}finally{lock.current=false;setBusy(false);}
 };
 return <form onSubmit={e=>{e.preventDefault();save(e.nativeEvent.submitter?.value||'draft');}}><Feedback error={error}/><div className="editor-summary"><Status value={item?.state||'draft'}/>{item?.has_published_version&&<p>Existe una versión aprobada. Los cambios del Gestor esperan revisión; la publicación anterior se conserva.</p>}</div><label>Categoría<select required value={values.category||''} onChange={e=>{set('category',Number(e.target.value));set('details',{});set('extra_fields',{});}}>{metadata.categories.filter(c=>(!item||c.content_type===item.content_type)&&c.permissions.includes(item?'edit':'create')).map(c=><option key={c.id} value={c.id}>{c.name}</option>)}</select></label><CharacterField label={kind==='event'?'Nombre del evento':kind==='service'?'Nombre del servicio':'Título'} required value={values.title} limit={category?.title_limit} onChange={v=>set('title',v)}/><CharacterField label="Descripción / contenido" required multiline rows={4} value={values.description} limit={category?.description_limit} onChange={v=>set('description',v)}/>{['news','event','service'].includes(kind)&&<label>Área responsable<select required value={values.details.area||''} onChange={e=>detail('area',Number(e.target.value))}><option value="">Seleccionar área…</option>{metadata.areas.map(a=><option key={a.id} value={a.id}>{a.name}</option>)}</select></label>}{kind==='news'&&<label>Enlace externo (opcional)<input type="url" pattern="https?://.*" value={values.details.external_url||''} onChange={e=>detail('external_url',e.target.value)}/></label>}{kind==='event'&&<><label>Fecha del evento (zona horaria del navegador)<input type="datetime-local" required value={localDate(values.details.event_at)} onChange={e=>detail('event_at',e.target.value?new Date(e.target.value).toISOString():'')}/></label><label>Datos de contacto<input required maxLength={250} value={values.details.contact||''} onChange={e=>detail('contact',e.target.value)}/></label><label>Enlace de convocatoria (opcional)<input type="url" pattern="https?://.*" value={values.details.invitation_url||''} onChange={e=>detail('invitation_url',e.target.value)}/></label></>}{kind==='service'&&<><label>Enlace de acceso<input type="url" pattern="https?://.*" required value={values.details.access_url||''} onChange={e=>detail('access_url',e.target.value)}/></label><label>Tipo de servicio (opcional)<select value={values.details.service_type||''} onChange={e=>detail('service_type',e.target.value?Number(e.target.value):null)}><option value="">Sin especificar</option>{metadata.service_types.map(t=><option key={t.id} value={t.id}>{t.name}</option>)}</select></label></>}{kind==='survey'&&<SurveyEditor value={values.details} onChange={v=>set('details',v)} config={metadata.survey}/>}{(category?.required_fields||[]).map(field=><CharacterField key={field} label={field} required value={values.extra_fields[field]||''} limit={category.description_limit} onChange={v=>set('extra_fields',{...values.extra_fields,[field]:v})}/>)}<div className="form-grid"><label>Vigencia<select value={values.validity} onChange={e=>set('validity',e.target.value)}>{validityOptions.map(([value,label])=><option key={value} value={value}>{label}</option>)}</select></label><label className="inline-label"><input type="checkbox" checked={values.manual_active} onChange={e=>set('manual_active',e.target.checked)}/>Visibilidad manual habilitada</label></div>{values.validity==='custom'&&<div className="form-grid"><label>Inicio de visibilidad<input required type="datetime-local" value={values.starts_at} onChange={e=>set('starts_at',e.target.value)}/></label><label>Fin de visibilidad<input required type="datetime-local" min={values.starts_at} value={values.ends_at} onChange={e=>set('ends_at',e.target.value)}/></label></div>}<p className="hint">Los rangos se introducen en la zona del navegador. Hoy, semana y mes se calculan en el servidor con America/Havana.</p><button type="button" onClick={()=>setPreview(!preview)}>{preview?'Cerrar vista previa':'Vista previa'}</button>{preview&&<PublicationPreview content={values} category={category} areas={metadata.areas}/>}<div className="form-actions"><button type="button" onClick={onCancel} disabled={busy}>Cancelar</button><button disabled={busy} type="submit" value="draft">{busy?'Guardando…':item?'Guardar cambios':'Guardar borrador'}</button>{category?.permissions.includes('submit')&&<button className="primary" disabled={busy} type="submit" value="submit">Enviar para aprobación</button>}</div></form>;
}
