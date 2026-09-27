// Synthetic desktop-runtime probe. Contains no FocusWatch or user data.
import React, {useEffect, useRef, useState} from 'react';
import {createRoot} from 'react-dom/client';

function report(value) {
  if (window.desktopProbe) window.desktopProbe.report(value);
  else window.__TAURI__.core.invoke('report', {payload: JSON.stringify(value)});
}

function App() {
  const ref = useRef(null);
  const [count, setCount] = useState(0);
  useEffect(() => {
    async function run() {
    const size = await (window.desktopProbe ? window.desktopProbe.config() : window.__TAURI__.core.invoke('probe_config'));
    setCount(size);
    const columns = Math.ceil(size / 10), width = 1000 / columns;
    const events = Array.from({length: size}, (_, i) => ({
      x: i % columns, lane: Math.floor(i / columns), category: i % 4,
    }));
    const colors = ['#70b7f7', '#78cfa0', '#e8be73', '#b79dec'];
    const ctx = ref.current.getContext('2d');
    const durations = [], frameTimes = [];
    function draw(frame) {
      const start = Date.now();
      ctx.fillStyle = '#15202b'; ctx.fillRect(0, 0, 1000, 500);
      for (const e of events) {
        ctx.fillStyle = colors[e.category];
        ctx.fillRect(((e.x + frame) % columns) * width, e.lane * 48 + 4, width, 40);
      }
      return Date.now() - start;
    }
    requestAnimationFrame(() => {
      draw(0);
      report({event:'ready', events:events.length, renderer:'canvas2d', react:React.version});
      setTimeout(() => {
        report({event:'idle_end'});
        let frame = 0;
        function tick() {
          frameTimes.push(Date.now()); durations.push(draw(frame));
          if (++frame < 60) requestAnimationFrame(tick);
          else report({event:'done', draw_submission_ms:durations, frame_times_ms:frameTimes});
        }
        requestAnimationFrame(tick);
      }, 5000);
    });
    }
    run();
  }, []);
  return <main><h1>FocusWatch — synthetic report</h1>
    <p>{count.toLocaleString()} synthetic segments · 10 lanes · no personal data</p>
    <canvas ref={ref} width="1000" height="500" />
  </main>;
}
createRoot(document.getElementById('root')).render(<App/>);
