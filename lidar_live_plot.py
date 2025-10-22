#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import matplotlib.pyplot as plt
import numpy as np
import time
import signal
import sys
from ydlidar import CYdLidar, LidarPropSerialPort, LidarPropSerialBaudrate, \
    LidarPropLidarType, LidarPropDeviceType, LidarPropScanFrequency, LidarPropSampleRate, \
    LidarPropSingleChannel, TYPE_TRIANGLE, YDLIDAR_TYPE_SERIAL

stop_flag = False

def signal_handler(sig, frame):
    global stop_flag
    print("\n🔴 Ctrl+C algılandı, LIDAR güvenli şekilde durduruluyor...")
    stop_flag = True

signal.signal(signal.SIGINT, signal_handler)

def init_lidar(port='/dev/ttyUSB0'):
    lidar = CYdLidar()
    
    lidar.setlidaropt(LidarPropSerialPort, port)
    lidar.setlidaropt(LidarPropSerialBaudrate, 230400)
    lidar.setlidaropt(LidarPropLidarType, TYPE_TRIANGLE)
    lidar.setlidaropt(LidarPropDeviceType, YDLIDAR_TYPE_SERIAL)
    lidar.setlidaropt(LidarPropScanFrequency, 10.0)
    lidar.setlidaropt(LidarPropSampleRate, 5)
    lidar.setlidaropt(LidarPropSingleChannel, False)

    if not lidar.initialize():
        print("❌ LIDAR başlatılamadı!")
        sys.exit(1)
    if not lidar.turnOn():
        print("❌ LIDAR taraması başlatılamadı!")
        sys.exit(1)

    print("✅ LIDAR çalışıyor...")
    return lidar

def init_plot():
    plt.ion()
    fig = plt.figure(figsize=(6,6))
    ax = fig.add_subplot(111, polar=True)
    ax.set_ylim(0, 6)
    scatter = ax.scatter([], [], s=5, c='green')
    return fig, ax, scatter

def update_plot(ax, scatter, scan):
    if not scan.points:
        return
    angles = []
    distances = []
    for point in scan.points:
        if point.range > 0.05:  # minimum mesafe filtresi
            angles.append(np.deg2rad(point.angle))
            distances.append(point.range)
    scatter.set_offsets(np.c_[angles, distances])
    ax.figure.canvas.draw()
    ax.figure.canvas.flush_events()

def main():
    global stop_flag
    lidar = init_lidar('/dev/ttyUSB0')
    fig, ax, scatter = init_plot()

    # Boş scan nesnesi oluştur
    from ydlidar import LaserScan
    scan_points = LaserScan()

    try:
        while not stop_flag:
            if lidar.doProcessSimple(scan_points):
                update_plot(ax, scatter, scan_points)
            time.sleep(0.01)
    finally:
        lidar.turnOff()
        print("✅ LIDAR güvenli şekilde durduruldu.")

if __name__ == "__main__":
    main()

