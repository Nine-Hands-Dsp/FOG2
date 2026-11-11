import numpy as np, cv2
from PIL import Image
src=np.asarray(Image.open('/mnt/user-data/attachments/c6160ff2-902c-5093-af99-9dd72239ab62/227c7683-image.png').convert('RGBA')).astype(np.float32)
# recentre on the fitted circle (512.05, 512.10) -> 511.5
def shift(img,dx,dy):
    p=img.copy(); p[...,:3]*=p[...,3:]/255
    o=cv2.warpAffine(p,np.float32([[1,0,dx],[0,1,dy]]),(1024,1024),flags=cv2.INTER_CUBIC)
    o=np.clip(o,0,None); a=o[...,3:]; o[...,:3]=np.where(a>0.5,o[...,:3]*255/np.maximum(a,1e-3),0); return np.clip(o,0,255)
img=shift(src,511.5-512.05,511.5-512.10)
C=511.5; R=421.5
yy,xx=np.mgrid[0:1024,0:1024].astype(np.float32); r=np.hypot(xx-C,yy-C); th=np.arctan2(yy-C,xx-C)
L=img[...,:3].mean(2)
# ---- marker: dark stroke near the vertical axis, top half
band=(np.abs(xx-519)<22)&(yy>160)&(yy<410)
bg=cv2.medianBlur(np.clip(L,0,255).astype(np.uint8),31).astype(np.float32)
mk=np.clip((bg-L-12)/25,0,1)*band
mk=cv2.GaussianBlur(mk,(0,0),0.6)
ys,xs=np.where(mk>0.5); mcx=np.average(xx[mk>0.5]); print('marker x',xs.min(),xs.max(),'centre',mcx,'y',ys.min(),ys.max())
marker=np.zeros_like(img); marker[...,:3]=img[...,:3]; marker[...,3]=mk*255
marker=shift(marker,C-mcx,0)          # radial
# remove marker from the body (inpaint)
hole=(cv2.dilate((mk>0.05).astype(np.uint8),np.ones((7,7),np.uint8))*255)
body=img.copy(); body[...,:3]=cv2.inpaint(np.clip(img[...,:3],0,255).astype(np.uint8),hole,6,cv2.INPAINT_TELEA).astype(np.float32)
Lb=body[...,:3].mean(2)
# ---- fixed light: low angular harmonics (1..3) of each ring -> highlight ; residual turns
NA=1440; rs=np.arange(0,424,1.0)
TH=np.linspace(-np.pi,np.pi,NA,endpoint=False)
PX=(C+np.cos(TH)[None]*rs[:,None]).astype(np.float32); PY=(C+np.sin(TH)[None]*rs[:,None]).astype(np.float32)
pol=cv2.remap(Lb,PX,PY,cv2.INTER_LINEAR)
F=np.fft.rfft(pol,axis=1); F[:,0]=0; F[:,4:]=0; lowp=np.fft.irfft(F,NA,axis=1)
# cap interior: use a smooth 2-D field instead of rings near the centre (rings are noisy at small r)
lowp=cv2.GaussianBlur(lowp.astype(np.float32),(0,0),sigmaX=0.1,sigmaY=1.2)
# back to cartesian
ti=((th+np.pi)/(2*np.pi)*NA).astype(np.float32); ri=r.astype(np.float32)
delta=cv2.remap(lowp,ti,ri,cv2.INTER_LINEAR,borderMode=cv2.BORDER_WRAP)
delta*=np.clip((R-1-r)/2,0,1)
flat=body.copy(); flat[...,:3]=np.clip(body[...,:3]-delta[...,None]*(body[...,:3]/np.maximum(Lb[...,None],1)),0,255)
base=np.maximum(Lb-delta,1)
hl=np.zeros_like(img); pos=delta>0; hl[...,:3]=np.where(pos[...,None],255,0)
hl[...,3]=np.clip(np.where(pos,delta/np.maximum(255-base,1),-delta/base),0,1)*255*np.clip((R-4-r)/3,0,1)
# ---- split crown / cap
RG=352.0
crown=flat.copy(); crown[...,3]*=np.clip((r-(RG-6))/2,0,1)       # crown starts just inside the groove
cap=flat.copy();   cap[...,3]*=np.clip((RG+3-r)/2,0,1)            # cap overlaps the groove
# ---- shadow: centred soft disc, no offset
sh=np.zeros_like(img); sh[...,:3]=[24,22,20]
sh[...,3]=cv2.GaussianBlur((r<R-2).astype(np.float32),(0,0),12)*0.55*255
for k,v in {'preset_cap':cap,'preset_crown':crown,'preset_marker':marker,'preset_shadow':sh,'preset_highlight':hl}.items():
    Image.fromarray(np.clip(v,0,255).astype(np.uint8),'RGBA').save(k+'.png')
# check light direction of the fixed layer
d=delta[(r<330)]; print('delta range',d.min(),d.max())
i=np.unravel_index(np.argmax(delta*(r<340)),delta.shape); print('brightest',np.degrees(np.arctan2(i[0]-C,i[1]-C)))
