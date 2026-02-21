#!python

# pip install --upgrade pip
# pip install cryptography
# pip install rich
# pip install Pillow

import sys, os, time, shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
from PIL import Image, ImageOps
import concurrent.futures
from rich.console import Console
from rich.progress import Progress, BarColumn, TimeElapsedColumn, Task
from rich.text import Text
from rich.padding import Padding
from rich.theme import Theme
from rich.panel import Panel
import math

first_bad_date = "2021-12-26"

src_path = "/Users/randy/Sites/PortlandAve"
dest_path = "/Users/randy/Sites/PortlandAve-ThumbFix"

src_folders = ["Local", "travel"]

thumb_folder_root = "thumbnails"
thumb_folder_root_2x = "thumbnails@2x"
thumb_folder_root_3x = "thumbnails@3x"
picture_folder_root = "pictures"

thumb_name_root = "thumb-"
picture_name_root = "picture-"

theme = Theme({
			"progress.percentage": "white",
			"progress.remaining": "green",
			"progress.elapsed": "cyan",
			"bar.complete": "green",
			"bar.finished": "green",
			"bar.pulse": "green",
			"repr.ellipsis": "white",
			"repr.number": "white",
			"repr.path": "white",
			"repr.filename": "white"
			# "progress.data.speed": "white",
			# "progress.description": "none",
			# "progress.download": "white",
			# "progress.filesize": "white",
			# "progress.filesize.total": "white",
			# "progress.spinner": "white",
			})

console = Console(theme=theme)

console_mid_line = False

def print_now(str):
	global console_mid_line
	console.print(str, end="")
	console_mid_line = True

def print_cr(*args):
	global console_mid_line
	console.print(*args)
	console_mid_line = False

def print_error(*args, dest_console=console):
	global console_mid_line
	message = args[0] if len(args) >= 1 else None
	item = args[1] if len(args) >= 2 else None
	error_message = args[2] if len(args) >= 3 else None

	if item and not isinstance(item, str):
		item = str(item)
	if error_message and not isinstance(error_message, str):
		error_message = str(error_message)

	error_color = "[bold red]"
	error_item_color = "[magenta]"
	error_message_color = "[yellow]"

	parts = []
	if message:
		parts.extend([error_color, message])
	if item:
		parts.extend([error_item_color, item])
	if error_message:
		if len(parts)>0:
			parts.extend([error_color, " - "]) 
		parts.extend([error_message_color, error_message]) 

	if dest_console == console and console_mid_line:
		console.print()
		console_mid_line = False
	dest_console.print("".join(parts))

def createFolder(path):
	if "." in path:
		path = os.path.dirname(path)
	try:
		os.makedirs(path, exist_ok=True)
		return True
	except OSError as e:
		print_cr(f"Error creating folder '{path}': {e}")
		return False
	
def size_of_image_file(file_ref):
	image_size = None

	try:
		image = Image.open(file_ref)
		# image.load()
		image_size = image.size
	except:
		pass

	return image_size

def scaled_size(input_size, max_size):
	width, height = input_size
	max_size = min(max_size, max(width, height))
	
	if width > height:
		height = round(max_size / width * height)
		width = max_size
	else:
		width = round(max_size / height * width)
		height = max_size
	
	return (width, height)
	
def save_image(image, path, profile):
	with open(path, "wb") as file:
		image.save(file, "JPEG", quality="high", icc_profile=profile)

def save_scaled(image, size, path, sampling, profile):
	scaled_image = image.resize(size, resample=sampling)
	save_image(scaled_image, path, profile)
	return (scaled_image)

def date_from_string(date_string):
	date_string = date_string[:10]
	if len(date_string)>0:
		try:
			return datetime.strptime(date_string, "%Y-%m-%d")
		except:
			pass	
	return None

def pluralize(str, count, pad=False):
	return f"{count:d} {str}{'s' if count != 1 else ' ' if pad else ''}"

def fixThumb(image, dest_pathx2, dest_pathx3, max_size):
	createFolder(dest_pathx2)
	createFolder(dest_pathx3)
		
	image.load()
	profile = image.info.get("icc_profile", None)
	save_scaled(image, scaled_size(image.size, max_size*2), dest_pathx2, Image.LANCZOS, profile)
	save_scaled(image, scaled_size(image.size, max_size*3), dest_pathx3, Image.LANCZOS, profile)

