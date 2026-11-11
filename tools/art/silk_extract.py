import numpy as np, cv2, json
from PIL import Image
D='/tmp/claude-0/-home-claude/c6160ff2-902c-5093-af99-9dd72239ab62/scratchpad/'
im=np.asarray(Image.open(D+'fogz_fixed_design.png').convert('RGB')).astype(np.float32)
H,W,_=im.shape; L=im.mean(2); S=im.max(2)-im.min(2)
cream=((L>150)&(S<95))
lim=np.zeros_like(cream); lim[40:1352,134:1716]=True; cream&=lim
yy,xx=np.mgrid[0:H,0:W]
def nocirc(cx,cy,r): global cream; cream&=~(np.hypot(xx-cx,yy-cy)<r)
nocirc(1621,212,104)                        # preset knob
for cx,cy,r in [(400,1170,105),(1460,1170,105),(1000.5,237.5,44),(1004.5,529.5,44),(1002,374,64),(1002,674,64),(697.5,1136,34),(1157.5,1135,34)]: nocirc(cx,cy,r)
for y in [364.5+58*i for i in range(8)]: nocirc(1619.5,y,25)
cream[1220:1280,760:1080]=False             # old logo
for sx in [261,409,557,704,853,1146,1290,1437]: cream[238:714,sx-21:sx+22]=False   # slot rims (ticks are redrawn)
np.save('cream.npy',cream)
n,lab,st,cen=cv2.connectedComponentsWithStats(cream.astype(np.uint8),connectivity=8)
comps=[]
for k in range(1,n):
    x,y,w,h,a=map(int,st[k])
    if a<6: continue
    if (y<720 and w<8 and h>12 and any(abs(x+w/2-sx)<22 for sx in [261,409,557,704,853,1146,1290,1437])): continue   # slot rims
    if w<8 and h<100: kind=None
    kind='line' if (w>200 or (h>100 and w>=4)) else ('title' if 300<=x and x+w<=1560 and 840<=y and y+h<=1070 else ('tick' if h<=7 and w>=8 else 'glyph'))
    comps.append(dict(k=k,x=x,y=y,w=w,h=h,a=a,kind=kind))
np.save('lab.npy',lab)
json.dump(comps,open('comps.json','w'))
from collections import Counter; print(Counter(c['kind'] for c in comps))
# cluster glyphs into words (gap-based, both orientations)
g=[c for c in comps if c['kind']=='glyph']
m=np.zeros((H,W),np.uint8)
for c in g: m[lab==c['k']]=255
m2=cv2.dilate(m,np.ones((9,9),np.uint8))
n2,l2,s2,c2=cv2.connectedComponentsWithStats(m2)
for k in range(1,n2):
    x,y,w,h,a=s2[k]; print('word',x+4,y+4,w-8,h-8, 'vertical' if h>w*1.5 else '')
