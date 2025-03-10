import os
import subprocess
import time
import tkinter as tk
import re
import cv2
import numpy as np
from PIL import Image
from pytesseract import pytesseract

from CoordinateTracker import CoordinatesTracker

available = 0
ping_rate = 0
# Cihaz seri numarasını burada bir kez tanımlıyoruz
device_serial = 'localhost:5565'

# Tkinter arayüzü kurma
root = tk.Tk()
root.title("Farm Bot")
root.geometry("500x500")

march_label = tk.Label(root, text="March:")
march_label.pack(pady=(20, 0))
march_entry = tk.Spinbox(root, from_=0, to=5, width=5)
march_entry.pack(pady=(0, 10))

# Corn için Spinbox
corn_label = tk.Label(root, text="Corn:")
corn_label.pack(pady=(20, 0))
corn_entry = tk.Spinbox(root, from_=0, to=5, width=5)
corn_entry.pack(pady=(0, 10))

# Wood için Spinbox
wood_label = tk.Label(root, text="Wood:")
wood_label.pack(pady=(20, 0))
wood_entry = tk.Spinbox(root, from_=0, to=5, width=5)
wood_entry.pack(pady=(0, 10))

# Stone için Spinbox
stone_label = tk.Label(root, text="Stone:")
stone_label.pack(pady=(20, 0))
stone_entry = tk.Spinbox(root, from_=0, to=5, width=5)
stone_entry.pack(pady=(0, 10))

# Gold için Spinbox
gold_label = tk.Label(root, text="Gold:")
gold_label.pack(pady=(20, 0))
gold_entry = tk.Spinbox(root, from_=0, to=5, width=5)
gold_entry.pack(pady=(0, 10))


# Start butonu
def start_farming():
    # Kullanıcının girdiği değerleri alır
    corn = corn_entry.get()
    wood = wood_entry.get()
    stone = stone_entry.get()
    gold = gold_entry.get()
    rss_tuple = [int(corn_entry.get()),int(wood_entry.get()),int(stone_entry.get()),int(gold_entry.get())]
    print(f"Corn: {corn}, Wood: {wood}, Stone: {stone}, Gold: {gold}")
    farm_loop(rss_tuple)


start_button = tk.Button(root, text="Start", command=start_farming)
start_button.pack(pady=20)


# ADB komutlarını çalıştırma
def run_adb_command(command):
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return result.stdout.decode(), result.stderr.decode()


# Şablon eşleştirme
def tab_process(rss_tuple):
    global ping_rate
    gather_area = 0
    plus = 0
    search = 0
    minus = 0
    adb_tap(90, 810)
    print(int(corn_entry.get()))
    if(int(corn_entry.get()) == 0 and int(wood_entry.get()) == 0  and int(stone_entry.get()) == 0  and int(gold_entry.get()) == 0):
        update_resource_entry("corn","plus",rss_tuple[0])
        update_resource_entry("wood", "plus", rss_tuple[1])
        update_resource_entry("stone", "plus", rss_tuple[2])
        update_resource_entry("gold", "plus", rss_tuple[3])
        ping_rate = 0
    time.sleep(0.5)
    if int(corn_entry.get()) > 0:
        gather_area = (665, 950)
        plus = (830, 605)
        minus =(466,610)
        search = (675, 735)
        update_resource_entry("corn","minus",1)
    elif int(wood_entry.get()) > 0:
        gather_area = (955, 950)
        plus = (1120, 605)
        minus = (757,610)
        search = (955, 735)
        update_resource_entry("wood","minus",1)
    elif int(stone_entry.get()) > 0:
        gather_area = (1245, 950)
        plus = (1405, 605)
        minus = (1046, 610)
        search = (1235, 735)
        update_resource_entry("stone","minus",1)
    elif int(gold_entry.get()) > 0:
        gather_area = (1535, 950)
        plus = (1695, 605)
        minus =(1327,610)
        search = (1525, 735)
        update_resource_entry("gold","minus",1)

    adb_tap(gather_area[0], gather_area[1])
    if ping_rate == 0:
        adb_tap(plus[0], plus[1])
    elif ping_rate > 5:
        adb_tap(minus[0], minus[1])
    adb_tap(search[0], search[1])


tracker = CoordinatesTracker()


def confirm_process():
    global ping_rate
    time.sleep(2)

    adb_tap(953, 530)  # kaynak
    time.sleep(1)
    collect_control = (1277, 671, 1581, 783)
    take_and_pull_screenshot()
    x_rss_coordinate = extract_coordinate(1386, 283, 1433, 315)  # X Kaynak koordinatını kaydettik.
    y_rss_coordinate = extract_coordinate(1457, 280, 1513, 315)  # Y Kaynak koordinatını kaydettik.
    crop_screenshot(collect_control)
    match = find_template_in_image("cropped_screenshot.png", "screenshot.png", threshold=0.70)
    valid = tracker.compare_coordinates(x_rss_coordinate, y_rss_coordinate)
    if valid == 0:
        tracker.add_coordinate(x_rss_coordinate, y_rss_coordinate)
        if match:
            ping_rate = 0
            adb_tap(1423, 730)  # Confirm
            time.sleep(0.5)
            adb_tap(1513, 215)  # Confirm
            time.sleep(0.5)
            adb_tap(1400, 944)
            time.sleep(0.5)
    else:
        global available
        ping_rate += 1
        available += 1

