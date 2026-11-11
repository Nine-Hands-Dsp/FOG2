import numpy as np, cv2
from PIL import Image
SC='/tmp/claude-0/-home-claude/c6160ff2-902c-5093-af99-9dd72239ab62/scratchpad/'
src=np.asarray(Image.open(SC+'fogz.png').convert('RGB')).astype(np.float32)
W,H=2350,1800
s=1800/1377.0
def T(xd,yd): return ((xd-91)*s+85,(yd-2)*s)
OX0,OY0=85.0,0.0; OX1,OY1=2265.0,1800.0; R_OUT=73   # sides reach the jacks (jack 190 units, glued 3 px under the edge)
IX0,IY0=T(128,34); IX1,IY1=T(1722.5,1354.5); R_IN=98
rng=np.random.default_rng(7)
yy,xx=np.mgrid[0:H,0:W].astype(np.float32)

def rrect_sdf(x0,y0,x1,y1,r):
    cx,cy=(x0+x1)/2,(y0+y1)/2; hx,hy=(x1-x0)/2-r,(y1-y0)/2-r
    qx=np.abs(xx-cx)-hx; qy=np.abs(yy-cy)-hy
    return np.hypot(np.maximum(qx,0),np.maximum(qy,0))+np.minimum(np.maximum(qx,qy),0)-r
d_out=rrect_sdf(OX0,OY0,OX1,OY1,R_OUT)     # <0 inside enclosure
d_in =rrect_sdf(IX0,IY0,IX1,IY1,R_IN)      # <0 inside red panel

