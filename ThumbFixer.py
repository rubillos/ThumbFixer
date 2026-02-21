#!python

# pip install --upgrade pip
# pip install cryptography
# pip install rich
# pip install Pillow

import os, shutil
from datetime import datetime
from PIL import Image
import concurrent.futures
from rich.console import Console
from rich.theme import Theme

first_bad_date = "2021-12-26"

src_path = "/Users/randy/Sites/PortlandAve"
dest_path = "/Users/randy/Sites/PortlandAve-ThumbFix"

src_folders = ["Local", "travel"]
direct_folders = ["fredandkatie/Gallery"]

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

	dest_console.print("".join(parts))

def createFolder(path):
	if "." in path:
		path = os.path.dirname(path)
	try:
		os.makedirs(path, exist_ok=True)
		return True
	except OSError as e:
		print_error(f"Error creating folder '{path}': {e}")
		return False
	
def size_of_image_file(path):
	try:
		return Image.open(path).size
	except Exception as e:
		return None

def scaled_size(input_size, thumb_width):
	width, height = input_size
	return (thumb_width, round(thumb_width / width * height))
	
def save_scaled(image, width, path, sampling, profile):
	new_size = scaled_size(image.size, width)
	scaled_image = image.resize(new_size, resample=sampling)
	createFolder(path)
	with open(path, "wb") as file:
		scaled_image.save(file, "JPEG", quality="high", icc_profile=profile)

def date_from_string(date_string):
	date_string = date_string[:10]
	if len(date_string)>0:
		try:
			return datetime.strptime(date_string, "%Y-%m-%d")
		except Exception as e:
			return None

def fixThumb(src_path, dest_pathx2, dest_pathx3, thumb_width):
	try:
		image = Image.open(src_path)
		image.load()
		profile = image.info.get("icc_profile", None)

		save_scaled(image, thumb_width*2, dest_pathx2, Image.LANCZOS, profile)
		save_scaled(image, thumb_width*3, dest_pathx3, Image.LANCZOS, profile)
	except Exception as e:
		print_error("Failed to load image:", src_path, str(e))

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
		thumb_width = thumb_size[0]
		
		# Create destination paths
		dest_pathx2 = os.path.join(dest_thumbs_folderx2, thumb_filename)
		dest_pathx3 = os.path.join(dest_thumbs_folderx3, thumb_filename)
		
		# Call fixThumb to save the new thumbnails
		try:
			fixThumb(src_picture_path, dest_pathx2, dest_pathx3, thumb_width)
			save_count += 1
		except Exception as e:
			print_error("Error processing:", filename, str(e))
	
	return save_count

if __name__ == '__main__':
	console.print("Starting thumb fixer...")

	folder_count = 0
	total_save_count = 0

	folders_to_process = []

	for direct_folder in direct_folders:
		src_folder_path = os.path.join(src_path, direct_folder)
		dest_folder_path = os.path.join(dest_path, direct_folder)
		
		if not os.path.exists(src_folder_path):
			print_error("Source folder not found:", src_folder_path)
			continue
		
		console.print(f"[green]Scanning folder: [yellow]{direct_folder}")

		if os.path.exists(dest_folder_path):
			shutil.rmtree(dest_folder_path)
		
		folders_to_process.append((src_folder_path, dest_folder_path, direct_folder))

	# Scan each source folder
	for folder_name in src_folders:
		src_folder_path = os.path.join(src_path, folder_name)
		dest_folder_path = os.path.join(dest_path, folder_name)
		
		if not os.path.exists(src_folder_path):
			print_error("Source folder not found:", src_folder_path)
			continue
		
		console.print(f"[green]Scanning folder: [yellow]{folder_name}")

		if os.path.exists(dest_folder_path):
			shutil.rmtree(dest_folder_path)
		
		for subfolder_name in os.listdir(src_folder_path):
			if len(subfolder_name) >= 10:
				folder_date = date_from_string(subfolder_name)
				
				if folder_date is not None and folder_date >= date_from_string(first_bad_date):
					subfolder_path = os.path.join(src_folder_path, subfolder_name)
					dest_subfolder_path = os.path.join(dest_folder_path, subfolder_name)
					folders_to_process.append((subfolder_path, dest_subfolder_path, subfolder_name))

	console.print()

	folders_to_process.sort(key=lambda x: x[2])
	max_folder_length = max((len(subfolder_name) for _, _, subfolder_name in folders_to_process), default=0)

	with concurrent.futures.ThreadPoolExecutor() as executor:
		futures = {}
		for subfolder_path, dest_subfolder_path, subfolder_name in folders_to_process:
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
				console.print(f"[green]✓ Completed: [yellow]{subfolder_name}" + " " * (max_folder_length - len(subfolder_name)) + f"[cyan]{count:4d} thumbs fixed")
			except Exception as e:
				print_error("Error in subfolder:", subfolder_name, str(e))

	console.print("\n[green]Thumb fixer complete!")
	console.print(f"[green]Processed [cyan]{folder_count} [green]folders, [green]fixed [cyan]{total_save_count} [green]thumbnails.")

