#!/usr/bin/env python3
"""
Create a simple icon for the JARVIS AI Assistant
"""

try:
    from PIL import Image, ImageDraw, ImageFont
    import os
    
    def create_jarvis_icon():
        """Create a simple JARVIS icon"""
        # Create a 256x256 image with transparent background
        size = 256
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Draw a modern circular background
        margin = 20
        circle_bbox = [margin, margin, size - margin, size - margin]
        
        # Gradient-like effect with multiple circles
        colors = [
            (13, 17, 23, 255),    # Dark background
            (88, 166, 255, 255),  # Blue accent
            (56, 189, 248, 255),  # Light blue
        ]
        
        # Draw background circle
        draw.ellipse(circle_bbox, fill=colors[0])
        
        # Draw inner circles for depth
        inner_margin = 40
        inner_bbox = [inner_margin, inner_margin, size - inner_margin, size - inner_margin]
        draw.ellipse(inner_bbox, outline=colors[1], width=4)
        
        # Draw robot face elements
        # Eyes
        eye_size = 20
        eye_y = size // 2 - 30
        left_eye = [size // 2 - 40, eye_y, size // 2 - 40 + eye_size, eye_y + eye_size]
        right_eye = [size // 2 + 20, eye_y, size // 2 + 20 + eye_size, eye_y + eye_size]
        
        draw.ellipse(left_eye, fill=colors[2])
        draw.ellipse(right_eye, fill=colors[2])
        
        # Mouth (smile)
        mouth_y = size // 2 + 20
        mouth_bbox = [size // 2 - 30, mouth_y, size // 2 + 30, mouth_y + 30]
        draw.arc(mouth_bbox, start=0, end=180, fill=colors[2], width=4)
        
        # Add some tech elements (small dots around the circle)
        for angle in range(0, 360, 30):
            import math
            x = size // 2 + int(90 * math.cos(math.radians(angle)))
            y = size // 2 + int(90 * math.sin(math.radians(angle)))
            dot_size = 4
            draw.ellipse([x - dot_size, y - dot_size, x + dot_size, y + dot_size], fill=colors[1])
        
        # Save as ICO file
        icon_path = "jarvis_icon.ico"
        img.save(icon_path, format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])
        
        print(f"✅ Icon created: {icon_path}")
        return icon_path
    
    if __name__ == "__main__":
        create_jarvis_icon()
        
except ImportError:
    print("⚠️ PIL (Pillow) not available. Installing...")
    import subprocess
    subprocess.run(["pip", "install", "Pillow"], check=True)
    print("✅ Pillow installed. Please run the script again.")
