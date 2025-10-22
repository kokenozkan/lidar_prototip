import time
from ydlidar import CYdLidar

def main():
    # LIDAR objesi oluştur
    lidar = CYdLidar()

    # Parametre ayarları
    lidar.setlidaropt(lidar.SERIAL_PORT, "/dev/ttyUSB0")  # LIDAR USB port
    lidar.setlidaropt(lidar.LIDAR_TYPE, lidar.TYPE_TRIANGLE)  # Model tipi
    lidar.setlidaropt(lidar.SCAN_FREQUENCY, 10.0)  # Hz, tarama hızı

    # Başlat
    if not lidar.initialize():
        print("LIDAR başlatılamadı!")
        return

    print("LIDAR başlatıldı. Tarama başlıyor...")
    try:
        while True:
            scan = lidar.doProcessSimple()
            if scan:
                for point in scan:
                    print(f"Açı: {point.angle:.2f}°, Mesafe: {point.range:.2f}m")
            else:
                print("Tarama verisi yok.")
            time.sleep(0.1)  # Çok hızlı dönmemesi için küçük gecikme
    except KeyboardInterrupt:
        print("\nTarama durduruldu. LIDAR kapatılıyor...")
    finally:
        lidar.turnOff()
        lidar.disconnect()
        print("LIDAR bağlantısı kapatıldı.")

if __name__ == "__main__":
    main()

