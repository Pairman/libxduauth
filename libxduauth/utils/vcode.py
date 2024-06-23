def _image_binarize(img, bg_color = 255, text_color = 0):
    # binarize an captcha image for cli view
    # color atop every column is treated as its background color
    # other different colors are filled to text_color
    img = img.convert('L')
    pxl = img.load()
    w, h = img.size
    for x in range(w):
        top_color = pxl[x, 0]
        for y in range(h):
            pxl[x, y] = bg_color if pxl[x, y] == top_color else text_color
    return img


def _image_to_ascii(img, size = (80, 16), invert_pallete = True):
    # convert image to ascii art for cli view
    # given char dimension 24*16, optimal sizes are
    # (80, 16) for xk, (80, 21) for rsbbs
    if invert_pallete:
        chs = '@&%QWNM0gB$#DR8mHXKAUbGOpV4d9h6Pkqwaxoenut1ivsz/*cr!+<>;=^:\'-.` '
    else:
        chs = ' `.-\':^=;><+!rc*/zsvi1tuneoxawqkP6h9d4VpOGbUAKXHm8RD#$Bg0MNWQ%&@'
    w, h = size
    img.load()
    im = img.im.convert('L').resize((w, h))
    return '\n'.join(''.join(
        chs[im[i] // 4] for i in range(y, y + w)
    ) for y in range(0, w*h, w))


def _solve_slider_captcha(big_img, small_img, border = 24):
    # ncc based slider captcha solver with ~0.65 accuracy for 24 bordered ids ones
    # the given images must be rgba moded
    # returns slider offset
    big_img.load()
    small_img.load()
    # align slider piece and cut off uninterested areas
    # lut literal saves ~1ms processing time
    x_l, y_t, x_r, y_b = small_img.im.getband(3).point((
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1
    ), None).getbbox()
    # avoid interferance from partial transparent areas
    x_l += border
    y_t += border
    x_r -= border
    y_b -= border
    # calculate template
    template = small_img.im.crop((
        x_l, y_t, x_r, y_b
    )).convert('L', 3)
    mean_t = sum(template) / len(template)
    template = [v - mean_t for v in template]
    ncc_max = x_max = 0
    width_w = x_r - x_l
    height_w = y_b - y_t
    len_w = width_w * height_w
    width_g = big_img.width - small_img.width + width_w - 1
    # crop background
    grayscale = big_img.im.crop((
        x_l + 1, y_t, x_l + width_g, y_b
    )).convert('L', 3)
    # slide window and calculate ncc per 2px
    for x in range(0, width_g - width_w, 2):
        window = grayscale.crop((x, 0, x + width_w, height_w))
        mean_w = sum(window) / len_w
        sum_wt = 0
        sum_ww = 0
        for w, t in zip(window, template):
            w -= mean_w
            sum_wt += w * t
            sum_ww += w * w
        ncc = sum_wt / sum_ww
        if ncc > ncc_max:
            ncc_max = ncc
            x_max = x
    return x_max
