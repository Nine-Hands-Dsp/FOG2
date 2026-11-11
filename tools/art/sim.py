import numpy as np, cv2
from PIL import Image
L={k:np.asarray(Image.open(f'preset_{k}.png')).astype(np.float32)/255 for k in ['shadow','crown','cap','marker','highlight']}
def rot(img,deg,dx=0,dy=0):
    M=cv2.getRotationMatrix2D((511.5,511.5),-deg,1.0); M[0,2]+=dx; M[1,2]+=dy
    p=img.copy(); p[...,:3]*=p[...,3:]
    return cv2.warpAffine(p,M,(1024,1024),flags=cv2.INTER_CUBIC)   # premultiplied
def over(dst,src):  # premultiplied
    return src+dst*(1-src[...,3:])
def pm(img): p=img.copy(); p[...,:3]*=p[...,3:]; return p
stack=np.zeros((1024,1024,4),np.float32)
for k in ['crown','cap','marker']: stack=over(stack,pm(L[k]))
def unpm(p): p=p.copy(); p[...,:3]=np.where(p[...,3:]>1e-4,p[...,:3]/np.maximum(p[...,3:],1e-4),0); return p
stack_u=unpm(stack)
def frame(angle,blur=0.0,bg=None):
    off=0.025*1024
    def blurred(img,dx=0,dy=0):
        if blur<=0: return rot(img,angle,dx,dy)
        n=int(np.clip(np.ceil(blur/3)+1,4,16)); acc=0
        for k in range(n): acc=acc+rot(img,angle-blur*k/(n-1),dx,dy)
        return acc/n
    out=bg.copy() if bg is not None else np.zeros((1024,1024,4),np.float32)
    out=over(out,blurred(L['shadow'],off,off))
    out=over(out,blurred(stack_u))
    out=over(out,pm(L['highlight']))
    return out
if __name__=='__main__':
    bg=np.zeros((1024,1024,4),np.float32); bg[...]=[0.48,0.15,0.13,1]
    tiles=[frame(a,0,bg) for a in [0,-135,-45,90,135]]
    tiles.append(frame(45,30,bg))
    row=np.concatenate(tiles,1)
    Image.fromarray((np.clip(row[...,:3],0,1)*255).astype(np.uint8)).resize((6*300,300),Image.LANCZOS).save('check_angles.png')
    # compare angle 0 to the user's complete render
    ref=np.asarray(Image.open("/mnt/user-data/attachments/c6160ff2-902c-5093-af99-9dd72239ab62/227c7683-image.png").convert("RGBA")).astype(np.float32)/255
    r=bg.copy(); r=over(r,pm(ref))
    Image.fromarray((np.clip(np.concatenate([r,frame(0,0,bg)],1)[...,:3],0,1)*255).astype(np.uint8)).resize((1200,600),Image.LANCZOS).save('check_ref.png')
