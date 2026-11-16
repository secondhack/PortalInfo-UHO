import React from 'react';
export function Feedback({error,message}) {return error ? <div role="alert" className="alert error">{error}</div> : message ? <div role="status" className="alert success">{message}</div> : null;}
export function Loading(){return <p role="status" className="loading">Cargando información…</p>;}
