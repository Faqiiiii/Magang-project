import easyocr
import cv2
import re
import numpy as np

reader = easyocr.Reader(['en'])

def extract_numbers(image_stream, min_required):
    # Baca gambar dari stream (BytesIO)
    img_array = np.asarray(bytearray(image_stream.read()), dtype=np.uint8)
    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

    # Konversi ke grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Threshold agar kontras tinggi
    gray = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)[1]

    # OCR
    result = reader.readtext(gray, detail=0)
    text = " ".join(result)

    # Ambil angka desimal dengan koma atau angka bulat
    raw_numbers = re.findall(r"\d+,\d+|\d+", text)

    # Ubah koma jadi titik dan konversi ke float
    numbers = []
    for n in raw_numbers:
        try:
            numbers.append(float(n.replace(",", ".")))
        except ValueError:
            continue

    # Buang angka pertama hanya jika jumlahnya lebih dari minimum
    if len(numbers) > min_required:
        numbers = numbers[1:]

    return numbers