# ---------- low-frequency colour fields taken from the design (its lighting) ----------
def field(mask_d, grid=24):
    h,w,_=src.shape; out=np.zeros((h//grid+1,w//grid+1,3),np.float32); ok=np.zeros(out.shape[:2],bool)
    for gy in range(out.shape[0]):
        for gx in range(out.shape[1]):
            p=src[gy*grid:(gy+1)*grid,gx*grid:(gx+1)*grid]; m=mask_d[gy*grid:(gy+1)*grid,gx*grid:(gx+1)*grid]
            if m.sum()>grid*grid*0.3:
                out[gy,gx]=np.median(p[m],0); ok[gy,gx]=True
    # fill holes
    u8=np.clip(out,0,255).astype(np.uint8)
    out=cv2.inpaint(u8,(~ok).astype(np.uint8)*255,5,cv2.INPAINT_TELEA).astype(np.float32)
    out=cv2.GaussianBlur(out,(0,0),2.5)
    return out
L=src.mean(2); S=src.max(2)-src.min(2)
redm=(src[...,0]-src[...,1]>45)&(L<120)
redm=cv2.erode(redm.astype(np.uint8),np.ones((5,5),np.uint8)).astype(bool)
creamm=(L>185)&(S<30)
cm=np.zeros_like(creamm); cm[:,80:140]=1; cm[:,1710:1770]=1; cm[0:36,:]=1; cm[1350:,:]=1
creamm&=cm.astype(bool)
def polyfield(mask,deg=2):
    ys,xs=np.where(mask); idx=np.random.default_rng(0).choice(len(ys),min(60000,len(ys)),replace=False)
    ys,xs=ys[idx]/1376.0,xs[idx]/1840.0
    terms=lambda X,Y:[X**i*Y**j for i in range(deg+1) for j in range(deg+1-i)]
    A=np.stack(terms(xs,ys),1); out=[]
    for c in range(3):
        v=src[ys.astype(int) if False else (ys*1376).astype(int),(xs*1840).astype(int),c]
        coef,*_=np.linalg.lstsq(A,v,rcond=None)
        # robust: refit without outliers (shadows, prints)
        r=v-A@coef; k=np.abs(r)<2*r.std(); coef,*_=np.linalg.lstsq(A[k],v[k],rcond=None)
        out.append(coef)
    xd=(xx-85)/s+91; yd=yy/s+2
    X,Y=xd/1840.0,yd/1376.0
    return np.dstack([sum(cf*t for cf,t in zip(co,terms(X,Y))) for co in out]).astype(np.float32)
# exclude dark zones around controls from the red sample
redm&=(L>55)
def warp_field(f,grid):
    # design pixel -> target mapping inverse
    xd=(xx-85)/s+91; yd=yy/s+2
    return cv2.remap(f,(xd/grid-0.5).astype(np.float32),(yd/grid-0.5).astype(np.float32),cv2.INTER_CUBIC,borderMode=cv2.BORDER_REPLICATE)
red_lf=polyfield(redm,2); cream_lf=polyfield(creamm,1)

# ---------- procedural textures ----------
def bandnoise(s1,s2,seed):
    r=np.random.default_rng(seed).standard_normal((H,W)).astype(np.float32)
    a=cv2.GaussianBlur(r,(0,0),s1)-cv2.GaussianBlur(r,(0,0),s2)
    return a/a.std()
# crinkle (wrinkle finish): worm-like ridges at zero crossings of band-passed, domain-warped noise
n=bandnoise(2.4,5.0,1)
wx=bandnoise(8,18,2)*3; wy=bandnoise(8,18,3)*3
n=cv2.remap(n,(xx+wx).astype(np.float32),(yy+wy).astype(np.float32),cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT)
ridge=np.clip(1-np.abs(n)/0.55,0,1)**1.6
h_red=cv2.GaussianBlur(ridge,(0,0),0.9)*1.0+bandnoise(1.0,2.0,4)*0.05+bandnoise(14,40,5)*0.12
# cream powder coat: very fine grain + soft orange peel
h_cr=bandnoise(0.8,1.8,6)*0.10+bandnoise(4,9,7)*0.18+np.clip(1-np.abs(bandnoise(3.6,7,8))/0.5,0,1)**2*0.25

def shade(h,strength,lightK=1.6):
    gx=cv2.Sobel(h,cv2.CV_32F,1,0,ksize=3)/8; gy=cv2.Sobel(h,cv2.CV_32F,0,1,ksize=3)/8
    nx,ny,nz=-gx*strength,-gy*strength,np.ones_like(h)
    nn=np.sqrt(nx*nx+ny*ny+nz*nz); nx/=nn; ny/=nn; nz/=nn
    l=np.array([-1,-1,lightK],np.float32); l/=np.linalg.norm(l)
    diff=nx*l[0]+ny*l[1]+nz*l[2]
    base=l[2]
    hv=np.array([l[0],l[1],l[2]+1]); hv/=np.linalg.norm(hv)
    spec=np.clip(nx*hv[0]+ny*hv[1]+nz*hv[2],0,1)**40
    return diff/base, spec
dr,sr_=shade(h_red,3.4)
dc,sc_=shade(h_cr,3.0)

red=red_lf*(0.80+0.20*dr[...,None])+ (sr_[...,None]*np.array([60,40,36]))*0.35
cream=cream_lf*(0.93+0.07*dc[...,None])+sc_[...,None]*10

# ---------- geometry shading ----------
# outer rounded edge of the enclosure (bevel ~16 px): light from top-left
bev=16.0
t=np.clip(-d_out/bev,0,1)          # 0 at edge -> 1 inside
# approximate edge normal from sdf gradient
gx=cv2.Sobel(d_out,cv2.CV_32F,1,0,ksize=3)/8; gy=cv2.Sobel(d_out,cv2.CV_32F,0,1,ksize=3)/8
gn=np.sqrt(gx*gx+gy*gy)+1e-6; ex,ey=gx/gn,gy/gn          # outward normal
slope=np.sqrt(np.clip(1-(t)**2,0,1))                       # quarter-round profile
lam=(-ex*-1+-ey*-1)/np.sqrt(2)                              # facing the light (top-left) >0
edge_shade=1+slope*(0.22*np.clip(-lam,-1,1)*-1)            # brighter toward light
edge_shade=1+slope*0.22*np.clip((-ex-ey)/np.sqrt(2),-1,1)
edge_shade-= (1-t)**3*0.25                                 # darker right at the silhouette
cream=cream*edge_shade[...,None]

# recess of the red panel: step down, inner shadow on the top-left inside, light rim bottom-right
gx2=cv2.Sobel(d_in,cv2.CV_32F,1,0,ksize=3)/8; gy2=cv2.Sobel(d_in,cv2.CV_32F,0,1,ksize=3)/8
gn2=np.sqrt(gx2*gx2+gy2*gy2)+1e-6; fx,fy=gx2/gn2,gy2/gn2
toward=np.clip((-fx-fy)/np.sqrt(2),-1,1)    # +1 on top/left walls
inside=-d_in
sh=np.exp(-np.clip(inside,0,None)/5.0)*np.clip(toward,0,1)*0.45 + np.exp(-np.clip(inside,0,None)/2.0)*0.20
red=red*(1-np.clip(sh,0,0.6))[...,None]
# cream lip just outside the panel: bottom/right lips catch light, top/left lips slightly darker
lip=np.exp(-np.clip(d_in,0,None)/2.2)*(d_in>0)
cream=cream*(1+lip*(0.10*np.clip(-toward,0,1)-0.10*np.clip(toward,0,1)))[...,None]

# composite with antialiased boundaries
a_in=np.clip(0.5-d_in,0,1)[...,None]
rgb=red*a_in+cream*(1-a_in)
# thin dark seam at the panel edge
seam=np.exp(-(d_in/0.9)**2)*0.35
rgb*= (1-seam)[...,None]
alpha=np.clip(0.5-d_out,0,1)
out=np.dstack([np.clip(rgb,0,255),alpha*255]).astype(np.uint8)
Image.fromarray(out,'RGBA').save('FogZ_boitier_2350x1800.png')
print('ok', OX0,OX1,IX0,IX1,IY0,IY1)
