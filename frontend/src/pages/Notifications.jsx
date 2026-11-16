import React,{useEffect,useState} from 'react';
import {Link} from 'react-router-dom';
import {api} from '../api/client';
import {Feedback,Loading} from '../components/Feedback';
import {Pagination,formatDate} from '../components/ContentUI';
import useRequestGuard from '../components/useRequestGuard';
export default function Notifications(){
 const beginRequest=useRequestGuard();
 const [data,setData]=useState(null),[page,setPage]=useState(1),[unread,setUnread]=useState(false),[error,setError]=useState('');
 const load=()=>{const current=beginRequest();return api(`/api/admin/notifications/?page=${page}${unread?'&read=false':''}`).then(value=>{if(current()){setData(value);setError('');}}).catch(e=>{if(current())setError(e.message);});};
 useEffect(()=>{load();},[page,unread]);
 const mark=async path=>{try{await api(path,{method:'POST'});await load();}catch(e){setError(e.message);}};
 return <><h1>Mis notificaciones</h1><Feedback error={error}/><section className="card"><label className="inline-label"><input type="checkbox" checked={unread} onChange={e=>{setPage(1);setUnread(e.target.checked);}}/>Solo no leídas</label><button onClick={()=>mark('/api/admin/notifications/mark_all_read/')}>Marcar todas como leídas</button>{!data?(!error&&<Loading/>):<>{data.results.map(n=><article className={n.read?'notification-read':'notification-unread'} key={n.id}><h2>{n.title||n.kind}</h2>{n.demo&&<span className="badge">DEMO</span>}<p>{n.message}</p><p>{formatDate(n.created_at)} · {n.kind} · Correo: {n.mail_state}</p>{n.read_at&&<small>Leída: {formatDate(n.read_at)}</small>}{n.resource_id&&<Link to={`/contents?content=${n.resource_id}`}>Ver contenido →</Link>}{!n.read&&<button onClick={()=>mark(`/api/admin/notifications/${n.id}/mark_read/`)}>Marcar como leída</button>}</article>)}{!data.results.length&&<p className="empty">No hay notificaciones.</p>}<Pagination data={data} page={page} onChange={setPage}/></>}</section></>;
}
