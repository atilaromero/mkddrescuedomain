#!/usr/bin/python
import sys
import os
import optparse
DEBUG=True

def listinodeschildren(infile,offset,inodedir):
    comando="fls '%s' -o %s %s -Fru"%(infile,offset,inodedir)
    if DEBUG:
        sys.stderr.write(comando+'\n')
    for line in os.popen(comando):
        if line:
            inode=line.split(' ')[1].split(':')[0].split('-')[0]
            yield inode

def listclusters(infile,offset,inode):
    comando="istat '%s' -o %s %s"%(infile,offset,inode)
    if DEBUG:
        sys.stderr.write(comando+'\n')
    printing=False
    for line in os.popen(comando):
        if printing:
            if line.startswith('Type'):
                printing=False
            else:
                line=line.rstrip()
                for x in line.split():
                    yield int(x.rstrip())
        else:
            if line.startswith('Type: $DATA') or line.rstrip()=='Sectors:':
                printing=True

def mkddrescue(clusters,infile,offset,clustersize=8,domain=False):
    if DEBUG:
        sys.stderr.write('Listando setores\n')
    sectors=[]
    #encontra o primeiro setor de cada cluster
    for cluster in clusters:
        sector=cluster*clustersize+offset
        sectors.append(sector)
    if DEBUG:
        sys.stderr.write('Ordenando setores\n')
    sectors.sort()

    if DEBUG:
        sys.stderr.write('Agrupando setores\n')
    lastsector=0
    basesector=[]
    #Agrupa os setores consecutivos
    for sector in sectors:
        if sector==lastsector:
            pass
        elif sector==lastsector+clustersize:
            basesector[-1][1]+=clustersize
        else:
            basesector.append([sector,clustersize])
        lastsector=sector
            
    if DEBUG:
        sys.stderr.write('Imprimindo resultado\n')
    pos=0
    for x in basesector:
        if domain:
            x0=x[0]*512
            x1=x[1]*512
            if pos==0:
                yield "0 ?"
            yield "%s %s ?"%(pos,x0-pos)
            yield "%s %s +"%(x0,x1)
            pos=x0+x1
        else:
            result="ddrescue infile outfile ddrescue.log -d -i %sb -s %sb -c %s "%(x[0],x[1],clustersize)
            yield result


def mkscriptdir(infile,offset,inodedir,clustersize=8,domain=False):
    clusters=[]
    for x in listinodeschildren(infile,offset,inodedir):
        for y in listclusters(infile,offset,x):
            clusters.append(y)
    for x in mkddrescue(clusters,infile,offset,clustersize,domain):
        print x

def mkscriptonefile(infile,offset,inode,clustersize=8,domain=False):
    clusters=[x for x in listclusters(infile,offset,inode)]
    for x in mkddrescue(clusters,infile,offset,clustersize,domain):
        print x

def main():
    p = optparse.OptionParser(usage="""usage: %prog [options] <infile> <sectoroffset> <-f|-d> <inode>
    This program creates a ddrescue domain file with 
    only the used areas of a damaged disk.
    That's usefull when you want to start by copping used areas of an unstable device.

Example for a NTFS partition:
    * /dev/sdx is an unstable device 
    * a NTFS partition starts at sector 63
    * MFT is at inode 0
    * root directory is at inode 5

    1-Recover the MFT: 
      # %prog /dev/sdx 63 -f 0 > mft.domain
      # ddrescue /dev/sdx image.dd ddrescue.log -m mft.domain
    2-Recover the non-deleted files:
      # %prog image.dd 63 -d 5 > allfiles.domain
      # ddrescue /dev/sdx image.dd ddrescue.log -m allfiles.domain
""")
    p.add_option('--clustersize', '-p', default="8",
                 help="8 para NTFS, 1 para FAT. fsstat fornece o clustersize em bytes: divida por 512")
    p.add_option('--file','-f',action='store_true',default=False,
                 help="inode belongs to a file")
    p.add_option('--dir','-d',action='store_true',default=False,
                 help="inode belongs to a directory")
    p.add_option('--script','-s',action='store_true',default=False,
                 help="print a ddrescue script, insted of a domain")
    options, arguments = p.parse_args()
    if len(arguments) < 3:
        p.error('missing argument')
    if len(arguments) > 3:
        p.error('too many arguments')
    if not (options.dir or options.file):
        p.error('inode is file or dir? use -f or -d to set')
    if (options.dir and options.file):
        p.error('-d OR -f, choose only one')
    infile,offset,inode=arguments
    offset=int(offset)
    clustersize=int(options.clustersize)
    domain=not options.script
    if options.file:
        mkscriptonefile(infile,offset,inode,clustersize,domain)
    else:
        mkscriptdir(infile,offset,inode,clustersize,domain)
    
if __name__ == '__main__':
    main()
