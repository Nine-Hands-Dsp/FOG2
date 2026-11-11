import numpy as np, cv2
from PIL import Image
A='/mnt/user-data/attachments/c6160ff2-902c-5093-af99-9dd72239ab62/'
def ld(f): return np.asarray(Image.open(A+f+'-image.png').convert('RGBA')).astype(np.float32)/255
def fitc(m):
    cs,_=cv2.findContours(m.astype(np.uint8),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE); c=max(cs,key=len)[:,0,:].astype(float)
    x,y=c[:,0],c[:,1]; A_=np.c_[2*x,2*y,np.ones(len(x))]; cx,cy,k=np.linalg.lstsq(A_,x*x+y*y,rcond=None)[0]; return cx,cy,np.sqrt(k+cx*cx+cy*cy)
def square(img,cx,cy,r,size):
    # centre on the fitted circle, crop a square of side 2r*1.02, resize
    h=r*1.02; M=np.float32([[size/(2*h),0,-(cx-h)*size/(2*h)],[0,size/(2*h),-(cy-h)*size/(2*h)]])
    p=img.copy(); p[...,:3]*=p[...,3:]; o=cv2.warpAffine(p,M,(size,size),flags=cv2.INTER_CUBIC if size>img.shape[0] else cv2.INTER_AREA)
    o=np.clip(o,0,1); a=o[...,3:]; o[...,:3]=np.where(a>1e-4,o[...,:3]/np.maximum(a,1e-4),0); return o
def hsv_variants(img,lens):
    out={}
    rgb=(np.clip(img[...,:3],0,1)*255).astype(np.uint8); hsv=cv2.cvtColor(rgb,cv2.COLOR_RGB2HSV).astype(np.float32)
    for name,hshift,sat in [('red',0,1.0),('amber',17,0.95),('green',58,0.9)]:
        h=hsv.copy(); h[...,0]=(h[...,0]+hshift*lens)%180; h[...,1]*=1-(1-sat)*lens
        if name=='green': h[...,2]=np.clip(h[...,2]*(1+0.1*lens),0,255)
        o=img.copy(); o[...,:3]=cv2.cvtColor(h.astype(np.uint8),cv2.COLOR_HSV2RGB).astype(np.float32)/255; out[name]=o
    # off: dark tinted lens, facets kept
    L=img[...,:3].mean(2,keepdims=True)
    off=img.copy(); dark=np.concatenate([0.30*L+0.05,0.07*L+0.03,0.06*L+0.03],2)
    off[...,:3]=img[...,:3]*(1-lens[...,None])+dark*lens[...,None]; out['off']=off
    return out
def halo(size,color,rr):
    yy,xx=np.mgrid[0:size,0:size]; r=np.hypot(xx-size/2+0.5,yy-size/2+0.5)/(size/2)
    a=np.exp(-((np.maximum(r-rr,0))/0.22)**2)*np.clip(1-r,0,1)**0.5*(r>rr*0.8)
    o=np.zeros((size,size,4),np.float32); o[...,:3]=color; o[...,3]=a*0.55; return o