def fixThumbs(src_folder, dest_folder):
	src_pictures_folder = os.path.join(src_folder, picture_folder_root)
	src_thumbs_folder = os.path.join(src_folder, thumb_folder_root)
	dest_thumbs_folderx2 = os.path.join(dest_folder, thumb_folder_root_2x)
	dest_thumbs_folderx3 = os.path.join(dest_folder, thumb_folder_root_3x)

	save_count = 0

	# Iterate over all files in the pictures folder
	for filename in os.listdir(src_pictures_folder):
		if not filename.startswith(picture_name_root):
			continue
			
		src_picture_path = os.path.join(src_pictures_folder, filename)
		
		# Skip if not a file
		if not os.path.isfile(src_picture_path):
			continue
		
		# Load the source image
		image = Image.open(src_picture_path)
		if image is None:
			print_error("Failed to load image:", src_picture_path)
			continue
		
		# Find the corresponding 1x thumbnail
		thumb_filename = filename.replace(picture_name_root, thumb_name_root)
		src_thumb_path = os.path.join(src_thumbs_folder, thumb_filename)
		
		if not os.path.exists(src_thumb_path):
			print_error("Thumbnail not found:", src_thumb_path)
			continue
		
		# Get the dimensions of the 1x thumbnail
		thumb_size = size_of_image_file(src_thumb_path)
		if thumb_size is None:
			print_error("Failed to get thumbnail size:", src_thumb_path)
			continue
		
		# Max size is the width of the 1x thumbnail
		max_size = thumb_size[1]
		
		# Create destination paths
		dest_pathx2 = os.path.join(dest_thumbs_folderx2, thumb_filename)
		dest_pathx3 = os.path.join(dest_thumbs_folderx3, thumb_filename)
		
		# Call fixThumb to save the new thumbnails
		try:
			fixThumb(image, dest_pathx2, dest_pathx3, max_size)
			save_count += 1
		except Exception as e:
			print_error("Error processing:", filename, str(e))
	
	return save_count

if __name__ == '__main__':
	console.print("Starting thumb fixer...")

	folder_count = 0
	total_save_count = 0

	# Scan each source folder
	for folder_name in src_folders:
		src_folder_path = os.path.join(src_path, folder_name)
		dest_folder_path = os.path.join(dest_path, folder_name)
		
		if not os.path.exists(src_folder_path):
			print_error("Source folder not found:", src_folder_path)
			continue
		
		console.print(f"\n[green]Scanning folder: [yellow]{folder_name}")

		if os.path.exists(dest_folder_path):
			shutil.rmtree(dest_folder_path)
		
		folder_paths = sorted(os.listdir(src_folder_path))
		max_folder_length = max((len(name) for name in folder_paths), default=0)

		with concurrent.futures.ThreadPoolExecutor() as executor:
			futures = {}
			for subfolder_name in os.listdir(src_folder_path):
				subfolder_path = os.path.join(src_folder_path, subfolder_name)
				
				if not os.path.isdir(subfolder_path):
					continue
				
				if len(subfolder_name) >= 10:
					folder_date = date_from_string(subfolder_name)
					
					if folder_date is not None and folder_date >= date_from_string(first_bad_date):
						dest_subfolder_path = os.path.join(dest_folder_path, subfolder_name)
						
						# Submit to executor instead of calling directly
						future = executor.submit(fixThumbs, subfolder_path, dest_subfolder_path)
						futures[future] = subfolder_name
			
			# Process results as they complete
			for future in concurrent.futures.as_completed(futures):
				subfolder_name = futures[future]
				try:
					count = future.result()
					total_save_count += count
					folder_count += 1
					console.print(f"  [green]✓ Completed: [yellow]{subfolder_name}" + " " * (max_folder_length - len(subfolder_name)) + f"[cyan]{count:4d} thumbs fixed")
				except Exception as e:
					print_error("Error in subfolder:", subfolder_name, str(e))

	console.print("\n[green]Thumb fixer complete!")
	console.print(f"[green]Processed [cyan]{folder_count} [green]folders, [green]fixed [cyan]{total_save_count} [green]thumbnails.")

