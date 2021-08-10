# Allwinner D1 Nezha Tools

I am still writings these tools but you can build your own boot.img via this script and the only requirement is `python3` with `hashlib`

```
usage: d1-nezha-bootimg.py [options]

boot.img utility for Allwinner D1 Nezha

optional arguments:
  -h, --help            show this help message and exit
  -d, --dump            dumps the boot.img
  -l, --vmlinux         converts a vmlinux image to zImage before creating the boot.img
  -x, --extract         extracts the zImage from a boot.img
  -i INPUT, --input INPUT
                        input filename
  -o OUTPUT, --output OUTPUT
                        output filename

example bulding boot.img from zImage:
        python d1-nezha-bootimg.py -i zImage -o my_boot.img

example bulding boot.img from vmlinux:
        python d1-nezha-bootimg.py -l -i vmlinux -o my_boot.img

example dumping boot.img info:
        python d1-nezha-bootimg.py -d -i boot.img

example extracting zImage from a boot.img:
        python d1-nezha-bootimg.py -x -i boot.img -o extracted_zImage
```

## Extra

So the boot.img is an android system image which contains just the kernel image (it can be rebuilt also via mkbootimg if you have the AOSP tools)

- `kernel_addr` is set to `0x40200000` for the D1
- `ramdisk_addr` is set to `0x41200000` for the D1
- `second_addr` is set to `0x41100000` for the D1
- `tags_addr` is set to `0x40200100` for the D1
- `page_size` is set to `0x00000800` for the D1


So the original zImage does this

```
        ┌─< 0x00000000      81a0           j     0x40
        │   0x00000002  0000 0000 0100 0000 2000 0000 0000 6c41  ........ .....lA
        │   0x00000012  9200 0000 0000 0000 0000 0000 0000 0200  ................
        │   0x00000022  0000 0000 0000 0000 0000 0000 0000 5249  ..............RI
        │   0x00000032  5343 5600 0000 5253 4305 0000 0000       SCV...RSC.....
        └─> 0x00000040      73104010       csrw  sie, zero
            0x00000044      73104014       csrw  sip, zero
            0x00000048      97218e00       auipc gp, 0x8e2
            0x0000004c      9381c1bb       addi  gp, gp, -1092
            0x00000050      b7628001       lui   t0, 0x1806
            0x00000054      73b00210       csrc  sstatus, t0
            0x00000058      97968e00       auipc a3, 0x8e9
            0x0000005c      93868685       addi  a3, a3, -1960
            0x00000060      0546           li    a2, 1
            0x00000062      afa6c600       amoadd.w a3, a2, (a3)
        ┌─< 0x00000066      e1e6           bnez  a3, 0x12e
        │   0x00000068      97268e00       auipc a3, 0x8e2
        │   0x0000006c      938686f9       addi  a3, a3, -104
        │   0x00000070      17279200       auipc a4, 0x922
        │   0x00000074      1307c722       addi  a4, a4, 556
       ┌──< 0x00000078      63d7e600       ble   a4, a3, 0x86
      ┌───> 0x0000007c      23b00600       sd    zero, 0(a3)
      ╎││   0x00000080      a106           addi  a3, a3, 8
      └───< 0x00000082      e3cde6fe       blt   a3, a4, 0x7c
       └──> 0x00000086      2a84           mv    s0, a0
        │   0x00000088      ae84           mv    s1, a1
```

The vmlinux image has a header (MZ header) but also has a jump after it like the zImage.

