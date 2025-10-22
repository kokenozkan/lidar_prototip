#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import csv
import datetime
import math
import matplotlib.pyplot as plt
from ydlidar import CYdLidar, LaserScan

# ---------- LIDAR PORT AYARLARI ----------
PORT = "/dev/ttyUSB0"
BAUDRATE = 230400

def init_lidar():
    lidar = CYdLidar()

    # Lidar parametreleri
    lidar.setlidaropt("serial_port", PORT)
    lidar.setlidaropt("serial_baudrate", BAUDRATE)
    lidar.setlidaropt("lidar_type", 1)        # 1 = G2B
    lidar.setlidaropt("device_type", True)    # USB bağlantı
    lidar.setlidaropt("sample_rate", 5.0)    # 5K
    lidar.setlidaropt("scan_frequency", 10.0) # Hz

    # Lidar başlat
    if not lidar.initialize():
        raise RuntimeError("Lidar başlatılamadı!")
    print("✅ LIDAR çalışıyor... (CTRL+C ile durdur)")

    return lidar

# ---------- CSV KAYIT FONKSİYONU ----------
def save_csv(filename, scan: LaserScan):
    with open(filename, mode='a', newline='') as file:
        writer = csv.writer(file)
        for pt in scan.points:
            writer.writerow([pt.angle, pt.range, pt.intensity])

# ---------- POLAR PLOT GÜNCELLEME ----------
def update_plot(scatter, scan: LaserScan):
    angles = []
    distances = []

    for pt in scan.points:
        angles.append(math.radians(pt.angle))
        distances.append(pt.range)

    # Noktalar boşsa atla
    if not angles:
        return

    xs = [d*math.cos(a) for a, d in zip(angles, distances)]
    ys = [d*math.sin(a) for a, d in zip(angles, distances)]

    scatter.set_offsets(list(zip(xs, ys)))

# ---------- ANA FONKSİYON ----------
def main():
    lidar = init_lidar()
    scan = LaserScan()  # LaserScan nesnesi, doProcessSimple için
    filename = f"lidar_data_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    # Matplotlib ayarları
    plt.ion()
    fig, ax = plt.subplots(figsize=(6,6))
    scatter = ax.scatter([], [])
    ax.set_xlim(-10, 10)
    ax.set_ylim(-10, 10)
    ax.set_xlabel("X [m]")
    ax.set_ylabel("Y [m]")
    ax.set_title("Lidar Canlı Tarama")

    try:
        while True:
            if lidar.doProcessSimple(scan):
                update_plot(scatter, scan)
                plt.pause(0.001)        # Grafik güncelle
                save_csv(filename, scan) # CSV kaydet
    except KeyboardInterrupt:
        print("✅ LIDAR güvenli şekilde durduruldu.")
        lidar.turnOff()
        lidar.disconnect()
        plt.ioff()
        plt.show()
        print(f"💾 Veriler kaydedildi: {filename}")

if __name__ == "__main__":
    main()

