import React from 'react';
import {NavLink,Outlet,useLocation} from 'react-router-dom';
import {api} from '../api/client';
import {useAuth} from '../contexts/Auth';
import NotificationBell from '../components/NotificationBell';
export default function Admin(){
  const {user,logout}=useAuth(); const [error,setError]=React.useState('');
  const staff=['superadmin','admin'].includes(user.role_code);
  const [categories,setCategories]=React.useState([]);const location=useLocation();
  React.useEffect(()=>{api('/api/admin/content-metadata/').then(data=>setCategories(data.categories)).catch(e=>setError(e.message));},[location.pathname]);
  const links=[['/','◈','Dashboard'],...categories.map(c=>['/content/'+c.slug,'▤',c.name]),['/contents','≡','Todos los contenidos'],['/contents/pending','◷','Mis pendientes'],['/contents/active','✓','Activos en portal'],['/contents/hidden','◇','No visibles'],['/notifications','🔔','Notificaciones'],...(staff ? [['/approvals','✓','Cola de aprobación'],['/statistics','▥','Estadísticas'],['/users','♙','Usuarios'],['/roles','◇','Roles'],['/permissions','⌘','Permisos'],['/categories','▦','Categorías'],['/catalog-types','▤','Tipos de nomenclador'],['/catalog-items','≡','Nomencladores'],['/settings','⚙','Configuración']] : []),...(user.role_code==='superadmin' ? [['/audit','◷','Auditoría']] : []),['/pending','⋯','Acerca de la demostración']];
  return <div className="shell"><a className="skip" href="#main">Ir al contenido</a><aside><div className="brand">PortalInfo<span> UHO</span><small>Gestión de contenidos</small></div><div className="nav-caption">ADMINISTRACIÓN</div><nav>{links.map(([to,icon,title])=><NavLink key={to} to={to} end={to==='/'}><span aria-hidden="true">{icon}</span>{title}</NavLink>)}</nav><div className="sidebar-footer">Universidad de Holguín<br/>Demostración local · Entrega final</div></aside><div className="workspace"><header><span>Portal Cautivo Institucional</span><div className="identity"><NotificationBell/><span className="avatar">{user.email.slice(0,2).toUpperCase()}</span><div>{user.email}<small>{user.role_name} {user.demo && '· DEMO'}</small></div><button onClick={()=>logout().catch(e=>setError(e.message))}>Salir</button></div></header>{error && <p role="alert">{error}</p>}<main id="main"><Outlet/></main><footer>PortalInfo UHO · Dirección General de Informatización</footer></div></div>;
}
