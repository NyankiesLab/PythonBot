import os
import subprocess
import time
import customtkinter as ctk
import re
import cv2
import numpy as np
import datetime
from PIL import Image
from pytesseract import pytesseract

from CoordinateTracker import CoordinatesTracker

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

app = ctk.CTk()
app.title("🌾 Farm Bot")
app.geometry("400x450")

available = 0
ping_rate = 0
device_serial = 'emulator-5554'

title_label = ctk.CTkLabel(app, text="Farm Bot", font=("Segoe UI", 20, "bold"))
title_label.pack(pady=(20, 10))

entry_vars = {}

def create_resource_input(label_text):
    frame = ctk.CTkFrame(app, fg_color="transparent")
    frame.pack(pady=5)
    label = ctk.CTkLabel(frame, text=label_text + ":", width=80, anchor="e")
    label.pack(side="left", padx=10)
    entry = ctk.CTkEntry(frame, width=60)
    entry.insert(0, "0")
    entry.pack(side="left")
    entry_vars[label_text.lower()] = entry

for label in ["March", "Corn", "Wood", "Stone", "Gold"]:
    create_resource_input(label)

def get_entry_int(name):
    try:
        return int(entry_vars[name].get())
    except:
        return 0


def start_farming():
    rss_tuple = [
        get_entry_int("corn"),
        get_entry_int("wood"),
        get_entry_int("stone"),
        get_entry_int("gold")
    ]
    print(f"Gönderilenler: {rss_tuple}")
    farm_loop(rss_tuple)

start_button = ctk.CTkButton(app, text="🚀 Başlat", command=start_farming, width=200, height=40)
start_button.pack(pady=30)


def run_adb_command(command):
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return result.stdout.decode(), result.stderr.decode()

def tab_process(rss_tuple):
    global ping_rate
    adb_tap(90, 810)
    gather_area, plus, minus, search = control_entry(rss_tuple)
    adb_tap(gather_area[0], gather_area[1])
    if ping_rate == 0:
        adb_tap(plus[0], plus[1])
    elif ping_rate > 3:
        adb_tap(minus[0], minus[1])
    adb_tap(search[0], search[1])

tracker = CoordinatesTracker()

def control_entry(rss_tuple):
    global ping_rate
    gather_area = plus = search = minus = 0
    if all(get_entry_int(k) == 0 for k in ["corn", "wood", "stone", "gold"]):
        update_resource_entry("corn", "plus", rss_tuple[0])
        update_resource_entry("wood", "plus", rss_tuple[1])
        update_resource_entry("stone", "plus", rss_tuple[2])
        update_resource_entry("gold", "plus", rss_tuple[3])
        ping_rate = 0
    time.sleep(0.5)
    if get_entry_int("corn") > 0:
        gather_area, plus, minus, search = (665, 950), (830, 605), (466, 610), (675, 735)
        update_resource_entry("corn", "minus", 1)
    elif get_entry_int("wood") > 0:
        gather_area, plus, minus, search = (955, 950), (1120, 605), (757, 610), (955, 735)
        update_resource_entry("wood", "minus", 1)
    elif get_entry_int("stone") > 0:
        gather_area, plus, minus, search = (1245, 950), (1405, 605), (1046, 610), (1235, 735)
        update_resource_entry("stone", "minus", 1)
    elif get_entry_int("gold") > 0:
        gather_area, plus, minus, search = (1535, 950), (1695, 605), (1327, 610), (1525, 735)
        update_resource_entry("gold", "minus", 1)
    return gather_area, plus, minus, search

def confirm_process():
    global ping_rate, available
    time.sleep(2)
    collect_control = (1277, 671, 1581, 783)
    find_button_control = (1408, 687, 1663, 785)
    take_and_pull_screenshot()
    crop_screenshot(find_button_control)
    match = find_template_in_image("screenshot.png", "Ara.png", threshold=0.68)
    if not match:
        x_rss_coordinate = extract_coordinate(1386, 283, 1433, 315)
        y_rss_coordinate = extract_coordinate(1457, 280, 1513, 315)
        crop_screenshot(collect_control)
        match = find_template_in_image("cropped_screenshot.png", "screenshot.png", threshold=0.70)
        if tracker.compare_coordinates(x_rss_coordinate, y_rss_coordinate) == 0:
            tracker.add_coordinate(x_rss_coordinate, y_rss_coordinate)
            if match:
                ping_rate = 0
                for coords in [(1423, 730), (1513, 215), (1400, 944)]:
                    adb_tap(*coords)
                    time.sleep(0.5)
        else:
            ping_rate += 1
            available += 1
    else:
        ping_rate += 1
        adb_tap(953, 530)

