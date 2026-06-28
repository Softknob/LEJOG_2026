import os
import csv
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

# --- Configuration ---
IMAGE_FOLDER = "images"  # Path to your photo directory
OUTPUT_CSV = "data/photo_coordinates.csv"  # Where to save the CSV file


def get_decimal_from_dms(dms, ref):
    """Converts Degrees/Minutes/Seconds tuple to Decimal Degrees."""
    if not dms or not ref:
        return None
    
    # Handle older Pillow versions returning tuples vs rational numbers
    degrees = float(dms[0])
    minutes = float(dms[1])
    seconds = float(dms[2])
    
    decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)
    if ref in ['S', 'W']:
        decimal = -decimal
    return round(decimal, 6)


def extract_gps_data(image_path):
    """Extracts latitude and longitude from image EXIF metadata."""
    try:
        with Image.open(image_path) as img:
            exif_data = img._getexif()
            if not exif_data:
                return None, None
            
            gps_info = {}
            for tag, value in exif_data.items():
                decoded = TAGS.get(tag, tag)
                if decoded == 'GPSInfo':
                    for t in value:
                        sub_tag = GPSTAGS.get(t, t)
                        gps_info[sub_tag] = value[t]
            
            # Check if required GPS fields are populated
            if 'GPSLatitude' in gps_info and 'GPSLongitude' in gps_info:
                lat = get_decimal_from_dms(gps_info['GPSLatitude'], gps_info.get('GPSLatitudeRef'))
                lon = get_decimal_from_dms(gps_info['GPSLongitude'], gps_info.get('GPSLongitudeRef'))
                return lat, lon
                
    except Exception as e:
        print(f"Error processing {image_path}: {e}")
        
    return None, None


def main():
    # Ensure output directory exists
    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    
    print(f"Scanning folder: '{IMAGE_FOLDER}' for images...")
    
    with open(OUTPUT_CSV, mode='w', newline='', encoding='utf-8') as csv_file:
        writer = csv.writer(csv_file)
        # Write CSV Header row
        writer.writerow(["image_name", "latitude", "longitude"])
        
        count = 0
        # Loop through folder contents
        for file_name in os.listdir(IMAGE_FOLDER):
            if file_name.lower().endswith(('.jpg', '.jpeg')):
                full_path = os.path.join(IMAGE_FOLDER, file_name)
                lat, lon = extract_gps_data(full_path)
                
                if lat is not None and lon is not None:
                    # Save relative path reference for Leaflet mapping asset use
                    relative_path = f"images/{file_name}"
                    writer.writerow([relative_path, lat, lon])
                    count += 1
                else:
                    print(f"Skipped: '{file_name}' (No GPS Metadata found)")
                    
    print(f"\nSuccess! Saved {count} image locations to '{OUTPUT_CSV}'.")


if __name__ == "__main__":
    main()
