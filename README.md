# mkddrescuedomain

```
Usage: mkddrescuedomain.py [options] <infile> <sectoroffset> <-f|-d> <inode>
    This program creates a ddrescue domain file with 
    only the used areas of a damaged disk.
    That's usefull when you want to start by copping used areas of an unstable device.

Example for a NTFS partition:
    * /dev/sdx is an unstable device 
    * a NTFS partition starts at sector 63
    * MFT is at inode 0
    * root directory is at inode 5

    1-Recover the MFT: 
      # mkddrescuedomain.py /dev/sdx 63 -f 0 > mft.domain
      # ddrescue /dev/sdx image.dd ddrescue.log -m mft.domain
    2-Recover the non-deleted files:
      # mkddrescuedomain.py image.dd 63 -d 5 > allfiles.domain
      # ddrescue /dev/sdx image.dd ddrescue.log -m allfiles.domain
```