def farm_loop(rss_tuple):
    adb_tap(90, 980)
    time.sleep(1)
    adb_tap(90, 980)
    time.sleep(1)
    while True:
        global available
        map_control = (0, 890, 180, 1070)
        take_and_pull_screenshot()
        crop_screenshot(map_control)
        match = find_template_in_image("cropped_screenshot.png", "city.png", threshold=0.68)
        if match:
            adb_tap(90, 980)
            time.sleep(1)
        while not match:
            adb_tap(953, 530)
            time.sleep(1)
            take_and_pull_screenshot()
            match = find_template_in_image("screenshot.png", "Koordinat.png", threshold=0.70)
            if match:
                x = extract_coordinate(1386, 283, 1433, 315)
                y = extract_coordinate(1457, 280, 1513, 315)
                city_coordinate = f"X:{x} Y:{y}"
                if re.findall(r'^X:(\d{1,4}) Y:(\d{1,4})$', city_coordinate.strip()):
                    while True:
                        take_and_pull_screenshot()
                        queue = extract_number_from_image(1808, 200, 1870, 237)
                        match = re.findall(rf'^[0-{get_entry_int("march")}]/\d$', queue.strip())
                        if match:
                            available = int(queue[2:3]) - int(queue[0:1])
                        else:
                            available = 5
                        for _ in range(available):
                            tab_process(rss_tuple)
                            confirm_process()
                        if available == 0:
                            print(datetime.datetime.now())
                            adb_tap(1400, 901)
                            time.sleep(120)

def update_resource_entry(resource, operation, amount):
    entry = entry_vars[resource]
    try:
        value = int(entry.get())
        new_value = value + amount if operation == "plus" else value - amount
        entry.delete(0, "end")
        entry.insert(0, str(max(new_value, 0)))
    except ValueError:
        pass

def extract_coordinate(left, top, right, bottom, lang='eng'):
    pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    image = Image.open('screenshot.png').crop((left, top, right, bottom)).convert('L')
    img_np = np.array(image)
    processed = Image.fromarray(img_np)
    processed.save('cropped_screenshot.png')
    config = r'--oem 3 --psm 7 -c tessedit_char_whitelist=X:Y0123456789'
    return pytesseract.image_to_string(processed, config=config, lang=lang).strip()

def extract_number_from_image(left, top, right, bottom, format="queue", lang='tur'):
    pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    image = Image.open("screenshot.png").crop((left, top, right, bottom)).convert("L")
    output = Image.fromarray(np.array(image))
    output.save("cropped_screenshot.png")
    config = r'--oem 3 --psm 7 -c tessedit_char_whitelist=12345/' if format == "queue" else \
             r'--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789:'
    return pytesseract.image_to_string(output, config=config, lang=lang)

def crop_screenshot(crop_area, path='screenshot.png', out='cropped_screenshot.png'):
    with Image.open(path) as img:
        img.crop(crop_area).save(out, format='PNG')
    return out

def take_and_pull_screenshot():
    path_on_device = '/sdcard/screenshot.png'
    local_dir = 'C:/Users/nesba/PycharmProjects/FarmBot/'
    local_path = os.path.join(local_dir, 'screenshot.png')
    run_adb_command(f'adb -s {device_serial} shell screencap -p {path_on_device}')
    run_adb_command(f'adb -s {device_serial} pull {path_on_device} {local_path}')
    return local_path

def adb_tap(x, y):
    cmd = f'adb -s {device_serial} shell input tap {x} {y}'
    time.sleep(0.1)
    out, err = run_adb_command(cmd)
    print(f"Tıklama: ({x}, {y})") if not err else print(f"Hata: {err}")

def find_template_in_image(big_image_path, small_image_path, threshold=0.91, crop_region=None):
    big = cv2.imread(big_image_path)
    if big is None:
        print("Büyük resim yok.")
        return []
    if crop_region:
        x1, y1, x2, y2 = crop_region
        big = big[y1:y2, x1:x2]
    small = cv2.imread(small_image_path)
    if small is None:
        print("Küçük resim yok.")
        return []
    result = cv2.matchTemplate(big, small, cv2.TM_CCOEFF_NORMED)
    loc = np.where(result >= threshold)
    h, w, _ = small.shape
    matches = []
    for pt in zip(*loc[::-1]):
        cx = pt[0] + w // 2
        cy = pt[1] + h // 2
        print(f"Eşleşti: ({cx}, {cy})")
        matches.append(((pt[0], pt[1]), (pt[0]+w, pt[1]+h)))
        break
    return matches

if __name__ == "__main__":
    app.mainloop()