```
            0x00000000  4d5a                                     MZ
        ┌─< 0x00000002      6f10f07f       j     0x2000
        │   0x00000006  0100 0000 2000 0000 0000 00d0 1b01 0000  .... ...........
        │   0x00000016  0000 0000 0000 0000 0000 0200 0000 0000  ................
        │   0x00000026  0000 0000 0000 0000 0000 5249 5343 5600  ..........RISCV.
        │   0x00000036  0000 5253 4305 4000 0000 5045 0000 6450  ..RSC.@...PE..dP
        │   0x00000046  0200 0000 0000 0000 0000 0000 0000 a000  ................
        │   0x00000056  0602 0b02 0214 0040 8b00 0080 9000 0000  .......@........
        │   ...... skipping bytes ......
        │   0x00001ff0  0000 0000 0000 0000 0000 0000 0000 0000  ................
        └─> 0x00002000      73104010       csrw  sie, zero
            0x00002004      73104014       csrw  sip, zero
            0x00002008      97111401       auipc gp, 0x1141
            0x0000200c      9381010f       addi  gp, gp, 240
            0x00002010      9962           lui   t0, 0x6
            0x00002012      73b00210       csrc  sstatus, t0
            0x00002016      a142           li    t0, 8
        ┌─< 0x00002018      63465500       blt   a0, t0, 0x2024
        │   0x0000201c      17f3ffff       auipc t1, 0xfffff
        │   0x00002020      6700630b       jr    182(t1)
        └─> 0x00002024      97161401       auipc a3, 0x1141
            0x00002028      9386c691       addi  a3, a3, -1764
            0x0000202c      0546           li    a2, 1
            0x0000202e      afa6c600       amoadd.w a3, a2, (a3)
        ┌─< 0x00002032      b5ee           bnez  a3, 0x20ae
        │   0x00002034      97361401       auipc a3, 0x1143
        │   0x00002038      9386c6fc       addi  a3, a3, -52
        │   0x0000203c      17a71b01       auipc a4, 0x11ba
        │   0x00002040      13079767       addi  a4, a4, 1657
       ┌──< 0x00002044      63d7e600       ble   a4, a3, 0x2052
      ┌───> 0x00002048      23b00600       sd    zero, 0(a3)
      ╎││   0x0000204c      a106           addi  a3, a3, 8
      └───< 0x0000204e      e3cde6fe       blt   a3, a4, 0x2048
       └──> 0x00002052      2a84           mv    s0, a0
        │   0x00002054      ae84           mv    s1, a1
```

So potentially we can patch the vmlinux image to do the same, by patching the first 2 bytes (MZ header) with a nop (0x01 0x00)

```
            0x00000000      0100           nop
        ┌─< 0x00000002      6f10f07f       j     0x2000
        │   0x00000006  0100 0000 2000 0000 0000 00d0 1b01 0000  .... ...........
        │   0x00000016  0000 0000 0000 0000 0000 0200 0000 0000  ................
        │   0x00000026  0000 0000 0000 0000 0000 5249 5343 5600  ..........RISCV.
        │   0x00000036  0000 5253 4305 4000 0000 5045 0000 6450  ..RSC.@...PE..dP
        │   0x00000046  0200 0000 0000 0000 0000 0000 0000 a000  ................
        │   0x00000056  0602 0b02 0214 0040 8b00 0080 9000 0000  .......@........
        │   0x00000066  0000 0a26 0300 0010 0000 0000 0000 0000  ...&............
        │   0x00000076  0000 0010 0000 0002 0000 0000 0000 0100  ..............
        │   ...... skipping bytes ......
        │   0x00001ff0  0000 0000 0000 0000 0000 0000 0000 0000  ................
        └─> 0x00002000      73104010       csrw  sie, zero
            0x00002004      73104014       csrw  sip, zero
            0x00002008      97111401       auipc gp, 0x1141
            0x0000200c      9381010f       addi  gp, gp, 240
            0x00002010      9962           lui   t0, 0x6
            0x00002012      73b00210       csrc  sstatus, t0
            0x00002016      a142           li    t0, 8
        ┌─< 0x00002018      63465500       blt   a0, t0, 0x2024
        │   0x0000201c      17f3ffff       auipc t1, 0xfffff
        │   0x00002020      6700630b       jr    182(t1)
        └─> 0x00002024      97161401       auipc a3, 0x1141
            0x00002028      9386c691       addi  a3, a3, -1764
            0x0000202c      0546           li    a2, 1
            0x0000202e      afa6c600       amoadd.w a3, a2, (a3)
        ┌─< 0x00002032      b5ee           bnez  a3, 0x20ae
        │   0x00002034      97361401       auipc a3, 0x1143
        │   0x00002038      9386c6fc       addi  a3, a3, -52
        │   0x0000203c      17a71b01       auipc a4, 0x11ba
        │   0x00002040      13079767       addi  a4, a4, 1657
       ┌──< 0x00002044      63d7e600       ble   a4, a3, 0x2052
      ┌───> 0x00002048      23b00600       sd    zero, 0(a3)
      ╎││   0x0000204c      a106           addi  a3, a3, 8
      └───< 0x0000204e      e3cde6fe       blt   a3, a4, 0x2048
       └──> 0x00002052      2a84           mv    s0, a0
        │   0x00002054      ae84           mv    s1, a1
```