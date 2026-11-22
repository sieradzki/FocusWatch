// Assemble an offline runtime from an already built report and native agent.
import {cp, mkdir, copyFile, rename, stat, access, writeFile} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const [agent, destination] = process.argv.slice(2);
if (!agent || !destination) throw Error('usage: node scripts/package.mjs <compiled agent> <new directory>');
const root = fileURLToPath(new URL('../', import.meta.url));
const desktop = path.join(root, 'desktop');
const win = process.platform === 'win32';
const executable = win ? 'electron.exe' : 'electron';
const runtime = path.join(desktop, 'node_modules', 'electron', 'dist');
await Promise.all([agent, path.join(runtime,executable), path.join(desktop,'dist','main.cjs')].map(p=>access(p)));
await mkdir(destination); // Refuse to overwrite an existing installation.
await cp(runtime,path.join(destination,'report'),{recursive:true});
await rename(path.join(destination,'report',executable),
  path.join(destination,'report',win?'FocusWatch-Report.exe':'focuswatch-report'));
const app = path.join(destination,'report','resources','app');
await mkdir(app);
await cp(path.join(desktop,'dist'),path.join(app,'dist'),{recursive:true});
await writeFile(path.join(app,'package.json'),JSON.stringify({name:'focuswatch-report',main:'dist/main.cjs',version:'0.1.0'}));
const notices=path.join(app,'licenses');
await mkdir(notices);
await copyFile(path.join(root,'LICENSE'),path.join(notices,'FocusWatch-LICENSE'));
for(const name of ['react','react-dom','scheduler']) {
  await copyFile(path.join(desktop,'node_modules',name,'LICENSE'),path.join(notices,name+'-LICENSE'));
}
await copyFile(agent,path.join(destination,win?'focuswatch-agent.exe':'focuswatch-agent'));
if(win) await copyFile(path.join(root,'scripts','Install-P0.ps1'),path.join(destination,'Install-P0.ps1'));
console.log('Packaged '+(await stat(agent)).size+' byte agent and report in '+destination);