COL={'red':(1,0.16,0.05),'amber':(1,0.62,0.12),'green':(0.25,1,0.25)}
for f,name,SZ in [('6ab1b68d','led_bezel',512),('27e30ec7','led_dome',256)]:
    im=ld(f); cx,cy,r=fitc(im[...,3]>0.5); print(name,cx,cy,r)
    sq=square(im,cx,cy,r,SZ)
    if name=='led_bezel':
        # lens only (no metal ring), framed on its dark seat: same overall size on the pedal
        LR=0.615
        c0=SZ/2-0.5; h=LR*SZ/2
        M=np.float32([[SZ/(2*h),0,-(c0-h+0.5)*SZ/(2*h)],[0,SZ/(2*h),-(c0-h+0.5)*SZ/(2*h)]])
        p=sq.copy(); p[...,:3]*=p[...,3:]; p=cv2.warpAffine(p,M,(SZ,SZ),flags=cv2.INTER_CUBIC)
        yy2,xx2=np.mgrid[0:SZ,0:SZ]; rr2=np.hypot(xx2-c0,yy2-c0)/(SZ/2)
        p*=np.clip((0.995-rr2)/0.01,0,1)[...,None]; p=np.clip(p,0,1)
        a=p[...,3:]; p[...,:3]=np.where(a>1e-4,p[...,:3]/np.maximum(a,1e-4),0)
        hsvL=cv2.cvtColor((np.clip(p[...,:3],0,1)*255).astype(np.uint8),cv2.COLOR_RGB2HSV).astype(np.float32)
        lensL=np.clip((0.93-rr2)/0.03,0,1)*p[...,3]
        for kk,v in hsv_variants(p,cv2.GaussianBlur(lensL.astype(np.float32),(0,0),1.0)).items():
            Image.fromarray((np.clip(v,0,1)*255).astype(np.uint8),'RGBA').save(f'led/led_lens_{kk}.png')
        for cc,v in COL.items():
            Image.fromarray((halo(SZ*3,v,0.95/3)*255).astype(np.uint8),'RGBA').save(f'led/led_lens_halo_{cc}.png')
        # metal ring 50 % narrower: lens untouched (r<0.62), ring 0.62..1.0 squeezed into 0.62..0.81, then re-framed
        R0=0.62; NEW=R0+(1.0-R0)/2
        yy,xx=np.mgrid[0:SZ,0:SZ].astype(np.float32); c=SZ/2-0.5
        rr=np.hypot(xx-c,yy-c)/(SZ/2)*NEW            # output pixel -> radius in old frame (after re-framing)
        src_r=np.where(rr<R0,rr,R0+(rr-R0)*2)
        k=np.where(rr>1e-6,src_r/np.maximum(rr,1e-6),1)*NEW
        mx=(c+(xx-c)*k).astype(np.float32); my=(c+(yy-c)*k).astype(np.float32)
        p=sq.copy(); p[...,:3]*=p[...,3:]
        p=cv2.remap(p,mx,my,cv2.INTER_CUBIC,borderMode=cv2.BORDER_CONSTANT,borderValue=0); p=np.clip(p,0,1)
        a=p[...,3:]; p[...,:3]=np.where(a>1e-4,p[...,:3]/np.maximum(a,1e-4),0); sq=p
        open('led/bezel_scale.txt','w').write(str(NEW))
    hsv=cv2.cvtColor((np.clip(sq[...,:3],0,1)*255).astype(np.uint8),cv2.COLOR_RGB2HSV).astype(np.float32)
    lens=np.clip((hsv[...,1]-90)/60,0,1)*((hsv[...,0]<20)|(hsv[...,0]>165))*sq[...,3]
    yy,xx=np.mgrid[0:SZ,0:SZ]; rr=np.hypot(xx-SZ/2+0.5,yy-SZ/2+0.5)/(SZ/2)
    if name=='led_bezel':
        lr0=np.sqrt((lens>0.5).sum()/np.pi)/(SZ/2)
        lens=np.maximum(lens,np.clip((lr0-0.01-rr)/0.02,0,1))   # whole lens, white-hot centre included
    lens=cv2.GaussianBlur(lens,(0,0),1.0)
    for k,v in hsv_variants(sq,lens).items():
        Image.fromarray((np.clip(v,0,1)*255).astype(np.uint8),'RGBA').save(f'led/{name}_{k}.png')
    # halo sized 3x the LED, light of the lens only
    lr=np.sqrt(lens.sum()/np.pi)/SZ*2   # lens radius / half size
    for c,v in COL.items():
        Image.fromarray((halo(SZ*3,v,lr/3)*255).astype(np.uint8),'RGBA').save(f'led/{name}_halo_{c}.png')
    print(name,'lens radius frac',lr)