def farm_loop(rss_tuple):
    adb_tap(90, 980)  # Map
    time.sleep(1)
    adb_tap(90, 980)  # Map
    time.sleep(1)
    while True:
        global available
        #City/Map control
        map_control = (0, 890, 180, 1070)
        take_and_pull_screenshot()
        crop_screenshot(map_control)
        match = find_template_in_image("cropped_screenshot.png", "city.png", threshold=0.68)
        if match:
            adb_tap(90, 980)  # Map
            time.sleep(1)
            match = False
        while not match:
            adb_tap(953, 530)  # Şehir
            time.sleep(1)
            take_and_pull_screenshot()
            match = find_template_in_image(big_image_path="screenshot.png", small_image_path="Koordinat.png",
                                           threshold=0.60)
            if match:
                time.sleep(0.2)
                x_city_coordinate = extract_coordinate(1386, 283, 1433, 315)  # X Şehir koordinatını kaydettik.
                y_city_coordinate = extract_coordinate(1457, 280, 1513, 315)  # Y Şehir koordinatını kaydettik.
                city_coordinate = "X:" + x_city_coordinate + " Y:" + y_city_coordinate
                match = re.findall(r'^X:(\d{1,4}) Y:(\d{1,4})$', city_coordinate.strip())
                if match:
                    # Queue control
                    queue = 0
                    while True:
                        take_and_pull_screenshot()
                        queue = extract_number_from_image(1808, 200, 1870, 237)
                        queue_number = re.findall(rf'^[0-{march_entry.get()}]/{march_entry.get()}$', queue.strip())
                        if queue_number:
                            # Free march
                            available = int(queue[2:3]) - int(queue[0:1])
                            for i in range(available):
                                tab_process(rss_tuple)
                                confirm_process()
                                available -= 1
                        else:
                            print("Okumadı. 0/0")
                            available = 5
                            for i in range(available):
                                tab_process(rss_tuple)
                                confirm_process()
                                available -= 1

                        if available == 0:
                            time.sleep(180)

                    else:
                        print("Koordinatlar düzgün okunmadı.")

def update_resource_entry(resource, operation, amount):

    resource_map = {
        "corn": corn_entry,
        "stone": stone_entry,
        "wood": wood_entry,
        "gold": gold_entry
    }

    # Doğru Spinbox'u seç
    if resource not in resource_map:
        raise ValueError(f"Geçersiz kaynak: {resource}. Geçerli kaynaklar: corn, stone, wood, gold")

    if operation not in ["plus", "minus"]:
        raise ValueError(f"Geçersiz işlem türü: {operation}. Geçerli işlemler: 'plus', 'minus'")

    entry = resource_map[resource]  # İlgili Spinbox'u al

    try:
        # Mevcut değeri al
        current_value = int(entry.get())

        # İşlemi uygula
        if operation == "plus":
            new_value = current_value + amount
        elif operation == "minus":
            new_value = current_value - amount

        # Spinbox'u güncelle
        entry.delete(0, "end")        # Spinbox içeriğini temizle
        entry.insert(0, str(new_value))  # Yeni değeri Spinbox'a yaz
    except ValueError:
        raise ValueError(f"{resource} Spinbox değerini güncellemek için geçerli bir sayı değil.")

def extract_coordinate(left, top, right, bottom, lang='eng'):

    # Tesseract'ın kurulu olduğu dizini belirtin
    pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

    # Görüntüyü açın
    image = Image.open('screenshot.png')

    # Belirli bir bölgeyi kırpma
    cropped_image = image.crop((left, top, right, bottom))

    # Görüntüyü grileştir
    gray_image = cropped_image.convert('L')

    # NumPy dizisine çevir
    img_np = np.array(gray_image)

    # Kontrast artırma (isteğe bağlı)
    # img_np = cv2.equalizeHist(img_np)

    # Threshold uygulama (OTSU kullanıyoruz)
    # _, thresh = cv2.threshold(img_np, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)

    # İsterseniz gürültü azaltma, erozyon vb. ekleyebilirsiniz
    # thresh = cv2.medianBlur(thresh, 3)

    # OCR ayarları
    custom_config = r'--oem 3 --psm 7 -c tessedit_char_whitelist=X:Y0123456789'

    # Threshold sonrası görüntüyü PIL formatına geri çevir
    processed_image = Image.fromarray(img_np)

    # İsteğe bağlı: Debug için işlenen görüntüyü kaydedin
    processed_image.save('cropped_screenshot.png')

    # OCR ile metni çıkarma
    text = pytesseract.image_to_string(processed_image, config=custom_config, lang=lang)

    return text.strip()


