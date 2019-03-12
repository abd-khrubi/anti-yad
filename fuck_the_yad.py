"""
	Try to locate the identify the yad window and locate the dismiss button Because FTY
"""

import subprocess

import datetime
import pyscreeze
import os


def get_yad_id():
	res = subprocess.check_output(
		'xwininfo -root -tree|sed -e \'s/^ *//\'|grep -E \"^0x\"|awk \'{ print $1 }\'',
		shell=True)
	res = str(res)[2:-1]
	windows = sorted(res.split('\\n')[:-1])
	for window in windows:
		res = str(subprocess.check_output(f'xprop -id {window} WM_NAME', shell=True))[2:-1].split(' = ')
		# if len(res) > 1 and res[1][1:-3].lower() == "yad":
		if len(res) > 1 and res[1][1:-3] == 'Are you alive?':
			return window

		# if
	return None


def get_window_pos(window_id):  # TODO still not tested enough!!
	res = subprocess.check_output(f'xwininfo -id {window_id} -stats', shell=True)
	res = str(res)[2:-1].split('\\n')
	x, y = -1, -1
	for line in res:
		line = line.strip()
		if line.startswith('Absolute upper-left X'):
			x = int(line[len("Absolute upper-left X:  "):])
		if line.startswith("Absolute upper-left Y:"):
			y = int(line[len("Absolute upper-left Y:  "):])
	return x, y


def get_window_dim(window_id):
	res = subprocess.check_output(f'xwininfo -id {window_id} -stats', shell=True)
	res = str(res)[2:-1].split('\\n')
	w, h = -1, -1
	for line in res:
		line = line.strip()
		if line.startswith('Width'):
			w = int(line[len("Width: "):])
		if line.startswith("Height"):
			h = int(line[len("Height: "):])
	return w, h


def get_position(logger):
	try:
		x, y = pyscreeze.locateCenterOnScreen(rel_path('button.png'))
		return 0, x, y
	except (pyscreeze.ImageNotFoundException, FileNotFoundError) as e:

		img_name = rel_path(f"logs/err-button-{(datetime.datetime.now().strftime('%Y-%m%d_%H-%M-%S-%f'))}.png")
		logger.error(f"Could not find button image: {type(e).__name__}: {str(e)}\nAttaching screenshot: {img_name}")
		subprocess.call(['scrot', img_name])

	# could not locate the button by image
	# try to locate the window id and position
	window_id = get_yad_id()
	if window_id is not None:
		base_x, base_y = get_window_pos(window_id)
		width, height = get_window_dim(window_id)
		x = base_x + width - 20
		y = base_y + height - 15
		if x != -22 and y != -17:
			return 1, x, y

	# if all failed return None to try and click on a fixed position
	return None, None, None


def rel_path(filename):
	return os.path.join(os.path.dirname(__file__), filename)
