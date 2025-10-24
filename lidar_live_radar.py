#!/usr/bin/env python3
# lidar_live_radar.py
# Real-time LIDAR radar display (Cartesian). Works with YDLidar SDK variations.

import time
import math
import csv
import sys
import os
from datetime import datetime

import numpy as np
import matplotlib.pyplot as plt

# serial ports helper
try:
    import serial.tools.list_ports as list_ports
except Exception:
    list_ports = None

# ydlidar imports
import ydlidar
from ydlidar import CYdLidar

# ---- Config ----
AUTO_FIND_PORT = True        # otomatik port bul
PORTS_TO_TRY = None          # None => tüm /dev/ttyUSB* / ttyACM* taranır (serial.tools.list_ports ile)
BAUDRATES = [230400, 115200] # denenebilir; senin cihazın için 115200/230400 ikisi de denenir
SCAN_FREQUENCY = 10.0
SAMPLE_RATE = 5.0
LOG_TO_CSV = True            # CSV'ye kaydetmek istersen True
CSV_DIR = "./"
MAX_POINTS = 2000           # grafik için üst sınır (performans)
# -----------------

def find_ports():
    ports = []
    if list_ports:
        ports = [p.device for p in list_ports.comports()]
    else:
        # fallback: list /dev
        for d in os.listdir("/dev"):
            if "ttyUSB" in d or "ttyACM" in d:
                ports.append(os.path.join("/dev", d))
    return sorted(ports)

def try_init_lidar(port, baud):
    """ Bir port+baud ile CYdLidar başlatmayı dener. Başarılı olursa lidar objesini döner. """
    lidar = CYdLidar()
    # Bazı SDK sürümlerinde setlidaropt sabitleri farklıdır. Burada integer kodları kullanıyoruz
    # Bu mapping daha önce işe yaradı: 4=SerialPort,5=Baudrate,1=LidarType,2=DeviceType,6=SampleRate,7=ScanFrequency
    try:
        LidarPropSerialPort = getattr(ydlidar, "LidarPropSerialPort", 4)
        LidarPropSerialBaudrate = getattr(ydlidar, "LidarPropSerialBaudrate", 5)
        LidarPropLidarType = getattr(ydlidar, "LidarPropLidarType", 1)
        LidarPropDeviceType = getattr(ydlidar, "LidarPropDeviceType", 2)
        LidarPropSampleRate = getattr(ydlidar, "LidarPropSampleRate", 6)
        LidarPropScanFrequency = getattr(ydlidar, "LidarPropScanFrequency", 7)

        lidar.setlidaropt(LidarPropSerialPort, port)
        lidar.setlidaropt(LidarPropSerialBaudrate, baud)
        lidar.setlidaropt(LidarPropLidarType, getattr(ydlidar, "TYPE_TRIANGLE", 1))
        lidar.setlidaropt(LidarPropDeviceType, getattr(ydlidar, "DEVICE_SERIAL", True))
        lidar.setlidaropt(LidarPropSampleRate, SAMPLE_RATE)
        lidar.setlidaropt(LidarPropScanFrequency, SCAN_FREQUENCY)

        # initialize only to check if device responds
        if not lidar.initialize():
            # cleanup attempt
            try:
                lidar.turnOff()
            except Exception:
                pass
            try:
                # some SDKs use disconnecting()
                if hasattr(lidar, "disconnect"):
                    lidar.disconnect()
                elif hasattr(lidar, "disconnecting"):
                    lidar.disconnecting()
            except Exception:
                pass
            return None
        # start scanning immediately to confirm
        if not lidar.turnOn():
            lidar.turnOff()
            try:
                if hasattr(lidar, "disconnect"):
                    lidar.disconnect()
                elif hasattr(lidar, "disconnecting"):
                    lidar.disconnecting()
            except Exception:
                pass
            return None

        # If we get here, it's good
        return lidar
    except Exception:
        try:
            if hasattr(lidar, "disconnect"):
                lidar.disconnect()
            elif hasattr(lidar, "disconnecting"):
                lidar.disconnecting()
        except Exception:
            pass
        return None

def find_and_init_lidar():
    ports = find_ports()
    if PORTS_TO_TRY:
        ports = PORTS_TO_TRY
    if not ports:
        print("❌ Hiç serial port bulunamadı. Lütfen kablo/bağlantıyı kontrol et.")
        return None, None, None

    print(f"🔍 Olası portlar: {ports}")
    for port in ports:
        for baud in BAUDRATES:
            print(f"⏳ Deneniyor: {port} @ {baud}")
            lidar = try_init_lidar(port, baud)
            if lidar:
                print(f"✅ Lidar bulundu: {port} @ {baud}")
                return lidar, port, baud
            else:
                print(f"❌ {port} @ {baud} başarısız.")
    return None, None, None

