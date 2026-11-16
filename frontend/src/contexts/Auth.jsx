import React, {createContext,useContext,useState,useEffect} from 'react';
import {api} from '../api/client';
const Auth = createContext();
export function AuthProvider({children}) {
  const [user,setUser]=useState(null), [loading,setLoading]=useState(true);
  useEffect(()=>{api('/api/me/').then(setUser).catch(()=>setUser(null)).finally(()=>setLoading(false));},[]);
  return <Auth.Provider value={{user,loading,login:async(email,password)=>setUser(await api('/auth/login',{method:'POST',body:{email,password}})),logout:async()=>{await api('/auth/logout',{method:'POST'});setUser(null);}}}>{children}</Auth.Provider>;
}
export const useAuth=()=>useContext(Auth);
