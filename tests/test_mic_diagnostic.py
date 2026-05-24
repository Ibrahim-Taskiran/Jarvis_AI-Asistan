"""
Mikrofon ve ses isleme diagnostik testi.
Mikrofonun ses alip almadigini ve filtre sonrasi seviyeleri kontrol eder.
"""

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.stdout.reconfigure(encoding="utf-8")

import numpy as np
import sounddevice as sd
import noisereduce as nr
from scipy.signal import butter, sosfilt

SAMPLE_RATE = 16000
SILENCE_THRESHOLD = 0.01

def highpass_filter(audio, sr, cutoff=80.0):
    sos = butter(5, cutoff, btype="high", fs=sr, output="sos")
    return sosfilt(sos, audio).astype(np.float32)

# 1) Mevcut ses cihazlarini listele
print("=" * 60)
print("MIKROFON DIAGNOSTIK TESTI")
print("=" * 60)
print()

print("[1] Mevcut ses cihazlari:")
print("-" * 40)
devices = sd.query_devices()
default_input = sd.default.device[0]
for i, d in enumerate(devices):
    if d['max_input_channels'] > 0:
        marker = " <<< DEFAULT" if i == default_input else ""
        print(f"  [{i}] {d['name']} (in={d['max_input_channels']}ch, sr={d['default_samplerate']}){marker}")

print()
print(f"[2] Varsayilan giris cihazi: [{default_input}] {devices[default_input]['name']}")
print()

# 2) 3 saniye kayit
print("[3] 3 saniye ses kaydediliyor... SIMDI KONUSUN!")
print("-" * 40)

audio_raw = sd.rec(int(3 * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype="float32")
sd.wait()
audio_raw = audio_raw.flatten()

rms_raw = np.sqrt(np.mean(audio_raw ** 2))
peak_raw = np.max(np.abs(audio_raw))
print(f"  Ham ses - RMS: {rms_raw:.6f}, Peak: {peak_raw:.6f}")
print(f"  Sessizlik esigi: {SILENCE_THRESHOLD}")
print(f"  Ham ses sessiz mi? {'EVET' if rms_raw < SILENCE_THRESHOLD else 'HAYIR'}")

# 3) Noise reduction uygula
print()
print("[4] Noise reduction uygulandiktan sonra:")
print("-" * 40)
audio_nr = nr.reduce_noise(y=audio_raw, sr=SAMPLE_RATE, stationary=False, prop_decrease=0.75)
rms_nr = np.sqrt(np.mean(audio_nr ** 2))
peak_nr = np.max(np.abs(audio_nr))
print(f"  NR sonrasi - RMS: {rms_nr:.6f}, Peak: {peak_nr:.6f}")
print(f"  NR sonrasi sessiz mi? {'EVET' if rms_nr < SILENCE_THRESHOLD else 'HAYIR'}")

# 4) High-pass filter uygula
print()
print("[5] High-pass filtre (80Hz) uygulandiktan sonra:")
print("-" * 40)
audio_hp = highpass_filter(audio_nr, sr=SAMPLE_RATE, cutoff=80.0)
rms_hp = np.sqrt(np.mean(audio_hp ** 2))
peak_hp = np.max(np.abs(audio_hp))
print(f"  HP sonrasi - RMS: {rms_hp:.6f}, Peak: {peak_hp:.6f}")
print(f"  HP sonrasi sessiz mi? {'EVET' if rms_hp < SILENCE_THRESHOLD else 'HAYIR'}")

# 5) Ozet
print()
print("=" * 60)
print("OZET:")
if rms_raw < 0.001:
    print("  [SORUN] Mikrofon neredeyse hic ses almiyor!")
    print("  >> Mikrofon baglantisinizi ve Windows ses ayarlarini kontrol edin.")
elif rms_raw < SILENCE_THRESHOLD:
    print("  [SORUN] Mikrofon ses aliyor ama cok dusuk.")
    print(f"  >> Sessizlik esigini {rms_raw * 0.5:.6f} gibi daha dusuk bir degere ayarlayin.")
elif rms_hp < SILENCE_THRESHOLD and rms_raw >= SILENCE_THRESHOLD:
    print("  [SORUN] Filtreler sesi cok bastiriyor!")
    print(f"  >> Ham RMS: {rms_raw:.6f} -> Filtre sonrasi: {rms_hp:.6f}")
    print("  >> prop_decrease degerini dusurmeyi veya esigi dusurmeyi deneyin.")
else:
    print("  [OK] Mikrofon ve filtreler dogru calisiyor.")
    print(f"  >> Son RMS: {rms_hp:.6f} > esik: {SILENCE_THRESHOLD}")
print("=" * 60)
