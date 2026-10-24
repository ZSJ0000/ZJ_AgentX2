try:
 from PySide2.QtCore import QUrl
 from PySide2.QtWidgets import QApplication,QCheckBox,QLabel,QMainWindow,QPushButton,QTextEdit,QVBoxLayout,QWidget
 from PySide2.QtWebEngineWidgets import QWebEngineView
 PYSIDE2_AVAILABLE=True
except ImportError:PYSIDE2_AVAILABLE=False
DARK='QWidget{background:#202124;color:#eee} QPushButton{padding:7px;background:#3c4043;color:white} QTextEdit{background:#303134;color:#eee}'
LIGHT='QWidget{background:#f4f5f7;color:#202124} QPushButton{padding:7px;background:#e1e5ea;color:#202124} QTextEdit{background:white;color:#202124}'
if PYSIDE2_AVAILABLE:
 class MainWindow(QMainWindow):
  def __init__(self,web_url='http://127.0.0.1:8765',web_server=None):
   super().__init__(); self.web_server=web_server; self.dark=True; self.setWindowTitle('ZJ AgentX2'); self.resize(1100,700); self.status=QLabel('Web 服务未启动'); self.log=QTextEdit(); self.log.setReadOnly(True); self.theme=QCheckBox('浅色主题'); self.theme.stateChanged.connect(self.toggle); self.start=QPushButton('启动 Web'); self.stop=QPushButton('停止 Web'); self.open=QPushButton('打开 Web 页面'); self.start.clicked.connect(self.start_web); self.stop.clicked.connect(self.stop_web); self.open.clicked.connect(lambda:self.browser.setUrl(QUrl(web_url))); self.browser=QWebEngineView(); self.browser.setUrl(QUrl(web_url)); box=QVBoxLayout(); [box.addWidget(x) for x in (self.status,self.theme,self.start,self.stop,self.open,self.browser,self.log)]; root=QWidget(); root.setLayout(box); self.setCentralWidget(root); self.apply()
  def apply(self):self.setStyleSheet(DARK if self.dark else LIGHT)
  def toggle(self,s):self.dark=not bool(s); self.apply()
  def start_web(self):
   if self.web_server:self.status.setText('Web 已启动: '+str(self.web_server.start())); self.log.append('Web server started')
  def stop_web(self):
   if self.web_server:self.web_server.stop(); self.status.setText('Web 已停止'); self.log.append('Web server stopped')
def run_gui(web_server=None):
 if not PYSIDE2_AVAILABLE:raise RuntimeError('PySide2 is not installed; install PySide2 to run desktop GUI')
 app=QApplication.instance() or QApplication([]); w=MainWindow(web_server=web_server); w.show(); return app.exec_()
