import React from 'react';
import {BrowserRouter,Routes,Route,Navigate,Outlet,Link} from 'react-router-dom';
import {useAuth} from '../contexts/Auth';
import Admin from '../layouts/Admin';
import Login from '../pages/Login';
import Dashboard from '../pages/Dashboard';
import Resource from '../pages/Resource';
import Settings from '../pages/Settings';
import Contents from '../pages/Contents';
import Approvals from '../pages/Approvals';
import Notifications from '../pages/Notifications';
import Statistics from '../pages/Statistics';
import Audit from '../pages/Audit';
import {resources} from '../pages/resources';
import {Loading} from '../components/Feedback';
function Protected({roles}){
  const {user,loading}=useAuth();
  if(loading)return <Loading/>;
  if(!user)return <Navigate to="/login" replace/>;
  if(roles&&!roles.includes(user.role_code))return <Navigate to="/denied" replace/>;
  return <Outlet/>;
}
export default function App(){return <BrowserRouter><Routes>
  <Route path="/login" element={<Login/>}/>
  <Route element={<Protected/>}><Route element={<Admin/>}>
    <Route index element={<Dashboard/>}/>
    <Route path="content/:slug" element={<Contents/>}/>
    <Route path="contents" element={<Contents/>}/>
    <Route path="contents/pending" element={<Contents fixedState="pending"/>}/>
    <Route path="contents/active" element={<Contents fixedVisibility="active"/>}/>
    <Route path="contents/hidden" element={<Contents fixedVisibility="hidden"/>}/>
    <Route path="notifications" element={<Notifications/>}/>
    <Route element={<Protected roles={['admin','superadmin']}/>}>
      {Object.entries(resources).filter(([key])=>key!=='audit').map(([key,config])=><Route key={key} path={key} element={<Resource key={key} config={config}/>}/>)}
      <Route path="settings" element={<Settings/>}/>
      <Route path="approvals" element={<Approvals/>}/>
      <Route path="statistics" element={<Statistics/>}/>
    </Route>
    <Route element={<Protected roles={['superadmin']}/>}><Route path="audit" element={<Audit/>}/></Route>
    <Route path="pending" element={<section className="card"><h1>Acerca de la demostración</h1><p>El portal local, el CMS y las estadísticas utilizan PostgreSQL. Las identidades son ficticias; AGA_AUTH, pfSense y SMTP institucional requieren integración autorizada.</p><a href="http://127.0.0.1:8010/portal/" target="_blank" rel="noopener noreferrer">Abrir portal cautivo local →</a></section>}/>
    <Route path="denied" element={<section className="card"><h1>Acceso denegado</h1><p>Tu rol no permite acceder a esta sección.</p><Link to="/">Volver al dashboard</Link></section>}/>
    <Route path="*" element={<section className="card"><h1>Página no encontrada</h1><Link to="/">Volver al dashboard</Link></section>}/>
  </Route></Route>
</Routes></BrowserRouter>}
