import numpy as np, cv2
from PIL import Image
m=np.asarray(Image.open('silk_shapes_ss.png')).astype(np.float32)   # 4700x3600, 2 px per image px
up=2
big=cv2.resize(m,None,fx=up,fy=up,interpolation=cv2.INTER_CUBIC)
big=cv2.GaussianBlur(big,(0,0),1.0)
bm=(big>127).astype(np.uint8)
cs,hier=cv2.findContours(bm,cv2.RETR_CCOMP,cv2.CHAIN_APPROX_NONE)
SC=2*up*2   # contour px -> units: /up -> SS px, /2 -> image px, /2 -> units
parts=[]; n=0
for c in cs:
    if len(c)<8: continue
    p=c[:,0,:].astype(np.float32)
    k=3; pad=np.concatenate([p[-k:],p,p[:k]]); ker=np.ones(2*k+1)/(2*k+1)
    sm=np.stack([np.convolve(pad[:,0],ker,'valid'),np.convolve(pad[:,1],ker,'valid')],1)
    sm=cv2.approxPolyDP(sm.reshape(-1,1,2).astype(np.float32),0.6,True)[:,0,:]
    u=np.stack([sm[:,0]/SC-21.0, sm[:,1]/SC],1)       # x: (px - 42)/2
    parts.append('M'+' L'.join(f'{x:.2f} {y:.2f}' for x,y in u)+' Z'); n+=len(u)
svg=f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1133 900" width="1133" height="900"><path fill="#E2DACE" fill-rule="evenodd" d="{" ".join(parts)}"/></svg>'
open('export/silk.svg','w').write(svg); print(len(parts),'contours',n,'points',len(svg)//1024,'KB')
