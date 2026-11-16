import React,{useEffect,useRef} from 'react';
import {Chart,BarController,LineController,DoughnutController,BarElement,LineElement,PointElement,ArcElement,CategoryScale,LinearScale,Tooltip,Legend} from 'chart.js';
Chart.register(BarController,LineController,DoughnutController,BarElement,LineElement,PointElement,ArcElement,CategoryScale,LinearScale,Tooltip,Legend);

export default function MetricChart({title,rows=[],labelKey='label',valueKey='count',type='bar'}){
 const canvas=useRef();
 useEffect(()=>{
  if(!canvas.current||!rows.some(row=>Number(row[valueKey])>0))return;
  const chart=new Chart(canvas.current,{type,data:{labels:rows.map(r=>String(r[labelKey]??'Sin identificar')),datasets:[{label:title,data:rows.map(r=>Number(r[valueKey])||0),backgroundColor:['#1565c0','#ff8b24','#288f6b','#7560b5','#44a3b8','#bf5276'],borderColor:'#1565c0',borderWidth:type==='line'?2:0,tension:.15}]},options:{responsive:true,maintainAspectRatio:false,animation:false,plugins:{legend:{display:type==='doughnut'}},scales:type==='doughnut'?undefined:{y:{beginAtZero:true,ticks:{precision:0}}}}});
  return()=>chart.destroy();
 },[rows,title,labelKey,valueKey,type]);
 const empty=!rows.some(row=>Number(row[valueKey])>0);
 return <section className="card metric-chart"><h2>{title}</h2>{empty?<p className="empty">No hay registros en el período seleccionado.</p>:<><div className="chart-canvas"><canvas ref={canvas} role="img" aria-label={title}/></div><details><summary>Consultar datos en tabla</summary><table><thead><tr><th>Grupo</th><th>Valor</th></tr></thead><tbody>{rows.map((row,i)=><tr key={i}><td>{String(row[labelKey]??'Sin identificar')}</td><td>{row[valueKey]}</td></tr>)}</tbody></table></details></>}</section>;
}