def extract_number_from_image(left, top, right, bottom, format="queue",
                              lang='tur'):

    # Tesseract'ın kurulu olduğu dizini belirtin
    pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

    # Görüntüyü açın
    image = Image.open(f'screenshot.png')

    # Belirli bir bölgeyi kırpma
    cropped_image = image.crop((left, top, right, bottom))

    # Görüntüyü grileştirme
    gray_image = cropped_image.convert('L')

    # Görüntüyü numpy dizisine çevirme
    sharpened_image_cv = np.array(gray_image)

    # Keskinleştirilen görüntüyü geri PIL formatına çevir
    sharpened_image = Image.fromarray(sharpened_image_cv)

    # Kırpılan ve işlenen görüntüyü sıralı isimle kaydetme
    output_path = f'cropped_screenshot.png'
    sharpened_image.save(output_path)

    # OCR ile metni çıkarma
    if format == "queue":
        custom_config = r'--oem 3 --psm 7 -c tessedit_char_whitelist=12345/'
    else:
        custom_config = r'--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789:'

    text = pytesseract.image_to_string(sharpened_image, config=custom_config, lang=lang)

    return text


def crop_screenshot(crop_area, local_screenshot_path='screenshot.png', cropped_filename='cropped_screenshot.png'):

    # local_screenshot_path'tan gelen görüntüyü aç
    with Image.open(local_screenshot_path) as img:
        # Belirtilen alana göre crop işlemini yap
        cropped_img = img.crop(crop_area)

        # Cropped görüntüyü aynı dizine kaydet
        cropped_path = os.path.join(os.path.dirname(local_screenshot_path), cropped_filename)
        cropped_img.save(cropped_path, format='PNG')

        return cropped_path


def take_and_pull_screenshot(device_serial='localhost:5565'):


    # Take a screenshot
    screenshot_path_on_device = '/sdcard/screenshot.png'
    output, error = run_adb_command(f'adb -s {device_serial} shell screencap -p {screenshot_path_on_device}')

    # Yerel dosya yolunu oluşturun
    local_directory = 'C:/Users/nesba/PycharmProjects/FarmBot/'
    local_screenshot_path = os.path.join(local_directory, f'screenshot.png')

    # Pull the screenshot to the local directory with the new filename
    output, error = run_adb_command(f'adb -s {device_serial} pull {screenshot_path_on_device} {local_screenshot_path}')

    # Global sayaç artırılır

    return (output, error, local_screenshot_path)


def adb_tap(x, y, device_serial='localhost:5565'):
    """ADB kullanarak Bluestacks ekranında belirtilen koordinatlara tıklar."""
    command = f'adb -s {device_serial} shell input tap {x} {y}'
    output, error = run_adb_command(command)
    if error:
        print(f"Hata: {error}")
    else:
        print(f"ADB ile tıklama gerçekleştirildi: ({x}, {y})")


def swipe_down(start_x=500, start_y=1200, end_x=500, end_y=800, duration=1000):
    device_serial = 'localhost:5565'
    cmd = [
        "adb", "-s", device_serial, "shell", "input", "swipe",
        str(start_x), str(start_y), str(end_x), str(end_y), str(duration)
    ]
    # Hata ayıklamak için geçici olarak check=False ve outputları yazdırabilirsiniz:
    result = subprocess.run(cmd, capture_output=True, text=True)
    print("stdout:", result.stdout)
    print("stderr:", result.stderr)
    # Hata yoksa tekrar check=True yapabilirsiniz.
    if result.returncode != 0:
        raise RuntimeError(f"Swipe komutu başarısız oldu: {result.stderr}")

def find_template_in_image(big_image_path, small_image_path, threshold=0.91, crop_region=None):
    big_image = cv2.imread(big_image_path)
    if big_image is None:
        print(f"Büyük resim {big_image_path} yüklenemedi!")
        return []

    if crop_region is None:
        crop_region = (0, 0, big_image.shape[1], big_image.shape[0])

    x1, y1, x2, y2 = crop_region
    big_image = big_image[y1:y2, x1:x2]
    if big_image.size == 0:
        print("Geçersiz kırpma bölgesi!")
        return []

    small_image = cv2.imread(small_image_path)
    if small_image is None:
        print(f"Küçük resim {small_image_path} yüklenemedi!")
        return []

    result = cv2.matchTemplate(big_image, small_image, cv2.TM_CCOEFF_NORMED)
    locations = np.where(result >= threshold)

    h, w, _ = small_image.shape
    matching_regions = []

    for point in zip(*locations[::-1]):
        top_left = point
        bottom_right = (top_left[0] + w, top_left[1] + h)
        matching_regions.append((top_left, bottom_right))

        center_x = top_left[0] + w // 2 + x1
        center_y = top_left[1] + h // 2 + y1

        # Eşleşen resim bulundu, ancak tıklama yapılmayacak
        print(f"Eşleşen resim bulundu, koordinatlar: {center_x}, {center_y}")

        break  # İlk eşleşme sonrası döngüden çık

    cv2.waitKey(0)
    cv2.destroyAllWindows()
    return matching_regions


if __name__ == "__main__":
    root.mainloop()
