#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import csv
import math
import datetime
import matplotlib.pyplot as plt
from ydlidar import CYdLidar

# ------------------- CONFIG -------------------
PORT = "/dev/ttyUSB0"
BAUDRATE = 230400
LIDAR_TYPE = 1        # TYPE_TRIANGLE = 1
SAMPLE_RATE = 5.0
SCAN_FREQUENCY = 10.0
CSV_DIR = "./"
# ----------------------------------------------

def init_lidar():
    lidar = CYdLidar()

    # SDK sabitleri:
    LidarPropSerialPort = 4
    LidarPropSerialBaudrate = 5
    LidarPropLidarType = 1
    LidarPropDeviceType = 2
    LidarPropSampleRate = 6
    LidarPropScanFrequency = 7

    # Lidar parametreleri
    lidar.setlidaropt(LidarPropSerialPort, PORT)
    lidar.setlidaropt(LidarPropSerialBaudrate, BAUDRATE)
    lidar.setlidaropt(LidarPropLidarType, LIDAR_TYPE)
    lidar.setlidaropt(LidarPropDeviceType, True)
    lidar.setlidaropt(LidarPropSampleRate, SAMPLE_RATE)
    lidar.setlidaropt(LidarPropScanFrequency, SCAN_FREQUENCY)

    if not lidar.initialize():
        print("❌ LIDAR başlatılamadı!")
        return None

    if not lidar.turnOn():
        print("❌ LIDAR taramaya başlayamadı!")
        return None

    print("✅ LIDAR çalışıyor... (CTRL+C ile durdur)")
    return lidar

def stop_lidar(lidar):
    if lidar:
        lidar.turnOff()
        lidar.disconnect()
    print("✅ LIDAR güvenli şekilde durduruldu.")

def process_scan(scan):
    angles = []
    distances = []
    for point in scan.points:
        if point.range > 0.0:  # geçerli mesafeleri al
            angles.append(math.radians(point.angle))
            distances.append(point.range)
    return angles, distances

def save_csv(angles, distances):
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(CSV_DIR, f"lidar_data_{timestamp}.csv")
    with open(filename, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["angle_deg", "distance_m"])
        for a, d in zip([math.degrees(a) for a in angles], distances):
            writer.writerow([a, d])
    print(f"💾 Veriler kaydedildi: {filename}")

def main():
    lidar = init_lidar()
    if lidar is None:
        return

    plt.ion()
    fig, ax = plt.subplots(subplot_kw={'projection':'polar'})
    scatter = ax.scatter([], [], s=10)
    ax.set_rmax(10)
    ax.set_rmin(0)
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)

    angles_all = []
    distances_all = []

    try:
        while True:
            scan = lidar.doProcessSimple()  # outscan parametresi otomatik artık
            if scan:
                angles, distances = process_scan(scan)
                angles_all.extend(angles)
                distances_all.extend(distances)

                scatter.set_offsets(list(zip(angles, distances)))
                fig.canvas.draw()
                fig.canvas.flush_events()
            else:
                time.sleep(0.01)
    except KeyboardInterrupt:
        pass
    finally:
        stop_lidar(lidar)
        save_csv(angles_all, distances_all)
        plt.ioff()
        plt.show()

if __name__ == "__main__":
    print("✅ LIDAR başlatılıyor...")
    main()

