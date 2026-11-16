import React,{useState} from 'react';
import {download} from '../api/client';
export default function ReportButtons({kind,query,onError}){
 const [busy,setBusy]=useState(false);
 const save=async fmt=>{if(busy)return;setBusy(true);try{await download(`/api/admin/reports/${kind}/?${query}&file_format=${fmt}`);}catch(e){onError(e.message);}finally{setBusy(false);}};
 return <div className="row-actions"><button disabled={busy} onClick={()=>save('csv')}>Descargar CSV</button><button disabled={busy} onClick={()=>save('pdf')}>Descargar PDF</button></div>;
}
