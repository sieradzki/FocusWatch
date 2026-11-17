require('esbuild').buildSync({entryPoints:['renderer.jsx'],bundle:true,platform:'browser',outfile:'report.js',minify:true,define:{'process.env.NODE_ENV':'"production"'}});
