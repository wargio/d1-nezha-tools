# SPDX-FileCopyrightText: 2021 deroad <wargio@libero.it>
# SPDX-License-Identifier: LGPL-3.0-only

import argparse
import sys
import hashlib
from os import path

kernel_addr     = 0x40200000
ramdisk_addr    = 0x41200000
second_addr     = 0x41100000
tags_addr       = 0x40200100
page_size       = 0x00000800
image_name      = b'd1-nezha'
cmdline         = b''

def align(value, size):
	vsize  = len(value)
	mask   = size - 1
	module = vsize & mask
	if module == 0 and vsize > 0:
		return value
	padding = (b'\x00' * (size - module))
	return value + padding

def write_le32(number):
	p = number.to_bytes(4, byteorder='little')
	return p

def read_le32(bytes):
	p = bytes[3] << 24
	p |= bytes[2] << 16
	p |= bytes[1] << 8
	p |= bytes[0]
	return p

def build_boot_img(kernel, output):
	ramdisk = b''
	second = b''

	kernel_size = len(kernel)
	ramdisk_size = 0
	second_size = 0

	m = hashlib.sha1()
	m.update(kernel)
	m.update(write_le32(kernel_size))
	m.update(ramdisk)
	m.update(write_le32(ramdisk_size))
	m.update(second)
	m.update(write_le32(second_size))

	with open(output, mode='wb') as file:
		header = b'ANDROID!'
		header += write_le32(kernel_size) # kernel_size
		header += write_le32(kernel_addr)
		header += write_le32(0) # ramdisk_size
		header += write_le32(ramdisk_addr)
		header += write_le32(0) # second_size
		header += write_le32(second_addr)
		header += write_le32(tags_addr) # tags_addr
		header += write_le32(page_size) # page_size
		header += b'\x00\x00\x00\x00' # padding
		header += b'\x00\x00\x00\x00' # padding
		header += align(image_name, 16) # name
		header += align(cmdline, 0x200) # cmdline
		header += align(m.digest(), 32) # id (sha1 + padding)

		file.write(align(header, page_size))
		file.write(align(kernel, page_size))
		file.write(align(ramdisk, page_size))
		if second_size > 0:
			file.write(align(second, page_size))

def build_zimage(vmlinux):
	# the kernel needs to be aligned 4
	# skip first 2 bytes and replace with nop operation
	# 6f10f07f j 0x2804
	return b'\x01\x00'+ vmlinux[2:]

	# 6f200000 j 0x2000
	# the fingerprint is actually the beginning of the
	# .text segment which always starts with
	# 73104010  csrw sie, zero
	# 73104014  csrw sip, zero
	fingerprint_beg = b'\x73\x10\x40\x10\x73\x10\x40\x14'
	fingerprint_end = b'\x05\x46\xaf\xa6\xc6\x00'
	vmlinux_size = len(vmlinux)
	offset = 0
	try:
		offset = vmlinux.find(fingerprint_beg)
		while False and offset < vmlinux_size:
			# looking for li, amoadd.w within 0x30 bytes
			# 0546      li a2, 1
			# afa6c600  amoadd.w a3, a2, (a3)
			if vmlinux[offset+8:offset+0x38].find(fingerprint_end) > 0:
				break

			offset += 8 + vmlinux[offset + 8:].find(fingerprint_beg)
	except:
		print("cannot find fingerprint.. report this bug")
		sys.exit(1)
	print("found offset 0x{:08x}".format(offset))
	#print("bad offset 0x{:08x}".format(offset))
	## ignore first result.
	zimage_size  = (vmlinux_size - offset) + 0x40
	# the zImage starts with
	# 81a0     j 0x40
	# 00000000 invalid
	zimage = b'\x81\xa0\x00\x00\x00\x00'
	zimage += vmlinux[0x06:0x10]
	zimage += write_le32(zimage_size)
	zimage += vmlinux[0x14:0x3c]
	zimage += b'\x00\x00\x00\x00'
	zimage += vmlinux[offset:]
	return zimage

def dump(input_filename):
	print("boot img:", input_filename)
	with open(input_filename, mode='rb') as file:
		print("  magic:        '{}'".format((file.read(8) + b'\x00').decode("ascii", errors="ignore")))
		print("  kernel_size:  0x{:08x}".format(read_le32(file.read(4))))
		print("  kernel_addr:  0x{:08x}".format(read_le32(file.read(4))))
		print("  ramdisk_size: 0x{:08x}".format(read_le32(file.read(4))))
		print("  ramdisk_addr: 0x{:08x}".format(read_le32(file.read(4))))
		print("  second_size:  0x{:08x}".format(read_le32(file.read(4))))
		print("  second_addr:  0x{:08x}".format(read_le32(file.read(4))))
		print("  tags_addr:    0x{:08x}".format(read_le32(file.read(4))))
		print("  page_size:    0x{:08x}".format(read_le32(file.read(4))))
		file.read(8)
		print("  image_name:   '{}'".format((file.read(16) + b'\x00').decode("ascii", errors="ignore")))
		print("  cmdline:      '{}'".format((file.read(0x200) + b'\x00').decode("ascii", errors="ignore")))
		print("  id:           {}".format(file.read(32).hex()))
		sys.exit(0)

def extract(input_filename, output_filename):
	zimage = None
	with open(input_filename, mode='rb') as file:
		zimage = file.read()

	zimage_end = 0x800 + read_le32(zimage[8:12])
	zimage = zimage[0x800 : zimage_end]

	with open(output_filename, mode='wb') as file:
		file.write(zimage)
	sys.exit(0)

def build(input_filename, output_filename, is_vmlinux):
	zimage = None
	with open(input_filename, mode='rb') as file:
		zimage = file.read()

	if is_vmlinux:
		zimage = build_zimage(zimage)

	build_boot_img(zimage, output_filename)
	dump(output_filename)

def main(args):
	if len(sys.argv) == 1:
		parser.print_help(sys.stderr)
		sys.exit(1)

	if args.dump:
		dump(args.input)
		
	if args.extract:
		extract(args.input, args.output)
		
	else:
		global cmdline
		cmdline = args.cmdline.encode('ascii')
		build(args.input, args.output, args.vmlinux)


if __name__ == '__main__':
	description='boot.img utility for Allwinner D1 Nezha'
	epilog = '''
example bulding boot.img from zImage:
	python d1-nezha-bootimg.py -i zImage -o my_boot.img

example bulding boot.img from vmlinux:
	python d1-nezha-bootimg.py -l -i vmlinux -o my_boot.img

example dumping boot.img info:
	python d1-nezha-bootimg.py -d -i boot.img

example extracting zImage from a boot.img:
	python d1-nezha-bootimg.py -x -i boot.img -o extracted_zImage'''
	parser = argparse.ArgumentParser(usage='%(prog)s [options]', description=description, epilog=epilog, formatter_class=argparse.RawDescriptionHelpFormatter)
	parser.add_argument('-d', '--dump', default=False, help='dumps the boot.img', action='store_true')
	parser.add_argument('-l', '--vmlinux', default=False, help='converts a vmlinux image to zImage before creating the boot.img', action='store_true')
	parser.add_argument('-x', '--extract', default=False, help='extracts the zImage from a boot.img', action='store_true')
	parser.add_argument('-i', '--input', help='input filename')
	parser.add_argument('-o', '--output', help='output filename')
	parser.add_argument('-c', '--cmdline', default='', help='kernel command line')
	args = parser.parse_args()
	main(args)