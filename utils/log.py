import sys

silent = False

def mute():
	global silent
	silent = True

def log(msg, type, errcode=None, sameline=False):
	global silent

	if silent:
		return
	if type == "error":
		print("[!] ", end="", flush=True)
	elif type == "warning":
		print("[-] ", end="", flush=True)
	elif type == "success":
		print("[+] ", end="", flush=True)

	if sameline:
		print (msg, end="\r", flush=True)
	else:
		print (msg)

	if errcode is not None:
		sys.exit(errcode)
