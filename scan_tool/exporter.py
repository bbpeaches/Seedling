import sys
import platform

def clean_text_for_image(text):
    """
    Remove emojis that Pillow struggles to render.
    """
    # Remove our custom folder/file icons
    cleaned = text.replace('📁 ', '').replace('📄 ', '')
    cleaned = cleaned.replace('📁', '').replace('📄', '')
    return cleaned

def get_best_font(font_size=18):
    """
    Intelligently select a font that supports Chinese characters based on the OS.
    """
    try:
        from PIL import ImageFont # type: ignore
    except ImportError:
        return None

    system = platform.system()
    
    # macOS: PingFang is the best for Chinese, Menlo for fallback code font
    if system == "Darwin":
        font_paths = ["PingFang.ttc", "Hiragino Sans GB.ttc", "Arial Unicode.ttf", "Menlo.ttc"]
    # Windows: Microsoft YaHei
    elif system == "Windows":
        font_paths = ["msyh.ttc", "simhei.ttf", "simsun.ttc", "consola.ttf"]
    # Linux: Noto Sans or MicroHei
    else:
        font_paths = ["NotoSansCJK-Regular.ttc", "wqy-microhei.ttc", "DejaVuSansMono.ttf"]
        
    for font_name in font_paths:
        try:
            return ImageFont.truetype(font_name, font_size)
        except IOError:
            continue
            
    return ImageFont.load_default()

def create_image_from_text(text, output_file, line_count):
    if line_count > 1500:
        print(f"\n⚠️ WARNING: Directory too large ({line_count} lines). Generating an image may cause memory overflow.")
        return False

    try:
        from PIL import Image, ImageDraw, ImageFont # type: ignore
    except ImportError:
        print("\n❌ ERROR: Exporting as image requires the Pillow library (pip install Pillow).")
        return False
    
    clean_text = clean_text_for_image(text)
    font_size = 18
    font = get_best_font(font_size)
    if font is None:
        font = ImageFont.load_default()

    lines = clean_text.split('\n')
    dummy_img = Image.new('RGB', (1, 1))
    draw = ImageDraw.Draw(dummy_img)
    
    max_width, total_height = 0, 0
    line_heights = []
    
    # Calculate dimensions
    for line in lines:
        try:
            bbox = draw.textbbox((0, 0), line, font=font)
            width = bbox[2] - bbox[0]
            height = bbox[3] - bbox[1]
        except AttributeError:
            width, height = draw.textsize(line, font=font)
            
        max_width = max(max_width, width)
        line_heights.append(max(height, font_size) + 6) 
        
    img_width = int(max_width + 80)  
    img_height = int(sum(line_heights) + 80) 
    
    bg_color = (40, 44, 52)
    text_color = (171, 178, 191)
    
    image = Image.new('RGB', (img_width, img_height), color=bg_color)
    draw = ImageDraw.Draw(image)
    
    y_offset = 40
    total_lines = len(lines)
    
    # Draw with Progress Bar
    for i, line in enumerate(lines):
        draw.text((40, y_offset), line, font=font, fill=text_color)
        y_offset += line_heights[i]
        
        # Update progress bar every 5%
        if i % max(1, (total_lines // 20)) == 0 or i == total_lines - 1:
            percent = int((i + 1) / total_lines * 100)
            bar = '█' * (percent // 5) + '-' * (20 - (percent // 5))
            sys.stdout.write(f"\r🎨 Rendering Image: [{bar}] {percent}% ")
            sys.stdout.flush()
            
    print() # New line after progress bar finishes
    
    try:
        image.save(output_file)
        return True
    except Exception as e:
        print(f"\n❌ ERROR saving image: {e}")
        return False