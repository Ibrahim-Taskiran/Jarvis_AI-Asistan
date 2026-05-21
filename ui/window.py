"""
ui/window.py - JARVIS PyQt6 Modern HUD Arayüzü
Sürekli üstte duran, modern neon yeşil-mavi renk şemasına sahip,
çerçevesiz, sürükleyebilir ve çift modlu (ses + metin) durum penceresi.
"""

import sys
import math
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QMenu, QSizePolicy
)
from PyQt6.QtCore import Qt, QPoint, QPointF, QRectF, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QPainter, QColor, QPen, QBrush, QFont

class JarvisAnimationWidget(QWidget):
    """JARVIS Dönen Neon Halka Animasyonu."""
    
    sig_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(130, 130)
        
        # Animasyon durumları: "listening", "processing", "speaking", "sleeping", "error"
        self.state = "listening"
        self.angle_inner = 0.0
        self.angle_outer = 0.0
        self.pulse_time = 0.0
        self.pulse_scale = 1.0
        
        # Zamanlayıcıyı başlat (60 FPS için ~16ms)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(16)

    def set_state(self, state: str):
        """Animasyon durumunu günceller."""
        state = state.lower()
        if state in ["listening", "processing", "speaking", "sleeping", "error"]:
            self.state = state
            
    def update_animation(self):
        # Duruma göre dönüş hızları ve pulse güncellemeleri
        if self.state == "listening":
            self.angle_inner += 1.8   # Saat yönünde yavaş dönüş
            self.angle_outer -= 1.2   # Ters saat yönünde yavaş dönüş
            self.pulse_time += 0.05
            self.pulse_scale = 1.0 + 0.1 * math.sin(self.pulse_time) # Yavaş nefes alma efekti
        elif self.state == "processing":
            self.angle_inner += 5.5   # Hızlı dönüş
            self.angle_outer -= 4.2
            self.pulse_time += 0.22
            self.pulse_scale = 1.0 + 0.25 * abs(math.sin(self.pulse_time)) # Hızlı nabız efekti
        elif self.state == "speaking":
            self.angle_inner += 3.2
            self.angle_outer -= 2.2
            self.pulse_time += 0.16
            self.pulse_scale = 1.05 + 0.28 * abs(math.sin(self.pulse_time)) # Konuşurken dalgalanma efekti
        elif self.state == "sleeping":
            self.angle_inner += 0.3
            self.angle_outer -= 0.2
            self.pulse_time += 0.015
            self.pulse_scale = 0.95 + 0.04 * math.sin(self.pulse_time)
        elif self.state == "error":
            self.angle_inner += 0.5
            self.angle_outer -= 0.5
            self.pulse_scale = 1.0
            
        self.update() # Repaint tetikle

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        center_x = self.width() / 2.0
        center_y = self.height() / 2.0
        
        # Renk paleti
        color_green = QColor("#00ff88")
        color_blue = QColor("#00b0ff")
        color_error = QColor("#ff3333")
        color_gray = QColor("#5c6b73")
        
        main_color = color_green
        if self.state == "sleeping":
            main_color = color_gray
        elif self.state == "error":
            main_color = color_error
        elif self.state == "processing":
            main_color = color_blue
            
        # 1. Merkez Noktası ve Glow Efekti
        # Dış Glow (Geniş ve şeffaf)
        glow_radius_outer = 13.0 * self.pulse_scale
        glow_color_outer = QColor(main_color)
        glow_color_outer.setAlpha(40)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(glow_color_outer))
        painter.drawEllipse(QPointF(center_x, center_y), glow_radius_outer + 8.0, glow_radius_outer + 8.0)
        
        # İç Glow (Dar ve yarı şeffaf)
        glow_radius_inner = 11.0 * self.pulse_scale
        glow_color_inner = QColor(main_color)
        glow_color_inner.setAlpha(90)
        painter.setBrush(QBrush(glow_color_inner))
        painter.drawEllipse(QPointF(center_x, center_y), glow_radius_inner + 3.0, glow_radius_inner + 3.0)
        
        # Merkez Daire (Opak çekirdek)
        painter.setBrush(QBrush(main_color))
        painter.drawEllipse(QPointF(center_x, center_y), glow_radius_inner, glow_radius_inner)
        
        # Uyku veya hata modunda halkaları sönük çiz
        if self.state == "sleeping":
            pen = QPen(QColor("#1f2733"), 2)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(QPointF(center_x, center_y), 32.0, 32.0)
            return
            
        # 2. İç Dönen Neon Halka (Mavi Arc)
        pen_inner = QPen(color_blue, 2.5)
        painter.setPen(pen_inner)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        inner_radius = 30.0
        rect_inner_f = QRectF(center_x - inner_radius, center_y - inner_radius, inner_radius * 2, inner_radius * 2)
        start_angle_inner = int(self.angle_inner * 16)
        span_angle_inner = int(90 * 16) # 90 derecelik yay
        painter.drawArc(rect_inner_f, start_angle_inner, span_angle_inner)
        
        # 3. Dış Dönen Neon Halka (Yeşil Arc)
        pen_outer = QPen(color_green, 2.5)
        painter.setPen(pen_outer)
        outer_radius = 42.0
        rect_outer_f = QRectF(center_x - outer_radius, center_y - outer_radius, outer_radius * 2, outer_radius * 2)
        start_angle_outer = int(self.angle_outer * 16)
        span_angle_outer = int(120 * 16) # 120 derecelik yay
        painter.drawArc(rect_outer_f, start_angle_outer, span_angle_outer)
        
        # 4. Halka Başlarındaki Parlak Öncü Noktalar (Lead Dots)
        # İç halka ucu
        rad_inner = math.radians(self.angle_inner + 90)
        dot_inner_x = center_x + inner_radius * math.cos(rad_inner)
        dot_inner_y = center_y - inner_radius * math.sin(rad_inner)
        painter.setBrush(QBrush(color_blue))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(dot_inner_x, dot_inner_y), 3.5, 3.5)
        
        # Dış halka ucu
        rad_outer = math.radians(self.angle_outer + 120)
        dot_outer_x = center_x + outer_radius * math.cos(rad_outer)
        dot_outer_y = center_y - outer_radius * math.sin(rad_outer)
        painter.setBrush(QBrush(color_green))
        painter.drawEllipse(QPointF(dot_outer_x, dot_outer_y), 4.2, 4.2)

    def mousePressEvent(self, event):
        """Merkez animasyona tıklanınca tıklama sinyalini tetikler."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.sig_clicked.emit()


class JarvisWindow(QWidget):
    """JARVIS Modern Masaüstü HUD Arayüzü."""
    
    sig_sleep_requested = pyqtSignal()
    sig_clear_mem_requested = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        # Pencereyi çerçevesiz, şeffaf arka planlı ve her zaman üstte ayarla
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Sabit pencere boyutu (HUD tasarımına tam uyan dikey düzen)
        self.setFixedSize(340, 470)

        # Pozisyon: Sağ üst köşeye sabitle
        app = QApplication.instance()
        if app:
            screen = app.primaryScreen().geometry()
            self.move(screen.width() - 360, 50)
        
        # Ana Layout (Transparan pencere içindeki gerçek HUD çerçevesini tutacak)
        window_layout = QVBoxLayout()
        window_layout.setContentsMargins(0, 0, 0, 0)
        
        # ── ANA ÇERÇEVE CONTAINER'I ──────────────────────────────────────────
        self.main_container = QWidget(self)
        self.main_container.setObjectName("mainContainer")
        self.update_border("#13382c") # Başlangıçta neon yeşil temalı kenarlık
        
        container_layout = QVBoxLayout(self.main_container)
        container_layout.setContentsMargins(20, 20, 20, 20)
        container_layout.setSpacing(15)
        
        # 1. HEADER (Başlık ve Versiyon)
        header_layout = QHBoxLayout()
        lbl_title = QLabel("J A R V I S")
        lbl_title.setStyleSheet("font-family: 'Segoe UI', Arial; font-size: 16px; font-weight: bold; color: #00ff88; letter-spacing: 5px;")
        
        lbl_version = QLabel("v2.0")
        lbl_version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_version.setStyleSheet(
            "border: 1px solid #1c2e26;"
            "border-radius: 8px;"
            "padding: 3px 12px;"
            "font-size: 10px;"
            "font-weight: bold;"
            "color: #8da295;"
            "background-color: #0e141a;"
        )
        
        header_layout.addWidget(lbl_title)
        header_layout.addStretch()
        header_layout.addWidget(lbl_version)
        
        # 2. ANIMASYON VE DURUM BİLGİSİ
        anim_container = QVBoxLayout()
        anim_container.setSpacing(8)
        anim_container.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.anim_widget = JarvisAnimationWidget(self)
        self.anim_widget.sig_clicked.connect(self.sig_sleep_requested.emit)
        
        self.lbl_status = QLabel("DİNLENİYOR")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_status.setStyleSheet("font-size: 11px; font-weight: bold; color: #00ff88; letter-spacing: 3px;")
        
        anim_container.addWidget(self.anim_widget, 0, Qt.AlignmentFlag.AlignCenter)
        anim_container.addWidget(self.lbl_status)
        
        # 3. SON KOMUT / SONUÇ KART GÖRÜNÜMÜ
        self.card_widget = QWidget()
        self.card_widget.setStyleSheet(
            "background-color: #0d1117;"
            "border: 1px solid #1a2332;"
            "border-radius: 12px;"
        )
        card_layout = QVBoxLayout(self.card_widget)
        card_layout.setContentsMargins(15, 12, 15, 12)
        card_layout.setSpacing(6)
        
        # Komut Satırı
        cmd_row = QHBoxLayout()
        lbl_cmd_title = QLabel("Son komut")
        lbl_cmd_title.setStyleSheet("font-size: 10px; color: #5c6b73; font-weight: bold;")
        self.lbl_last_command = QLabel("-")
        self.lbl_last_command.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.lbl_last_command.setStyleSheet("font-size: 11px; color: #ffffff; font-weight: bold;")
        cmd_row.addWidget(lbl_cmd_title)
        cmd_row.addStretch()
        cmd_row.addWidget(self.lbl_last_command)
        
        # Durum Çıktı Satırı
        self.lbl_result = QLabel("-")
        self.lbl_result.setWordWrap(True)
        self.lbl_result.setStyleSheet("font-size: 11px; color: #00ff88; font-weight: bold;")
        
        # Model & Zaman Çıktı Satırı
        self.lbl_model_info = QLabel("Llama 3B · 0.0sn")
        self.lbl_model_info.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.lbl_model_info.setStyleSheet("font-size: 9px; color: #4b5866; font-weight: bold;")
        
        card_layout.addLayout(cmd_row)
        card_layout.addWidget(self.lbl_result)
        card_layout.addWidget(self.lbl_model_info)
        
        # 4. YAZILI PROMPT GİRİŞ SATIRI (QLineEdit + Gönder butonu)
        input_layout = QHBoxLayout()
        input_layout.setSpacing(8)
        
        self.input_command = QLineEdit()
        self.input_command.setPlaceholderText("komut yaz...")
        self.input_command.setStyleSheet(
            "QLineEdit {"
            "    background-color: #11141c;"
            "    border: 1px solid #1e2633;"
            "    border-radius: 8px;"
            "    color: #ffffff;"
            "    padding: 8px 12px;"
            "    font-size: 11px;"
            "    selection-background-color: #00ff88;"
            "    selection-color: #0b0d12;"
            "}"
            "QLineEdit:focus {"
            "    border: 1px solid #00ff88;"
            "}"
        )
        
        self.btn_send = QPushButton("↵")
        self.btn_send.setStyleSheet(
            "QPushButton {"
            "    background-color: #11141c;"
            "    border: 1px solid #1e2633;"
            "    border-radius: 8px;"
            "    color: #00ff88;"
            "    font-size: 15px;"
            "    font-weight: bold;"
            "    min-width: 36px;"
            "    max-width: 36px;"
            "    min-height: 32px;"
            "}"
            "QPushButton:hover {"
            "    background-color: #19202e;"
            "    border: 1px solid #00ff88;"
            "}"
            "QPushButton:pressed {"
            "    background-color: #00ff88;"
            "    color: #0b0d12;"
            "}"
        )
        
        input_layout.addWidget(self.input_command)
        input_layout.addWidget(self.btn_send)
        
        # 5. ALT EYLEM ÇUBUĞU (Mikrofon Aç/Kapat + Durdur + Ayarlar)
        action_layout = QHBoxLayout()
        action_layout.setSpacing(8)
        
        self.btn_mic = QPushButton("🎙️ Mikrofon açık")
        # Mikrofon açık varsayılan stil
        self.btn_mic.setStyleSheet(
            "QPushButton {"
            "    background-color: #0f1917;"
            "    border: 1px solid #133c30;"
            "    border-radius: 8px;"
            "    color: #00ff88;"
            "    font-size: 11px;"
            "    font-weight: bold;"
            "    min-height: 34px;"
            "    padding: 0 15px;"
            "}"
            "QPushButton:hover {"
            "    background-color: #132e26;"
            "    border: 1px solid #00ff88;"
            "}"
        )
        
        self.btn_stop = QPushButton("⏹")
        self.btn_stop.setToolTip("Sesi Durdur")
        self.btn_stop.setStyleSheet(
            "QPushButton {"
            "    background-color: #1a1114;"
            "    border: 1px solid #3c131a;"
            "    border-radius: 8px;"
            "    color: #ff3333;"
            "    font-size: 11px;"
            "    font-weight: bold;"
            "    min-width: 34px;"
            "    max-width: 34px;"
            "    min-height: 34px;"
            "}"
            "QPushButton:hover {"
            "    background-color: #2e1318;"
            "    border: 1px solid #ff3333;"
            "}"
            "QPushButton:pressed {"
            "    background-color: #ff3333;"
            "    color: #ffffff;"
            "}"
        )
        
        self.btn_settings = QPushButton("⚙")
        self.btn_settings.setToolTip("Seçenekler")
        self.btn_settings.setStyleSheet(
            "QPushButton {"
            "    background-color: #11141c;"
            "    border: 1px solid #1e2633;"
            "    border-radius: 8px;"
            "    color: #8da295;"
            "    font-size: 13px;"
            "    min-width: 34px;"
            "    max-width: 34px;"
            "    min-height: 34px;"
            "}"
            "QPushButton:hover {"
            "    background-color: #19202e;"
            "    border: 1px solid #00b0ff;"
            "    color: #00b0ff;"
            "}"
        )
        
        action_layout.addWidget(self.btn_mic, 1) # Mikrofon tuşu genişlesin
        action_layout.addWidget(self.btn_stop)
        action_layout.addWidget(self.btn_settings)
        
        # Layout birleştirmeleri
        container_layout.addLayout(header_layout)
        container_layout.addLayout(anim_container)
        container_layout.addWidget(self.card_widget)
        container_layout.addLayout(input_layout)
        container_layout.addLayout(action_layout)
        
        window_layout.addWidget(self.main_container)
        self.setLayout(window_layout)

    def update_border(self, border_color_hex: str):
        """HUD penceresinin neon yeşil/mavi/kırmızı dış kenarlık rengini günceller."""
        self.main_container.setStyleSheet(f"""
            QWidget#mainContainer {{
                background-color: #07090d;
                border: 1.5px solid {border_color_hex};
                border-radius: 20px;
            }}
        """)

    def contextMenuEvent(self, event):
        """Sağ tık menüsü."""
        self.show_settings_menu(event.globalPosition().toPoint())

    def show_settings_menu(self, position: QPoint):
        """Gelişmiş HUD temalı seçenekler menüsünü gösterir."""
        menu = QMenu(self)
        menu.setStyleSheet(
            "QMenu {"
            "    background-color: #0d1117;"
            "    color: #8da295;"
            "    border: 1px solid #1a2332;"
            "    border-radius: 6px;"
            "    font-size: 11px;"
            "    font-weight: bold;"
            "    padding: 4px;"
            "}"
            "QMenu::item {"
            "    padding: 6px 20px;"
            "    border-radius: 4px;"
            "}"
            "QMenu::item:selected {"
            "    background-color: #19202e;"
            "    color: #00ff88;"
            "}"
        )
        
        if self.anim_widget.state == "sleeping":
            sleep_action = QAction("☀️ Uykudan Uyandır", self)
        else:
            sleep_action = QAction("🌙 Uyku Moduna Al", self)
        sleep_action.triggered.connect(self.sig_sleep_requested.emit)
        
        clear_mem_action = QAction("🧠 Hafızayı Temizle", self)
        clear_mem_action.triggered.connect(self.sig_clear_mem_requested.emit)
        
        close_action = QAction("❌ Sistemi Kapat", self)
        close_action.triggered.connect(QApplication.quit)
        
        menu.addAction(sleep_action)
        menu.addAction(clear_mem_action)
        menu.addSeparator()
        menu.addAction(close_action)
        
        menu.exec(position)

    def set_status(self, status: str):
        """Penceredeki durumu günceller (Renk kodlaması ve animasyon tetiklemesi içerir)."""
        status_lower = status.lower()
        display_status = status.upper().replace("...", "").strip()
        
        if "dinleniyor" in status_lower:
            color = "#00ff88" # Neon yeşil
            self.anim_widget.set_state("listening")
            self.update_border("#13382c")
        elif "işleniyor" in status_lower or "isleniyor" in status_lower:
            color = "#00b0ff" # Neon mavi
            self.anim_widget.set_state("processing")
            self.update_border("#132838")
        elif "konuşuyor" in status_lower or "konusuyor" in status_lower or "speaking" in status_lower:
            color = "#00ff88" # Neon yeşil
            self.anim_widget.set_state("speaking")
            self.update_border("#13382c")
        elif "başlatılıyor" in status_lower or "baslatiliyor" in status_lower:
            color = "#00b0ff"
            self.anim_widget.set_state("listening")
            self.update_border("#132838")
        elif "onay bekliyor" in status_lower or "onay" in status_lower:
            color = "#ffb300" # Turuncu/Sarı
            self.anim_widget.set_state("processing")
            self.update_border("#3d3013")
        elif "hata" in status_lower:
            color = "#ff3333" # Kırmızı
            self.anim_widget.set_state("error")
            self.update_border("#3d1316")
        elif "uyku" in status_lower or "uykuda" in status_lower:
            color = "#5c6b73" # Gri
            self.anim_widget.set_state("sleeping")
            self.update_border("#222833")
        else:
            color = "#ffffff"
            self.anim_widget.set_state("listening")
            
        self.lbl_status.setText(display_status)
        self.lbl_status.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {color}; letter-spacing: 3px;")

    def set_last_command(self, text: str):
        """Son duyulan veya girilen komutu günceller."""
        # Komut çok uzunsa kırp
        if len(text) > 32:
            text = text[:29] + "..."
        self.lbl_last_command.setText(f'"{text}"')

    def set_result(self, text: str, success: bool = True):
        """Çalıştırılan aksiyonun sonucunu günceller."""
        # Duruma göre yeşil checkmark veya kırmızı ünlem ekleyelim
        if success:
            display_text = f"✓ {text}"
            color = "#00ff88"
        else:
            display_text = f"✗ {text}"
            color = "#ff3333"
            
        self.lbl_result.setText(display_text)
        self.lbl_result.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {color};")

    def set_model_info(self, model_name: str, response_time: float):
        """LLM işleme süresini ve model bilgisini alt çubuğa yazar."""
        # Model adını biraz süsleyelim: llama3.2:3b -> Llama 3B
        name_clean = model_name.replace(":", " ").replace("llama3.2", "Llama").replace("mistral", "Mistral")
        name_clean = name_clean.title()
        self.lbl_model_info.setText(f"{name_clean} · {response_time:.1f}sn")

    # ── SÜRÜKLEME OYUNLARI ────────────────────────────────────────────────
    def mousePressEvent(self, event):
        """Pencereyi sürükleyebilmek için fare tıklama olayını yakalar."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        """Pencereyi ekranda kaydırmak için fare hareketini yakalar."""
        if hasattr(self, "_old_pos"):
            delta = QPoint(event.globalPosition().toPoint() - self._old_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self._old_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        """Fare bırakıldığında sürükleme işlemini tamamlar."""
        if hasattr(self, "_old_pos"):
            del self._old_pos
