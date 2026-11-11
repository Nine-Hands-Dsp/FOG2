import numpy as np, cv2, json
from PIL import Image, ImageDraw, ImageFont
s=1800/1377.0; SS=2                      # supersampling
W,H=2350*SS,1800*SS
def T(x,y): return (((x-91)*s+85)*SS, ((y-2)*s)*SS)
cream=np.load('cream.npy'); lab=np.load('lab.npy'); comps=json.load(open('comps.json'))
canvas=Image.new('L',(W,H),0); d=ImageDraw.Draw(canvas)
# ---------- 1. traced shapes: panel outlines + FOGZ title + subtitle ----------
def trace(kinds,blur=1.6,k=5):
    m=np.zeros(cream.shape,np.uint8)
    for c in comps:
        if c['kind'] in kinds: m[lab==c['k']]=255
    up=4
    big=cv2.resize(m.astype(np.float32),None,fx=up,fy=up,interpolation=cv2.INTER_CUBIC)
    big=cv2.GaussianBlur(big,(0,0),blur)
    bm=(big>127).astype(np.uint8)
    cs,hier=cv2.findContours(bm,cv2.RETR_CCOMP,cv2.CHAIN_APPROX_NONE)
    out=[]
    for i,c in enumerate(cs):
        if len(c)<12: continue
        p=c[:,0,:].astype(np.float32)
        # smooth along the contour (circular), keeps corners reasonably sharp at this scale
        pad=np.concatenate([p[-k:],p,p[:k]]); ker=np.ones(2*k+1)/(2*k+1)
        sm=np.stack([np.convolve(pad[:,0],ker,'valid'),np.convolve(pad[:,1],ker,'valid')],1)
        out.append((sm/up, hier[0][i][3]>=0))
    return out
paths={'outlines':trace(['line']),'title':trace(['title'],blur=3.2,k=9)}
for name,cs in paths.items():
    layer=Image.new('L',(W,H),0); dl=ImageDraw.Draw(layer)
    for pts,is_hole in sorted(cs,key=lambda t:t[1]):       # outers first, then holes
        poly=[T(x,y) for x,y in pts]
        dl.polygon(poly,fill=0 if is_hole else 255)
    canvas=Image.fromarray(np.maximum(np.asarray(canvas),np.asarray(layer)))
d=ImageDraw.Draw(canvas)
# preset column right edge: ragged end near the top replaced by a clean straight line running under the knob
(a0,b0),(a1,b1)=T(1683,296),T(1712,388); d.rectangle((a0,b0,a1,b1),fill=0)
(a0,b0),(a1,b1)=T(1691.6,236),T(1702.4,392); d.rectangle((a0,b0,a1,b1),fill=255)   # runs up under the knob
# EFFECTS box: top edge and right edge continued under the preset knob (the knob hides their corner)
import numpy as _np
xs=_np.arange(1380,1520,4); ys=_np.array([176,176,176.5,176.5,177,177.5,178,178.5,179,179.5,180,180.5,180.5,181.5,182,182.5,183,183.5,184.5,185,186,186.5,187.5,188,189.5,190,191,192,193,193.5,195,196,197,198.5,199.5])
cf=_np.polyfit(xs,ys,2)
for x in _np.arange(1500,1566,0.5):
    yc=_np.polyval(cf,x); (a0,b0),(a1,b1)=T(x-0.6,yc-5),T(x+0.6,yc+5); d.rectangle((a0,b0,a1,b1),fill=255)
yc=_np.polyval(cf,1532); (a0,b0),(a1,b1)=T(1527,yc-4),T(1537.5,320); d.rectangle((a0,b0,a1,b1),fill=255)
# ---------- 2. text (Poppins Bold) ----------
FB='/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf'
labels=[  # text, cx, cy (design), cap height (design px), rotation (deg, 90 = reads bottom->top), max length
 ('DRY OUTPUT',221.5,471,24,90,228),('-2 OCTAVES',369,474.5,24,90,213),('-1 OCTAVE',515,476,24,90,194),
 ('+1 OCTAVE',661,472.5,24,90,193),('+2 OCTAVES',810,473.5,24,90,215),
 ('ATTACK',1208,477,24,90,130),('LP FILTER',1353,476.5,24,90,153),('DETUNE',1500.5,477.5,24,90,133),
 ('DRY FX',998.5,455.52,25,0,123),('Q',998.5,751.52,24,0,40),('VOICE MIX',539,748,26,0,214),('EFFECTS',1317.5,752,26,0,149),
 ('HOLD TO SAVE PRESETS',1668,569.5,21,90,373),
 ('OUTPUT',180.5,938,24,90,138),('INPUT',1685.5,925.5,24,90,93),('PRESET',400,1299,25,0,120),('BYPASS',1462,1301,25,0,132)]
