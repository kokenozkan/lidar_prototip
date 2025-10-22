import sys
import glob
import time
import pyrealsense2 as rs
from ydlidar import CYdLidar, LaserScan

# -------------------------------
# 1️⃣ LIDAR Port Bulma
# -------------------------------
def find_lidar_port():
    ports = glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*')
    if not ports:
        print("⚠️ LIDAR portu bulunamadı!")
        return None
    print(f"Port bulundu: {ports[0]}")
    return ports[0]

lidar_port = find_lidar_port()
if lidar_port is None:
    sys.exit(1)

# -------------------------------
# 2️⃣ LIDAR Başlatma
# -------------------------------
lidar = CYdLidar()
lidar.setlidaropt(0, lidar_port)   # serial_port
lidar.setlidaropt(1, 230400)       # baudrate
lidar.setlidaropt(2, 0)            # LIDAR_TYPE
lidar.setlidaropt(3, 10.0)         # scan_frequency
lidar.setlidaropt(4, True)         # fixed_angle
lidar.setlidaropt(5, True)         # reversed
lidar.setlidaropt(6, True)         # auto_reconnect

if not lidar.initialize():
    print("❌ LIDAR başlatılamadı! Port ve baudrate kontrol et.")
    sys.exit(1)

print("✅ LIDAR başlatıldı.")

# -------------------------------
# 3️⃣ RealSense Başlat
# -------------------------------
pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)

try:
    pipeline.start(config)
    print("✅ RealSense başlatıldı.")
    time.sleep(2)  # 🔹 Kameranın sensörleri ısınsın
except Exception as e:
    print(f"❌ RealSense başlatılamadı: {e}")
    sys.exit(1)

# -------------------------------
# 4️⃣ Tarama ve Görüntü Döngüsü
# -------------------------------
try:
    while True:
        # --- LIDAR ---
        scan = LaserScan()
        if lidar.doProcessSimple(scan):
            print(f"{len(scan.points)} nokta alındı.")
            for p in scan.points[:5]:  # sadece ilk 5 noktayı örnek yazdır
                print(f"Açı: {p.angle:.2f}, Mesafe: {p.range:.2f}")

        # --- RealSense ---
        try:
            frames = pipeline.wait_for_frames(timeout_ms=1000)  # 🔹 1 saniye bekle
            color_frame = frames.get_color_frame()
            depth_frame = frames.get_depth_frame()
            if color_frame and depth_frame:
                print("📷 RealSense kareleri alındı.")
        except RuntimeError:
            print("⚠️ RealSense veri gelmedi, tekrar deniyor...")
            continuey

        time.sleep(0.1)

except KeyboardInterrupt:
    print("\n🛑 Program durduruldu.")
finally:
    lidar.turnOff()
    pipeline.stop()




