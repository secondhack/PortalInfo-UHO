import {useCallback,useEffect,useRef} from 'react';

// Commit only the latest request for this mounted page; older searches may finish last.
export default function useRequestGuard(){
 const generation=useRef(0);
 useEffect(()=>()=>{generation.current++;},[]);
 return useCallback(()=>{const current=++generation.current;return()=>current===generation.current;},[]);
}
