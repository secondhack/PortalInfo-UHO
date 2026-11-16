import {defineConfig} from '@playwright/test';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {existsSync,mkdirSync} from 'node:fs';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
process.env.PLAYWRIGHT_BROWSERS_PATH=path.join(root,'.local/ms-playwright');
const temporary=path.join(root,'.local/browser-temp');mkdirSync(temporary,{recursive:true});process.env.TEMP=temporary;process.env.TMP=temporary;
const executable=[process.env.PORTAL_BROWSER_EXECUTABLE,'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe','C:/Program Files/Google/Chrome/Application/chrome.exe'].find(value=>value&&existsSync(value));
export default defineConfig({testDir:'./e2e',workers:1,retries:0,timeout:90000,fullyParallel:false,
 outputDir:path.join(root,'.local/browser-results'),reporter:[['list'],['json',{outputFile:path.join(root,'docs/pruebas/NAVEGADOR_FINAL.json')}]],
 use:{baseURL:'http://127.0.0.1:5174',channel:executable?undefined:'chromium',headless:true,trace:'off',video:'off',screenshot:'off',
  launchOptions:{executablePath:executable,args:['--disable-background-networking','--disable-component-update','--disable-sync','--no-first-run','--no-default-browser-check']}}});
