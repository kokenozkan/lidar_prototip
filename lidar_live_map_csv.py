import math
import time
import csv
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from ydlidar import CYdLidar, LaserScan

# === Ayarlar ===
PORT = "/dev/ttyUSB0"
BAUDRATE = 230400
CSV_FILENAME = f"lidar_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

# === CSV Dosyası Hazırlığı ===
csv_file = open(CSV_FILENAME, mode='w', newline='')
csv_writer = csv.writer(csv_file)
csv_writer.writerow(["timestamp", "angle_deg", "distance_m"])

# === LIDAR Başlatma ===
def init_lidar():
    lidar = CYdLidar()

    # Parametreler string olarak gönderiliyor (eski SDK uyumlu)
    lidar.setlidaropt("lidar_type", 1)
    lidar.setlidaropt("device_type", 0)
    lidar.setlidaropt("port", PORT)
    lidar.setlidaropt("baudrate", BAUDRATE)
    lidar.setlidaropt("sample_rate", 5)
    lidar.setlidaropt("scan_frequency", 10.0)
    lidar.setlidaropt("single_channel", False)

    if not lidar.initialize():
        print("❌ LIDAR başlatılamadı!")
        exit(1)
    if not lidar.turnOn():
        print("❌ LIDAR açılamadı!")
        exit(1)

    print("✅ LIDAR çalışıyor...")
    return lidar

# === Matplotlib Görsel ===
fig = plt.figure(figsize=(6, 6))
ax = plt.subplot(111, projection='polar')
ax.set_ylim(0, 12)
ax.grid(True)

points, = ax.plot([], [], 'b.', markersize=2)
text_handle = ax.text(0.05, 1.05, "", transform=ax.transAxes)

# === Global değişkenler ===
lidar = None
scan_data = []

# === Grafik Güncelleme ===
def update(frame):
    global scan_data
    scan = LaserScan()

    if lidar.doProcessSimple(scan):  # Veri geldi mi?
        print(f"{len(scan.points)} nokta alındı.")  # Test çıktısı
        angles = []
        distances = []
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]

        for point in scan.points:
            if point.range > 0.05:
                angles.append(math.radians(point.angle))
                distances.append(point.range)
                csv_writer.writerow([timestamp, point.angle, point.range])

        scan_data = (angles, distances)
        if angles and distances:
            points.set_data(angles, distances)
            text_handle.set_text(f"🌐 Nokta sayısı: {len(distances)}")
    else:
        text_handle.set_text("⚠️ Veri alınamıyor...")

    return points, text_handle

# === Ana Fonksiyon ===
def main():
    global lidar
    print("✅ LIDAR başlatılıyor...")
    lidar = init_lidar()

    print("📊 Canlı veri akışı başlıyor... (CTRL+C ile durdur)")
    ani = FuncAnimation(fig, update, interval=100)
    plt.show()

# === Program Sonu ===
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Kullanıcı tarafından durduruldu.")
    finally:
        if lidar:
            lidar.turnOff()
            lidar.disconnecting()
        csv_file.close()
        print("✅ LIDAR güvenli şekilde durduruldu.")
        print(f"💾 Veriler kaydedildi: {CSV_FILENAME}")