def create_laserscan_instance():
    """Farklı ydlidar wrapper varyasyonlarına tolerant LaserScan oluştur."""
    # 1) try ydlidar._ydlidar.LaserScan
    try:
        return ydlidar._ydlidar.LaserScan()
    except Exception:
        pass
    # 2) try ydlidar.LaserScan
    try:
        return ydlidar.LaserScan()
    except Exception:
        pass
    # 3) fallback: create minimal object with .points = []
    class DummyScan:
        def __init__(self):
            self.points = []
    return DummyScan()

def safe_disconnect(lidar):
    try:
        lidar.turnOff()
    except Exception:
        pass
    try:
        if hasattr(lidar, "disconnect"):
            lidar.disconnect()
        elif hasattr(lidar, "disconnecting"):
            lidar.disconnecting()
    except Exception:
        pass

def run_radar():
    print("✅ LIDAR başlatılıyor...")

    lidar, port, baud = find_and_init_lidar()
    if lidar is None:
        print("❌ Lidar bulunamadı. Script sonlandırılıyor.")
        return

    # create LaserScan container once
    scan = create_laserscan_instance()

    # Prepare CSV logging if isteniyorsa
    csv_writer = None
    csv_file = None
    if LOG_TO_CSV:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(CSV_DIR, f"lidar_live_{ts}.csv")
        csv_file = open(filename, "w", newline="")
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(["timestamp", "angle_deg", "distance", "intensity"])

    # Matplotlib setup (Cartesian)
    plt.ion()
    fig, ax = plt.subplots(figsize=(7,7))
    scatter = ax.scatter([], [], s=6)
    ax.set_title(f"LIDAR Live Radar — {port} @ {baud}")
    max_range_m = 6.0  # 6 meters default
    ax.set_xlim(-max_range_m, max_range_m)
    ax.set_ylim(-max_range_m, max_range_m)
    ax.set_xlabel("X (m)")
    ax.set_ylabel("Y (m)")
    ax.set_aspect('equal', 'box')
    fig.canvas.draw()
    fig.canvas.flush_events()

    try:
        while True:
            # DoProcessSimple expects a LaserScan& argument (we created 'scan' instance)
            try:
                ok = lidar.doProcessSimple(scan)
            except TypeError:
                # some wrappers accept list and return points directly
                try:
                    ok = lidar.doProcessSimple()
                except Exception:
                    ok = False

            if ok:
                angles = []
                dists = []
                # depending on wrapper attribute names: use .points with objects having .angle and .range
                pts = getattr(scan, "points", None)
                if pts is None:
                    # maybe scan is a list
                    pts = scan

                for p in pts:
                    # p may have attributes 'angle'/'range' or 'angle'/'distance' etc.
                    angle = getattr(p, "angle", None)
                    rng = getattr(p, "range", None) or getattr(p, "distance", None) or getattr(p, "dist", None)
                    intensity = getattr(p, "intensity", None)
                    if angle is None or rng is None:
                        continue
                    # Convert to meters if it looks like mm (heuristic: values over 1000 -> treat as mm)
                    if rng > 1000:  # likely mm
                        rng_m = rng / 1000.0
                    else:
                        rng_m = rng
                    angles.append(math.radians(angle))
                    dists.append(rng_m)
                    if csv_writer:
                        csv_writer.writerow([time.time(), angle, rng_m, intensity])

                if len(angles) == 0:
                    # no valid points
                    scatter.set_offsets(np.empty((0,2)))
                else:
                    xs = np.asarray(dists) * np.cos(np.asarray(angles))
                    ys = np.asarray(dists) * np.sin(np.asarray(angles))
                    points = np.c_[xs, ys]
                    # limit to MAX_POINTS for performance
                    if points.shape[0] > MAX_POINTS:
                        points = points[-MAX_POINTS:, :]
                    scatter.set_offsets(points)

                    # autoscale if needed (optional) - keep fixed for stability
                    # ax.set_xlim(-max_range_m, max_range_m)
                    # ax.set_ylim(-max_range_m, max_range_m)

                fig.canvas.draw()
                fig.canvas.flush_events()
            else:
                # no data this loop
                time.sleep(0.01)

    except KeyboardInterrupt:
        print("\n🛑 Kullanıcı tarafından durduruldu (CTRL+C).")
    except Exception as e:
        print("\n❌ Hata oluştu:", e)
    finally:
        print("✅ LIDAR güvenli şekilde durduruluyor...")
        try:
            if csv_file:
                csv_file.close()
        except Exception:
            pass
        safe_disconnect(lidar)
        plt.close(fig)
        if csv_writer:
            print(f"💾 CSV kaydedildi: {filename}")

if __name__ == "__main__":
    run_radar()