for i,y in enumerate([349+58*k for k in range(8)]): labels.append((str(i+1),1571.5,y,23,0,30))   # same rows as the preset LEDs, a bit higher and to the left
def text_img(txt,cap_px,maxlen_px):
    size=200; f=ImageFont.truetype(FB,size)
    bb=f.getbbox('H'); capr=(bb[3]-bb[1])/size
    sz=cap_px/capr; f=ImageFont.truetype(FB,int(round(sz)))
    L=f.getlength(txt)
    if L>maxlen_px: sz*=maxlen_px/L; f=ImageFont.truetype(FB,int(round(sz)))
    bb=f.getbbox(txt); im=Image.new('L',(bb[2]-bb[0]+8,bb[3]-bb[1]+8),0)
    ImageDraw.Draw(im).text((4-bb[0],4-bb[1]),txt,font=f,fill=255)
    return im
import os as _os, json as _js
NOTEXT=_os.environ.get('NOTEXT')=='1'
TEXTS=[]
def text_em(cap_px,maxlen_px,txt):
    size=200; f=ImageFont.truetype(FB,size); bb=f.getbbox('H'); capr=(bb[3]-bb[1])/size
    sz=cap_px/capr; f=ImageFont.truetype(FB,int(round(sz))); L=f.getlength(txt)
    if L>maxlen_px: sz*=maxlen_px/L
    return int(round(sz))
for txt,cx,cy,cap,rot,ml in labels:
    k=s*SS
    X,Y=T(cx,cy); TEXTS.append(dict(s=txt,em=text_em(cap*k,ml*k,txt)/SS/2,x=(X/SS-42)/2,y=(Y/SS)/2,rot=rot))
    if NOTEXT: continue
    im=text_img(txt,cap*k,ml*k)
    if rot: im=im.rotate(rot,expand=True,resample=Image.BICUBIC)
    X,Y=T(cx,cy); canvas.paste(Image.new('L',im.size,255),(int(X-im.width/2),int(Y-im.height/2)),im)
# triangle above HOLD TO SAVE PRESETS
X,Y=T(1668,355.5); r=8*s*SS
d.polygon([(X,Y-r),(X-r*1.0,Y+r*0.8),(X+r*1.0,Y+r*0.8)],fill=255)
# ---------- 3. tick rows, straight and regular, cut at slots and labels ----------
ROWS=[280+47.8*k for k in range(9)]
ZONES=[(171,909,[261,409,557,704,853],[(221.5,357,585),(369,368,581),(515,379,573),(661,376,569),(810,366,581)]),
       (1088,1525,[1146,1290,1437],[(1208,412,542),(1353,400,553),(1500.5,411,544)])]
for zx0,zx1,slots,labs in ZONES:
    for ry in ROWS:
        cuts=[(cx-16,cx+16) for cx in slots]+[(lx-20,lx+20) for lx,y0,y1 in labs if y0-8<=ry<=y1+8]
        cuts.sort(); x=zx0+2; segs=[]
        for a,b in cuts:
            if a>x: segs.append((x,a))
            x=max(x,b)
        if x<zx1-2: segs.append((x,zx1-2))
        for a,b in segs:
            if b-a>3:
                (X0,Y0),(X1,Y1)=T(a,ry-1.8),T(b,ry+1.8); d.rectangle((X0,Y0,X1,Y1),fill=255)
_js.dump(TEXTS,open('silk_texts.json','w'))
if NOTEXT: canvas.save('silk_shapes_ss.png')
silk=canvas.resize((2350,1800),Image.LANCZOS)
silk.save('silk_mask.png')
