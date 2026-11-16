import React,{useState,useEffect} from 'react';
import {api,all} from '../api/client';
import {Feedback,Loading} from '../components/Feedback';
import {Dialog,Pagination,formatDate} from '../components/ContentUI';
import PeriodFilters,{initialPeriod,periodQuery} from '../components/PeriodFilters';
import ReportButtons from '../components/ReportButtons';
import useRequestGuard from '../components/useRequestGuard';
export default function Audit(){
 const beginRequest=useRequestGuard();
 const [data,setData]=useState(null),[period,setPeriod]=useState(initialPeriod),[users,setUsers]=useState([]),[filters,setFilters]=useState({actor:'',action:'',entity:'',search:''}),[page,setPage]=useState(1),[detail,setDetail]=useState(null),[error,setError]=useState('');
 const query=periodQuery(period,{page,...Object.fromEntries(Object.entries(filters).filter(([,v])=>v!==''))});
 useEffect(()=>{all('/api/admin/users/').then(setUsers).catch(e=>setError(e.message));},[]);
 useEffect(()=>{const current=beginRequest();if(period.period==='custom'&&(!period.date_from||!period.date_to))return;api('/api/admin/audit/?'+query).then(value=>{if(current()){setData(value);setError('');}}).catch(e=>{if(current())setError(e.message);});},[query]);
 const set=(key,value)=>{setPage(1);setFilters({...filters,[key]:value});};
 return <><h1>Auditoría administrativa</h1><p className="subtitle">Solo lectura · sin eliminación manual desde la API</p><PeriodFilters value={period} onChange={v=>{setPeriod(v);setPage(1);}} hideScope/><Feedback error={error}/><section className="card"><div className="content-filters"><label>Usuario actor<select value={filters.actor} onChange={e=>set('actor',e.target.value)}><option value="">Todos</option>{users.map(u=><option key={u.id} value={u.id}>{u.email}</option>)}</select></label><label>Acción exacta<input value={filters.action} onChange={e=>set('action',e.target.value)} placeholder="content.approve"/></label><label>Entidad<input value={filters.entity} onChange={e=>set('entity',e.target.value)} placeholder="content, user, grant…"/></label><label>Buscar<input value={filters.search} onChange={e=>set('search',e.target.value)}/></label></div><ReportButtons kind="audit" query={query} onError={setError}/>{!data?(!error&&<Loading/>):<><div className="table-wrap"><table><thead><tr>{['Fecha','Actor ID','Acción','Entidad / recurso','IP','Detalle'].map(x=><th key={x}>{x}</th>)}</tr></thead><tbody>{data.results.map(row=><tr key={row.id}><td>{formatDate(row.created_at)}</td><td>{row.actor??'Sistema'}</td><td>{row.action}</td><td>{row.entity} / {row.resource}</td><td>{row.ip||'—'}</td><td><button onClick={()=>setDetail(row)}>Ver resumen antes/después</button></td></tr>)}</tbody></table>{!data.results.length&&<p className="empty">No hay eventos con estos filtros.</p>}</div><Pagination data={data} page={page} onChange={setPage}/></>}</section>{detail&&<Dialog wide title="Detalle de auditoría" onClose={()=>setDetail(null)}><pre className="json-detail">{JSON.stringify(detail,null,2)}</pre></Dialog>}</>;
}
