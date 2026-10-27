# -*- coding: utf-8 -*-
"""ساخت آیکون LeaguePro.ico (نمایشگر امتیاز فوتبال) در چند اندازه."""
from PIL import Image, ImageDraw

S = 512
img = new = Image.new("RGBA", (S, S), (0, 0, 0, 0))
d = ImageDraw.Draw(img)

# پس‌زمینه دایره‌ای سبز چمنی با حاشیه طلایی
d.ellipse([8, 8, S - 8, S - 8], fill=(16, 128, 48, 255), outline=(255, 200, 40, 255), width=14)

# خطوط سفید زمین (وسط و دایره مرکزی)
d.line([(S // 2, 60), (S // 2, S - 60)], fill=(255, 255, 255, 200), width=8)
d.ellipse([S // 2 - 90, S // 2 - 90, S // 2 + 90, S // 2 + 90], outline=(255, 255, 255, 200), width=8)

# تابلوی امتیاز (اسکوربورد) مشکی با حاشیه نقره‌ای
bx0, by0, bx1, by1 = 70, 150, S - 70, S - 150
d.rounded_rectangle([bx0, by0, bx1, by1], radius=30, fill=(20, 20, 30, 255), outline=(200, 200, 210, 255), width=8)

# اعداد طلایی "3" و "1" روی تابلو
def digit_segments(dr, x, y, w, h, ch, color):
    t = max(10, w // 6)
    """رسم رقم هفت‌قسمتی ساده."""
    segs = {
        'a': [(x + t, y), (x + w - t, y), (x + w - t, y + t), (x + t, y + t)],
        'b': [(x + w - t, y), (x + w, y + t), (x + w, y + h // 2 - t // 2), (x + w - t, y + h // 2 - t // 2)],
        'c': [(x + w - t, y + h // 2 + t // 2), (x + w, y + h // 2 + t), (x + w, y + h - t), (x + w - t, y + h - t)],
        'd': [(x + t, y + h - t), (x + w - t, y + h - t), (x + w - t, y + h), (x + t, y + h)],
        'e': [(x, y + h // 2 + t // 2), (x + t, y + h // 2 + t), (x + t, y + h - t), (x, y + h - t)],
        'f': [(x, y + t), (x + t, y + t), (x + t, y + h // 2 - t // 2), (x, y + h // 2 - t // 2)],
        'g': [(x + t, y + h // 2 - t // 2), (x + w - t, y + h // 2 - t // 2), (x + w - t, y + h // 2 + t // 2), (x + t, y + h // 2 + t // 2)],
    }
    on = {
        '0': 'abcdef', '1': 'bc', '2': 'abged', '3': 'abgcd', '4': 'fgbc',
        '5': 'afgcd', '6': 'afgcde', '7': 'abc', '8': 'abcdefg', '9': 'abcfgd',
    }
    for s in on.get(ch, ""):
        dr.polygon(segs[s], fill=color)

gold = (255, 205, 60, 255)
digit_segments(d, bx0 + 70, by0 + 45, 90, 120, '3', gold)
d.rectangle([bx0 + 215, by0 + 60, bx0 + 235, by0 + 80], fill=gold)
d.rectangle([bx0 + 215, by0 + 130, bx0 + 235, by0 + 150], fill=gold)
digit_segments(d, bx0 + 270, by0 + 45, 90, 120, '1', gold)

# توپ فوتبال کوچک پایین برنامه
cx, cy, r = S // 2, S - 78, 42
d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 255, 255, 255), outline=(30, 30, 30, 255), width=6)
d.polygon([(cx, cy - 18), (cx + 17, cy - 6), (cx + 10, cy + 15), (cx - 10, cy + 15), (cx - 17, cy - 6)], fill=(30, 30, 30, 255))

img.save("/workspace/assets/LeaguePro.ico", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
img.save("/workspace/assets/LeaguePro.png")
print("OK: assets/LeaguePro.ico + assets/LeaguePro.png")
