"""
	Try to locate the identify the yad window and locate the dismiss button Because FTY
"""

import subprocess


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


def get_pos():  # TODO still not tested enough!!
	window_id = get_yad_id()
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
