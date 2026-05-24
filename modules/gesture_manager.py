"""
modules/gesture_manager.py - Jest Kontrol Yöneticisi
MediaPipe Hands ve OpenCV kullanarak web kamerasından el hareketlerini algılar ve sistem komutlarını tetikler.
"""

import cv2
import mediapipe as mp
import pyautogui
import time
import threading
import logging
import math
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from modules.media_manager import MediaManager

logger = logging.getLogger(__name__)

class GestureManager:
    """Web kamerasından el hareketlerini algılayıp JARVIS komutlarını çalıştıran yönetici sınıf."""
    
    def __init__(self):
        self.media_manager = MediaManager()
        self.is_running = False
        self.thread = None
        self.cap = None
        self.cooldown_time = 1.0  # Hareketler arası 1 saniye bekleme süresi
        self.last_gesture_time = 0.0
        
        # Pycaw ses kontrol arayüzünü başlat
        try:
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            self.volume_control = cast(interface, POINTER(IAudioEndpointVolume))
            logger.info("Pycaw ses kontrolü başarıyla başlatıldı.")
        except Exception as e:
            logger.error(f"Pycaw başlatılamadı: {e}")
            self.volume_control = None

    def start(self) -> dict:
        """Kamerayı ve hareket algılama döngüsünü ayrı bir thread'de başlatır."""
        if self.is_running:
            logger.info("GestureManager zaten çalışıyor.")
            return {"success": True, "message": "Kamera zaten aktif."}
            
        self.is_running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        logger.info("GestureManager başlatıldı.")
        return {"success": True, "message": "Kamera ve jest kontrolü aktifleştirildi."}

    def stop(self) -> dict:
        """Kamerayı kapatır ve hareket algılama döngüsünü sonlandırır."""
        if not self.is_running:
            logger.info("GestureManager zaten durdurulmuş.")
            return {"success": True, "message": "Kamera zaten kapalı."}
            
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=2.0)
            self.thread = None
            
        logger.info("GestureManager durduruldu.")
        return {"success": True, "message": "Kamera ve jest kontrolü kapatıldı."}

    def _run_loop(self):
        """Web kamerası okuma ve el hareketi algılama ana döngüsü."""
        # MediaPipe Hands bileşenlerini başlat (Çift el algılama için max_num_hands=2)
        mp_hands = mp.solutions.hands
        mp_drawing = mp.solutions.drawing_utils
        
        hands = mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )

        # Kamera cihazını aç (Varsayılan kamera: 0)
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            logger.error("Web kamerası açılamadı!")
            self.is_running = False
            return

        logger.info("Web kamerası başarıyla açıldı, el hareketleri taranıyor...")

        while self.is_running:
            ret, frame = self.cap.read()
            if not ret:
                logger.warning("Kameradan görüntü alınamadı.")
                time.sleep(0.03)
                continue

            # Görüntüyü yatayda aynala (kullanıcı için daha doğal olması adına)
            frame = cv2.flip(frame, 1)
            
            # Görüntüyü küçült (daha hızlı işlem ve küçük önizleme için)
            h, w, c = frame.shape
            preview_w = 400
            preview_h = int((preview_w / w) * h)
            frame = cv2.resize(frame, (preview_w, preview_h))

            # MediaPipe için BGR -> RGB dönüşümü
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(rgb_frame)

            detected_gesture = None
            current_time = time.time()
            cooldown_active = (current_time - self.last_gesture_time) < self.cooldown_time

            if results.multi_hand_landmarks:
                num_hands = len(results.multi_hand_landmarks)

                # Landmarkları ekrana çiz
                for hand_landmarks in results.multi_hand_landmarks:
                    mp_drawing.draw_landmarks(
                        frame, 
                        hand_landmarks, 
                        mp_hands.HAND_CONNECTIONS,
                        mp_drawing.DrawingSpec(color=(0, 255, 136), thickness=2, circle_radius=2),
                        mp_drawing.DrawingSpec(color=(255, 176, 0), thickness=2)
                    )

                # ── 1. ÇİFT EL JESTLERİ (Wrists crossing / BOTH_FISTS_CROSS) ────
                if num_hands == 2 and not cooldown_active:
                    hand1 = results.multi_hand_landmarks[0]
                    hand2 = results.multi_hand_landmarks[1]

                    # Hand 1 yumruk kontrolü
                    h1_index = hand1.landmark[8].y < hand1.landmark[6].y
                    h1_middle = hand1.landmark[12].y < hand1.landmark[10].y
                    h1_ring = hand1.landmark[16].y < hand1.landmark[14].y
                    h1_pinky = hand1.landmark[20].y < hand1.landmark[18].y
                    h1_fist = not h1_index and not h1_middle and not h1_ring and not h1_pinky

                    # Hand 2 yumruk kontrolü
                    h2_index = hand2.landmark[8].y < hand2.landmark[6].y
                    h2_middle = hand2.landmark[12].y < hand2.landmark[10].y
                    h2_ring = hand2.landmark[16].y < hand2.landmark[14].y
                    h2_pinky = hand2.landmark[20].y < hand2.landmark[18].y
                    h2_fist = not h2_index and not h2_middle and not h2_ring and not h2_pinky

                    if h1_fist and h2_fist:
                        # Wrists crossing tespiti: left wrist x > right wrist x
                        left_wrist_x = None
                        right_wrist_x = None

                        for idx, hand_class in enumerate(results.multi_handedness):
                            label = hand_class.classification[0].label # "Left" veya "Right"
                            wrist_x = results.multi_hand_landmarks[idx].landmark[0].x
                            if label == "Left":
                                left_wrist_x = wrist_x
                            elif label == "Right":
                                right_wrist_x = wrist_x

                        if left_wrist_x is not None and right_wrist_x is not None:
                            if left_wrist_x > right_wrist_x:
                                detected_gesture = "BOTH_FISTS_CROSS"

                # ── 2. TEK EL JESTLERİ ──────────────────────────────────────────
                if not detected_gesture and num_hands >= 1 and not cooldown_active:
                    hand_landmarks = results.multi_hand_landmarks[0]
                    landmarks = hand_landmarks.landmark

                    # Parmak durumlarını analiz et
                    index_open = landmarks[8].y < landmarks[6].y
                    middle_open = landmarks[12].y < landmarks[10].y
                    ring_open = landmarks[16].y < landmarks[14].y
                    pinky_open = landmarks[20].y < landmarks[18].y
                    
                    # Baş parmak için indeks MCP (5) ile mesafe kıyaslama
                    d_4_5 = math.hypot(landmarks[4].x - landmarks[5].x, landmarks[4].y - landmarks[5].y)
                    d_2_5 = math.hypot(landmarks[2].x - landmarks[5].x, landmarks[2].y - landmarks[5].y)
                    thumb_open = d_4_5 > d_2_5 * 1.3

                    # INDEX_UP tespiti
                    # Diğer tüm parmaklar kapalı olmalı (tip y > pip y)
                    other_fingers_closed = (
                        landmarks[12].y > landmarks[10].y and  # Orta
                        landmarks[16].y > landmarks[14].y and  # Yüzük
                        landmarks[20].y > landmarks[18].y      # Serçe
                    )

                    if other_fingers_closed:
                        # İşaret parmağı yönü
                        if landmarks[8].y < landmarks[5].y:
                            detected_gesture = "INDEX_UP"

                    if not detected_gesture:
                        if index_open and middle_open and ring_open and pinky_open and thumb_open:
                            detected_gesture = "OPEN_PALM"
                        elif not index_open and not middle_open and not ring_open and not pinky_open:
                            if thumb_open:
                                # Baş parmak yönünü kontrol et
                                if landmarks[4].y < landmarks[3].y:
                                    detected_gesture = "THUMBS_UP"
                                elif landmarks[4].y > landmarks[3].y:
                                    detected_gesture = "THUMBS_DOWN"
                            else:
                                detected_gesture = "FIST"

                # Jest tetikleme işlemi
                if detected_gesture:
                    self._trigger_action(detected_gesture)
                    self.last_gesture_time = current_time

            # Bilgilendirme metnini ekrana yazdır
            status_text = "Bekleniyor..."
            if detected_gesture:
                status_text = f"Tetiklendi: {detected_gesture}"
            elif (time.time() - self.last_gesture_time) < self.cooldown_time:
                status_text = "Bekleme Modu (1s)"
                
            # Arka plan kutusu
            cv2.rectangle(frame, (10, preview_h - 40), (220, preview_h - 10), (7, 9, 13), -1)
            cv2.putText(
                frame, 
                status_text, 
                (15, preview_h - 18), 
                cv2.FONT_HERSHEY_SIMPLEX, 
                0.5, 
                (0, 255, 136), 
                1, 
                cv2.LINE_AA
            )

            # Önizleme penceresini göster
            cv2.imshow("JARVIS Gesture Control", frame)
            
            # OpenCV pencerelerinin tepki vermesi için waitKey
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        # Temizlik işlemleri
        if self.cap:
            self.cap.release()
            self.cap = None
        hands.close()
        cv2.destroyAllWindows()
        self.is_running = False

    def _trigger_action(self, gesture: str):
        """Algılanan jiste göre ilgili JARVIS/sistem eylemini yürütür."""
        logger.info(f"Jest Algılandı: {gesture}")
        try:
            if gesture == "OPEN_PALM":
                pyautogui.hotkey("space")
            elif gesture == "FIST":
                pyautogui.hotkey("alt", "f4")
            elif gesture == "THUMBS_UP":
                # volume up
                if self.volume_control:
                    try:
                        current_vol = self.volume_control.GetMasterVolumeLevelScalar()
                        self.volume_control.SetMasterVolumeLevelScalar(min(1.0, current_vol + 0.05), None)
                    except Exception as e:
                        logger.error(f"Pycaw volume up error: {e}")
                pyautogui.hotkey("ctrl", "up")
                pyautogui.press("volumeup")
            elif gesture == "THUMBS_DOWN":
                # volume down
                if self.volume_control:
                    try:
                        current_vol = self.volume_control.GetMasterVolumeLevelScalar()
                        self.volume_control.SetMasterVolumeLevelScalar(max(0.0, current_vol - 0.05), None)
                    except Exception as e:
                        logger.error(f"Pycaw volume down error: {e}")
                pyautogui.hotkey("ctrl", "down")
                pyautogui.press("volumedown")
            elif gesture == "INDEX_UP":
                pyautogui.scroll(300)
            elif gesture == "BOTH_FISTS_CROSS":
                pyautogui.hotkey("win", "d")
        except Exception as e:
            logger.error(f"Jest eylemi çalıştırılırken hata: {e}")
