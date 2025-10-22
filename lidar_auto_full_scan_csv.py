import time
import csv
import datetime
import serial.tools.list_ports
from ydlidar import CYdLidar, LaserScan

def init_lidar(port, baudrate):
    lidar = CYdLidar()
    lidar.setlidaropt(0, port)         # 0 = serial port
    lidar.setlidaropt(1, baudrate)     # 1 = baudrate
    lidar.setlidaropt(2, True)         # 2 = intensities
    lidar.setlidaropt(3, 10.0)         # 3 = scan frequency
    lidar.setlidaropt(4, False)        # 4 = fixed angle
    lidar.setlidaropt(5, 180.0)        # 5 = angle min
    lidar.setlidaropt(6, -180.0)       # 6 = angle max
    lidar.setlidaropt(7, 0.25)         # 7 = max range
    lidar.setlidaropt(8, 16.0)         # 8 = min range
    lidar.setlidaropt(9, False)        # 9 = reversion
    lidar.setlidaropt(10, False)       # 10 = auto reconnect
    lidar.setlidaropt(11, False)       # 11 = glass noise filter
    lidar.setlidaropt(12, False)       # 12 = sun noise filter
    lidar.setlidaropt(13, False)       # 13 = low exposure
    lidar.setlidaropt(14, False)       # 14 = heartbeat
    lidar.initialize()
    return lidar

def find_lidar_port():
    ports = [p.device for p in serial.tools.list_ports.comports()]
    print(f"🔍 Olası portlar: {ports}")
    for port in ports:
        for baud in [115200, 230400]:
            print(f"⏳ Deneniyor: {port} @ {baud}")
            lidar = init_lidar(port, baud)
            if lidar:
                if lidar.initialize():
                    print(f"✅ Lidar bulundu: {port} @ {baud}")
                    return lidar, port, baud
                else:
                    print(f"❌ {port} @ {baud} başarısız.")
    return None, None, None

def save_to_csv(data):
    filename = f"lidar_data_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["angle", "distance"])
        for angle, distance in data:
            writer.writerow([angle, distance])
    print(f"💾 Veriler kaydedildi: {filename}")

def main():
    print("✅ LIDAR başlatılıyor...")
    lidar, port, baud = find_lidar_port()
    if not lidar:
        print("❌ Lidar bulunamadı.")
        return

    if not lidar.turnOn():
        print("❌ Lidar açılamadı.")
        return

    print("✅ LIDAR çalışıyor... (CTRL+C ile durdur)")
    scan = LaserScan()
    data = []
    try:
        for _ in range(30):  # 3 saniye kadar örnek veri
            success = lidar.doProcessSimple(scan)
            if success:
                for p in scan.points:
                    data.append((p.angle, p.range))
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass
    finally:
        print("✅ LIDAR güvenli şekilde durduruluyor...")
        lidar.turnOff()
        lidar.disconnecting()
        save_to_csv(data)
        print("✅ Kapatıldı.")

if __name__ == "__main__":
    main()

