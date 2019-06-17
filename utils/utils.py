import os
import subprocess
import pyscreeze
import time


def rel_path(filename):
	"""
	Gets the relative path of the given file
	:param filename: The file to get its relative path
	:return: the relative path of the given file
	"""
	return os.path.join(os.path.dirname(__file__), filename)


def execute_shell_cmd(cmd: str):
	"""
	execute shell command and returns a list of the output lines
	"""
	res = subprocess.check_output(cmd, shell=True)
	res = str(res)[2:-1]
	return res.split('\\n')[:-1]


def get_yad_id():
	"""
	Gets the ID of the window which has title 'Are you alive?'
	"""
	windows = execute_shell_cmd('xwininfo -root -tree|sed -e \'s/^ *//\'|grep -E \"^0x\"|awk \'{ print $1 }\'')
	windows = sorted(windows)
	for window in windows:
		window_name = execute_shell_cmd(f'xprop -id {window} WM_NAME')[0].split(' = ')
		if len(window_name) > 1 and window_name[1][1:-1] == 'Are you alive?':
			return window
	return None


def get_window_rect(window_id):
	attrs = execute_shell_cmd(f'xwininfo -id {window_id} -stats')
	x, y, w, h = -1, -1, -1, -1
	for line in attrs:
		line = line.strip()
		if line.startswith('Absolute upper-left X:'):
			x = int(line[len('Absolute upper-left X:'):].strip())
		if line.startswith('Absolute upper-left Y:'):
			y = int(line[len('Absolute upper-left Y:'):].strip())
		if line.startswith('Width'):
			w = int(line[len('Width:'):].strip())
		if line.startswith("Height"):
			h = int(line[len("Height:"):].strip())
	return x, y, w, h


def find_button_pos(logger):
	#try: # TODO throws NoneType Exception
	#	if pyscreeze.useOpenCV:
	#		x, y = pyscreeze.locateCenterOnScreen(rel_path('../assets/button.png'), confidence=0.8)
	#	else:
	#		x, y = pyscreeze.locateCenterOnScreen(rel_path('../assets/button.png'))
	#		logger.warning('Install OpenCV for better results.')
	#	return 0, x, y
	#except pyscreeze.ImageNotFoundException as e:
	#	logger.warning(f'Could not locate button image: {type(2).__name__}: {str(e)}')

	"""
	Get button position from window's position
	"""

	window_id = get_yad_id()
	if window_id is not None:
		base_x, base_y, width, height = get_window_rect(window_id)
		x = base_x + width - 20
		y = base_y + height - 15
		if x > 0 and y > 0:
			return 1, x, y
	logger.error('Fatal: Could not find button\'s position.')
	return None, None, None


def is_screen_locked(logger):
	try:
		res = execute_shell_cmd('mate-screensaver-command -q')[0]
		return res.endswith('is active')
	except subprocess.CalledProcessError:
		logger.error('No response from mate-screensaver')
	return None


def get_current_layout():
	return int(execute_shell_cmd(rel_path('./xkblayout-state print "%c"'))[0])


def get_en_layout():
	layouts = execute_shell_cmd(rel_path('./xkblayout-state print "%E"'))
	en_idx = -1
	for layout in layouts:
		layout = layout.split(',')
		if len(layout) == 2 and layout[0] == 'en':
			en_idx = int(layout[1])
	return en_idx


def change_keyboard_layout(layout_idx=None):
	if layout_idx is None:
		layout_idx = get_en_layout()
	execute_shell_cmd(rel_path(f'./xkblayout-state set {layout_idx}'))


def format_time(seconds=None):
	if seconds:
		t = time.gmtime(seconds)
		return time.strftime('%H:%M:%S', t)
	else:
		return time.strftime("%I:%M:%S %p")
