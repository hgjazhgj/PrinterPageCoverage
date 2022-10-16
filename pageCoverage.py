import sys
import numpy as np
import fitz
from multiprocessing import Pool,cpu_count

def pdfPageProc(args):
    with fitz.open(args[0])as doc:
        page=doc[args[1]]
        pix=page.get_pixmap(dpi=100)
    height=pix.height/100*25.4
    width=pix.width/100*25.4
    return (1-np.average(np.frombuffer(pix.samples_mv,dtype=np.uint8))/255)*(
        1 if height<=297 and width<=210 else min(297/height,210/width)**2
    )*height*width/(297*210)

if __name__=='__main__':
    if __import__('platform').system()=='Windows':(lambda k:k.SetConsoleMode(k.GetStdHandle(-11),7))(__import__('ctypes').windll.kernel32) # -11:STD_OUTPUT_HANDLE, 7:ENABLE_VIRTUAL_TERMINAL_PROCESSING
    ink=0
    paper=0
    print(''.join('\033[48;2;{0};{0};{0}m '.format(i<<4|i)for i in range(16)),end='\033[0m\n')
    for i in sys.argv[1:]:
        print(i)
        if i.endswith('.pdf'):
            with fitz.open(i)as doc:
                pages=len(doc)
            paper+=pages
            with Pool(cpu_count()>>1)as pool:
                for coverage in pool.imap(pdfPageProc,((i,j)for j in range(pages))):
                    ink+=coverage
                    print('\033[48;2;{0};{0};{0}m '.format(round(coverage*255)),end='',flush=True)
        elif False:...
        print('\033[0m-')
    print(f'{ink/paper*100:8.2f}% {ink/.05:8.2f} {ink*1636/250/.05:10.2f}')
    input('Press Enter to continue...')
