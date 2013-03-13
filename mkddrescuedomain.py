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

def mkddrescue(clusters,infile,outfile,offset,clustersize=8,domain=False):
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
            result="ddrescue '%s' '%s' ddrescue.log -d -i %sb -s %sb -c %s "%(infile,outfile,x[0],x[1],clustersize)
            yield result


def mkscriptdir(infile,outfile,offset,inodedir,clustersize=8,domain=False,altinfile=''):
    clusters=[]
    for x in listinodeschildren(infile,offset,inodedir):
        for y in listclusters(infile,offset,x):
            clusters.append(y)
    if not altinfile:
        altinfile=infile
    for x in mkddrescue(clusters,altinfile,outfile,offset,clustersize,domain):
        print x

def mkscriptonefile(infile,outfile,offset,inode,clustersize=8,domain=False,altinfile=''):
    if not altinfile:
        altinfile=infile
    clusters=[x for x in listclusters(infile,offset,inode)]
    for x in mkddrescue(clusters,altinfile,outfile,offset,clustersize,domain):
        print x

def main():
    p = optparse.OptionParser(usage="""usage: %prog [options] <infile> <outfile> <sectoroffset> <inode>
    This program creates a script with ddrescue commands to recover 
         used areas of a damaged disk.
    Or it can create a ddrescue domain file with those areas.""")
    p.add_option('--clustersize', '-p', default="8",
                 help="8 para NTFS, 1 para FAT. fsstat fornece o clustersize em bytes: divida por 512")
    p.add_option('--altinfile', '-x', default="",
                 help="input file to be printed, if diferent from infile")
    p.add_option('--file','-f',action='store_true',default=False,
                 help="inode pertence a um arquivo")
    p.add_option('--dir','-d',action='store_true',default=True,
                 help="inode pertence a um diretorio")
    p.add_option('--domain','-m',action='store_true',default=False,
                 help="print a domain ddrescue file, instead of a script")
    options, arguments = p.parse_args()
    if len(arguments) < 4:
        p.error('missing argument')
    if len(arguments) > 4:
        p.error('too many arguments')
    infile,outfile,offset,inode=arguments
    offset=int(offset)
    clustersize=int(options.clustersize)
    if options.file:
        mkscriptonefile(infile,outfile,offset,inode,clustersize,options.domain,options.altinfile)
    else:
        mkscriptdir(infile,outfile,offset,inode,clustersize,options.domain,options.altinfile)
    
if __name__ == '__main__':
    main()
