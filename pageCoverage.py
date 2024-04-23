import argparse
from multiprocessing import Pool, cpu_count
import fitz
import numpy

def pdfPageProc(args):
    with fitz.open(args[0])as doc:
        page=doc[args[1]]
        pix=page.get_pixmap(dpi=args[2])
    return(1-numpy.average(numpy.frombuffer(pix.samples_mv,dtype=numpy.uint8))/255)*pix.height*pix.width/(8.268*11.693*args[2]**2)

class RGB(numpy.ndarray):
    def __new__(cls,value):
        return numpy.array([value],dtype=numpy.uint32).view(numpy.uint8,cls)[:3].astype(numpy.float32)
    @classmethod
    def fromString(cls,str):
        return cls(int(str,base=16))
    def __format__(self,format_spec):
        srg={
            'F':38,
            'B':48,
            '':48,
        }[format_spec]
        return f'\033[{srg};2;{self[2]:.0f};{self[1]:.0f};{self[0]:.0f}m'

if __name__=='__main__':
    if __import__('platform').system()=='Windows':(lambda k:k.SetConsoleMode(k.GetStdHandle(-11),7))(__import__('ctypes').windll.kernel32) # -11:STD_OUTPUT_HANDLE, 7:ENABLE_VIRTUAL_TERMINAL_PROCESSING
    parser=argparse.ArgumentParser('PrinterPageCoverage',description='Know how much ink will be used',fromfile_prefix_chars='!')
    parser.add_argument('files',nargs='*')
    parser.add_argument('-j','--jobs',default=cpu_count()>>1,help='Multiprocessing jobs, default to cpu_count()>>1')
    parser.add_argument('-i','--ink',default=1,type=int,help='Number of ink')
    parser.add_argument('-n','--ink-name',nargs='+',help='Name of each ink')
    parser.add_argument('-c','--ink-color',nargs='+',type=RGB.fromString,help='The color displayed on screen of each ink')
    parser.add_argument('-w','--ink-worth',nargs='+',type=float,help='The cost for one 5%% coverage page of each ink')
    parser.add_argument('-m','--max-display',default=.25,type=float,help='Page with coverage above max-display will be shown in the max brightness')
    parser.add_argument('-d','--dpi',default=300,type=int,help='DPI of internal image, larger DPI will give higher precision but slower')
    parser.add_argument('--CMYK',action='store_true')
    arg=parser.parse_args()
    if arg.CMYK:
        arg.ink=4
        arg.ink_name=list('CMYK')
        arg.ink_color=[RGB(0x00FFFF),RGB(0xFF00FF),RGB(0xFFFF00),RGB(0xFFFFFF)]
    if arg.ink_name is None:
        arg.ink_name=['Mono']if arg.ink==1 else[f'Color{i}'for i in range(arg.ink)]
    if arg.ink_color is None:
        arg.ink_color=[RGB(0xFFFFFF)]*arg.ink
    if arg.ink_worth is None:
        arg.ink_worth=[.0]*arg.ink
    assert arg.ink>=1 and arg.ink==len(arg.ink_name)==len(arg.ink_color)==len(arg.ink_worth)

    ink=[.0]*arg.ink
    paper=0
    for file in arg.files:
        print(file)
        if file.endswith('.pdf'):
            with fitz.open(file)as doc:
                pages=len(doc)
            paper+=pages
            with Pool(arg.jobs)as pool:
                for file,coverage in enumerate(pool.imap(pdfPageProc,((file,i,arg.dpi)for i in range(pages)))):
                    ink[file%arg.ink]+=coverage
                    print(f'{arg.ink_color[file%arg.ink]*min(coverage,arg.max_display)/arg.max_display} ',end='',flush=True)
        elif False:...
        print('\033[0m-')
    for color,name,coverage,worth in zip(arg.ink_color,arg.ink_name,ink,arg.ink_worth):
        print(''.join(f'{color*i/16} 'for i in range(1,17))+f'\033[0m {color*min(coverage,arg.max_display)/arg.max_display}{(128+color*min(coverage/arg.max_display,1))%256:F}{name:^{max(len(i)for i in arg.ink_name)+2}}\033[0m{coverage*arg.ink/paper*100:9.2f}%{coverage*20:10.2f}{coverage*20*worth:12.2f}')
    print(f'{sum(amount*20*worth for amount,worth in zip(ink,arg.ink_worth)):.2f}')
    input('Press Enter to continue...')
