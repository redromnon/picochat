import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QTextEdit, QLabel, QFrame,
    QDoubleSpinBox, QFormLayout
)
from PySide6.QtCore import QThread, Signal, Slot
from PySide6.QtGui import QShortcut, QKeySequence, QColor, QTextCharFormat, QTextCursor
from qt_material import apply_stylesheet
from openai import OpenAI
import markdown

# Open AI-like LLM
class ChatWorker(QThread):
    finished = Signal(str)
    error = Signal(str)
    stream_chunk = Signal(str)

    def __init__(self, client, model, messages, params):
        super().__init__()
        self.client = client
        self.model = model
        self.messages = messages
        self.params = params

    def run(self):
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                stream=True,
                **self.params
            )
            full_response = ""
            for chunk in response:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    self.stream_chunk.emit(content)
            self.finished.emit(full_response)
        except Exception as e:
            self.error.emit(str(e))

# UI
class PicoChat(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PicoChat")
        self.setMinimumSize(900, 700)
        
        self.messages = []
        self.client = None

        self.user_color = "#FFBF00"
        self.llm_color = "#F5F5F5"
        
        self.init_ui()
        self.setup_shortcuts()

    def init_ui(self):

        # Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Top Bar (Endpoint)
        top_bar = QFrame()
        top_bar.setObjectName("TopBar")
        top_bar.setFixedHeight(50)
        top_bar_layout = QHBoxLayout(top_bar)
        
        self.endpoint_input = QLineEdit()
        self.endpoint_input.setPlaceholderText("LLM API Endpoint (e.g., http://localhost:11434/v1)")
        self.endpoint_input.setText("http://localhost:1234/v1") # Default common local endpoint
        
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("API Key (optional)")
        self.api_key_input.setEchoMode(QLineEdit.Password)
        
        top_bar_layout.addWidget(QLabel("Endpoint:"))
        top_bar_layout.addWidget(self.endpoint_input, 2)
        top_bar_layout.addWidget(QLabel("Key:"))
        top_bar_layout.addWidget(self.api_key_input, 1)
        
        main_layout.addWidget(top_bar)

        # Content Area (Sidebar + Chat)
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Sidebar
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(200)
        sidebar_layout = QVBoxLayout(sidebar)
        
        params_label = QLabel("HYPERPARAMETERS")
        params_label.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
        sidebar_layout.addWidget(params_label)
        
        form_layout = QFormLayout()
        
        self.temp_spin = QDoubleSpinBox()
        self.temp_spin.setRange(0.0, 2.0)
        self.temp_spin.setSingleStep(0.1)
        self.temp_spin.setValue(0.7)
        
        self.top_p_spin = QDoubleSpinBox()
        self.top_p_spin.setRange(0.0, 1.0)
        self.top_p_spin.setSingleStep(0.05)
        self.top_p_spin.setValue(0.95)

        form_layout.addRow("Temp:", self.temp_spin)
        form_layout.addRow("Top-P:", self.top_p_spin)
        
        sidebar_layout.addLayout(form_layout)
        sidebar_layout.addStretch()
        
        # Shortcut Information
        shortcut_info = QLabel("Ctrl+Shift+D\nto start fresh")
        shortcut_info.setStyleSheet("color: #888; font-size: 10px;")
        sidebar_layout.addWidget(shortcut_info)
        
        content_layout.addWidget(sidebar)

        # Chat Area
        chat_container = QWidget()
        chat_v_layout = QVBoxLayout(chat_container)
        
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setAcceptRichText(True)
        self.chat_display.setStyleSheet("""
            QTextEdit {
                selection-background-color: #FFBF00;
                selection-color: #FFFFFF;
            }
        """)
        
        input_container = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Enter your query...")
        self.input_field.setStyleSheet("""
            QLineEdit {
                selection-background-color: #FFBF00;
                selection-color: #FFFFFF;
            }
        """)
        self.input_field.returnPressed.connect(self.send_message)
        
        self.send_btn = QPushButton("Send", flat=True)
        self.send_btn.clicked.connect(self.send_message)
        
        input_container.addWidget(self.input_field)
        input_container.addWidget(self.send_btn)
        
        chat_v_layout.addWidget(self.chat_display)
        chat_v_layout.addLayout(input_container)
        
        content_layout.addWidget(chat_container)
        
        main_layout.addWidget(content_widget)

    def setup_shortcuts(self):
        self.clear_shortcut = QShortcut(QKeySequence("Ctrl+Shift+D"), self)
        self.clear_shortcut.activated.connect(self.new_session)

    # Clear and start new session
    def new_session(self):
        self.messages = []
        self.chat_display.clear()
        self.chat_display.append("<i>New session started. All history erased.</i> <br>")

    # Append message to chat display
    def append_message(self, role, text):

        name = "YOU"
        
        # formatted_text = f"<b><u>{name}</u></b>: {text}<br>"
        # self.chat_display.append(formatted_text)
        self.chat_display.append(f"> {text}<br>")


    # Send message to LLM
    def send_message(self):

        user_text = self.input_field.text().strip()
        if not user_text:
            return
            
        self.input_field.clear()
        self.append_message("user", user_text)
        self.messages.append({"role": "user", "content": user_text})
        
        # Prepare client
        endpoint = self.endpoint_input.text().strip()
        api_key = self.api_key_input.text().strip() or "none"
        
        try:
            self.client = OpenAI(base_url=endpoint, api_key=api_key)
            
            # Start worker
            params = {
                "temperature": self.temp_spin.value(),
                "top_p": self.top_p_spin.value(),
            }

            #self.chat_display.append(f"<b><u><span style='color: {self.llm_color}'>ASSISTANT:</span></u></b> ")
            self.chat_cursor_start = self.chat_display.textCursor().position()
            
            self.worker = ChatWorker(self.client, "default", self.messages, params)
            self.worker.stream_chunk.connect(self.on_stream_chunk)
            self.worker.finished.connect(self.on_worker_finished)
            self.worker.error.connect(self.on_worker_error)
            
            self.send_btn.setEnabled(False)
            self.worker.start()
            
        except Exception as e:
            self.chat_display.append(f"<i style='color: red'>Error: {str(e)}</i>")

    # Process stream chunks
    @Slot(str)
    def on_stream_chunk(self, chunk):
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        
        # Force white color for chunks
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(self.llm_color))
        cursor.setCharFormat(fmt)
        
        cursor.insertText(chunk)
        
        # Move cursor to end (auto scroll)
        self.chat_display.setTextCursor(cursor)
        self.chat_display.ensureCursorVisible()

    # After chunk streaming is over
    @Slot(str)
    def on_worker_finished(self, full_response):
        self.messages.append({"role": "assistant", "content": full_response})
        
        # Replace the streamed text with formatted markdown
        cursor = self.chat_display.textCursor()
        cursor.setPosition(self.chat_cursor_start, QTextCursor.MoveMode.MoveAnchor)
        cursor.movePosition(QTextCursor.MoveOperation.End, QTextCursor.MoveMode.KeepAnchor)
        cursor.removeSelectedText()

        # Convert LLM response to markdown format        
        html_content = markdown.markdown(full_response, extensions=['fenced_code', 'codehilite'])
        cursor.insertHtml(f"<div style='color: {self.llm_color}'>{html_content}</div><br>")
        
        # Move cursor to end (auto scroll)
        self.chat_display.setTextCursor(cursor)
        self.chat_display.ensureCursorVisible()
        
        self.send_btn.setEnabled(True)

    @Slot(str)
    def on_worker_error(self, error_msg):
        self.chat_display.append(f"<br><i style='color: red'>Error: {error_msg}</i>")
        self.send_btn.setEnabled(True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    extra = {
        'density_scale': '3',
        'font_family': 'Source Code Pro'
    }
    apply_stylesheet(app, theme='dark_amber.xml', extra=extra)
    
    window = PicoChat()
    window.show()
    window.input_field.setFocus()
    sys.exit(app.exec())
