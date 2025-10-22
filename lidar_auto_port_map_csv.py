#!/usr/bin/env python3
import os
import csv
import time
import serial.tools.list_ports
import ydlidar
from ydlidar import CYdLidar

def find_lidar_port():
    """Lidar bağlı olabilecek portları otomatik bulur"""
    ports = [port.device for port in serial.tools.list_ports.comports()]
    print(f"🔍 Olası portlar: {ports}")
    for port in ports:
        try:
            lidar = CYdLidar()
            lidar.setlidaropt(ydlidar.LidarPropSerialPort, port)
            lidar.setlidaropt(ydlidar.LidarPropSerialBaudrate, 230400)
            lidar.setlidaropt(ydlidar.LidarPropLidarType, ydlidar.TYPE_TRIANGLE)
            lidar.setlidaropt(ydlidar.LidarPropDeviceType, ydlidar.DEVICE_SERIAL)
            lidar.setlidaropt(ydlidar.LidarPropScanFrequency, 10.0)

            if lidar.initialize() and lidar.turnOn():
                print(f"✅ Lidar bulundu: {port}")
                lidar.turnOff()
                lidar.disconnect()
                return port
        except Exception:
            pass
    return None


def main():
    print("✅ LIDAR başlatılıyor...")

    port = find_lidar_port()
    if not port:
        print("❌ Lidar bulunamadı.")
        return

    lidar = CYdLidar()
    lidar.setlidaropt(ydlidar.LidarPropSerialPort, port)
    lidar.setlidaropt(ydlidar.LidarPropSerialBaudrate, BAUDRATE = 230400)  # ✅ baudrate sıfırlanmasın
    lidar.setlidaropt(ydlidar.LidarPropLidarType, ydlidar.TYPE_TRIANGLE)
    lidar.setlidaropt(ydlidar.LidarPropDeviceType, ydlidar.DEVICE_SERIAL)
    lidar.setlidaropt(ydlidar.LidarPropScanFrequency, 10.0)

    if not lidar.initialize():
        print("❌ LIDAR başlatılamadı!")
        return

    if not lidar.turnOn():
        print("❌ LIDAR açılamadı!")
        return

    print("✅ LIDAR çalışıyor... (CTRL+C ile durdur)")

    # 🔧 Doğru LaserScan objesi
    try:
        scan = ydlidar._ydlidar.LaserScan()  # Bazı sürümlerde bu gerekiyor
    except AttributeError:
        scan = ydlidar.LaserScan()  # Eğer üstteki yoksa bu çalışır

    # 📁 CSV kayıt dosyası
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    csv_filename = f"lidar_data_{timestamp}.csv"

    with open(csv_filename, "w", newline="") as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(["angle", "distance", "intensity", "timestamp"])

        try:
            while True:
                success = lidar.doProcessSimple(scan)
                if success:
                    for p in scan.points:
                        csv_writer.writerow([p.angle, p.range, p.intensity, time.time()])
                time.sleep(0.05)
        except KeyboardInterrupt:
            print("\n🛑 Kullanıcı tarafından durduruldu.")
        finally:
            print("✅ LIDAR güvenli şekilde durduruluyor...")
            lidar.turnOff()
            lidar.disconnect()
            print(f"💾 Veriler kaydedildi: {csv_filename}")


if __name__ == "__main__":
    main()

