"""A new Qt Quick/PySide UI, not the existing FocusWatch Widgets application."""
import sys
import os
from PySide6.QtCore import QObject, Slot, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine


class Bridge(QObject):
    @Slot(str)
    def report(self, value):
        print("DESKTOP_PROBE " + value, flush=True)


app = QGuiApplication(sys.argv)
bridge = Bridge()
engine = QQmlApplicationEngine()
engine.rootContext().setContextProperty("probe", bridge)
engine.rootContext().setContextProperty("segmentCount", int(os.environ.get("PROBE_SEGMENTS", "10000")))
engine.loadData('''
import QtQuick
import QtQuick.Window
Window {
  width: 1200; height: 700; visible: true; color: "#101820"
  title: "FocusWatch synthetic desktop probe"
  Text { x: 30; y: 25; text: "FocusWatch — synthetic report"; color: "#eef2f7"; font.pixelSize: 26 }
  Text { x: 30; y: 72; text: segmentCount + " synthetic segments · 10 lanes · no personal data"; color: "#aebdca" }
  Canvas {
    id: canvas; x:30; y:110; width:1000; height:500
    property var events: []
    property var durations: []
    property var frameTimes: []
    property int frame: -1
    property bool initialized: false
    property int columns: Math.ceil(segmentCount / 10)
    Component.onCompleted: {
      let data = [];
      for (let i = 0; i < segmentCount; i++) data.push({x:i%columns, lane:Math.floor(i/columns), category:i%4});
      events = data; requestPaint();
    }
    onPaint: {
      let start = Date.now();
      let ctx = getContext("2d");
      let colors = ['#70b7f7', '#78cfa0', '#e8be73', '#b79dec'];
      let cols = columns, segmentWidth = 1000/cols, drawFrame = Math.max(frame,0);
      ctx.fillStyle='#15202b'; ctx.fillRect(0,0,1000,500);
      for (let e of events) {
        ctx.fillStyle = colors[e.category];
        ctx.fillRect(((e.x + drawFrame) % cols)*segmentWidth, e.lane*48+4, segmentWidth, 40);
      }
      let duration = Date.now() - start;
      if (!initialized) {
        initialized = true;
        probe.report(JSON.stringify({event:'ready', events:events.length, renderer:'QtQuick.Canvas'}));
        idle.start();
      } else if (frame >= 0) {
        durations.push(duration); frameTimes.push(start);
        frame++;
        if (frame === 60) {
          animation.stop();
          probe.report(JSON.stringify({event:'done', draw_submission_ms:durations, frame_times_ms:frameTimes}));
        }
      }
    }
  }
  Timer { id:idle; interval:5000; onTriggered: {
    probe.report(JSON.stringify({event:'idle_end'})); canvas.frame=0; animation.start();
  } }
  Timer { id:animation; interval:16; repeat:true; onTriggered:canvas.requestPaint() }
}
'''.encode(), QUrl("file:///synthetic-probe.qml"))
if not engine.rootObjects():
    raise SystemExit(2)
sys.exit(app.exec())
