import numpy as np, cv2, sys, os
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0,'/home/claude/nine-hands-dsp/strong-pickle/tools'); import photo_controls as pc
A='/mnt/user-data/attachments/c6160ff2-902c-5093-af99-9dd72239ab62/'
def ld(p): return np.asarray(Image.open(p).convert('RGBA')).astype(np.float32)/255
def pm(x): y=x.copy(); y[...,:3]*=y[...,3:]; return y
def unpm(p): p=p.copy(); a=p[...,3:]; p[...,:3]=np.where(a>1e-4,p[...,:3]/np.maximum(a,1e-4),0); return p
def crop_alpha(x,pad=2):
    ys,xs=np.where(x[...,3]>0.004); return x[max(ys.min()-pad,0):ys.max()+pad+1, max(xs.min()-pad,0):xs.max()+pad+1]
def resize(x,w,h): return unpm(cv2.resize(pm(x),(w,h),interpolation=cv2.INTER_AREA))
s=1800/1377.0; T=lambda xd,yd:((xd-91)*s+85,(yd-2)*s)
GLOW=float(sys.argv[1]) if len(sys.argv)>1 else 1.0
canvas=pm(ld('FogZ_boitier_2350x1800.png'))
# ---- silkscreen: cream ink following the paint relief a little
silk=np.asarray(Image.open('silk_mask.png')).astype(np.float32)/255
ink=np.array([0.886,0.855,0.808],np.float32)
lum=canvas[...,:3].mean(2,keepdims=True); hp=lum-cv2.GaussianBlur(lum,(0,0),3)[...,None]
inkc=np.clip(ink+hp*0.9,0,1)
a=silk[...,None]*0.96*canvas[...,3:]
canvas[...,:3]=canvas[...,:3]*(1-a)+inkc*a
def occlude(al,x0,y0,r,k):
    # ambient occlusion: soft darkening of the panel right around an object that sits on it (no offset)
    h,w=al.shape; pad=int(r*3)+2
    m=np.zeros((h+2*pad,w+2*pad),np.float32); m[pad:pad+h,pad:pad+w]=al
    ao=cv2.GaussianBlur(m,(0,0),r)*k
    sl=canvas[y0-pad:y0-pad+m.shape[0],x0-pad:x0-pad+m.shape[1]]; sl[...,:3]*=(1-np.clip(ao,0,0.9)[...,None])
def paste(img,cx,cy,shadow=None,premult=False,ao=None):
    h,w=img.shape[:2]; x0=int(round(cx-w/2)); y0=int(round(cy-h/2))
    if ao: occlude(img[...,3],x0,y0,*ao)
    if shadow:
        off,bl,op=shadow; al=img[...,3]; pad=int(bl*3+off+2)
        sh=np.zeros((h+2*pad,w+2*pad),np.float32); sh[pad:pad+h,pad:pad+w]=al
        sh=cv2.warpAffine(sh,np.float32([[1,0,off],[0,1,off]]),sh.shape[::-1]); sh=cv2.GaussianBlur(sh,(0,0),bl)*op
        sl=canvas[y0-pad:y0-pad+sh.shape[0],x0-pad:x0-pad+sh.shape[1]]; sl[...,:3]*=(1-sh[...,None])
    p=img if premult else pm(img); sl=canvas[y0:y0+h,x0:x0+w]; sl[:]=p+sl*(1-p[...,3:])
# ---- slots + caps
slot=crop_alpha(ld(A+'7e4a6e05-image.png'))
SW=int(round(29.5*s)); SLOT_Y0,SLOT_Y1=280-17,280+47.8*8+17; SL=int(round((SLOT_Y1-SLOT_Y0)*s));   # slot ends just past the travel (hidden under the cap at the stops)
k=SW/slot.shape[1]; endh=int(slot.shape[1]*0.55)
top=resize(slot[:endh],SW,int(endh*k)); bot=resize(slot[-endh:],SW,int(endh*k)); mid=resize(slot[endh:-endh],SW,SL-top.shape[0]-bot.shape[0])
slotT=np.concatenate([top,mid,bot],0)
VOICE=[261,409,557,704,853]; EFFECT=[1146,1290,1437]
for xd in VOICE+EFFECT: paste(slotT,*T(xd,(SLOT_Y0+SLOT_Y1)/2),ao=(4,0.35))
cap=crop_alpha(ld(A+'e842650a-image.png')); CW=int(round(44*s)); capT=resize(cap,CW,int(round(cap.shape[0]*CW/cap.shape[1])))
YTOP,YBOT=280.0,280+47.8*8          # travel: cap centre exactly on the top / bottom line (half the cap past it, no more)
import json as _j
POS=_j.loads(os.environ.get('FADERS','[1,0,0.5,1,0,1,0.5,0]'))
for xd,yd in zip(VOICE+EFFECT,[YBOT+(YTOP-YBOT)*v for v in POS]): paste(capT,*T(xd,yd),shadow=(7,5,0.55),ao=(3,0.3))
# ---- push buttons
btn=crop_alpha(ld(A+'6e1c3dff-image.png')); BD=int(round(122*s)); btnT=resize(btn,BD,BD)
for yd in [356,656]: paste(btnT,*T(998.5,yd),shadow=(5,4,0.5),ao=(6,0.5))
# ---- LEDs (halo dosed by Glow)
NEWB=float(open('led/bezel_scale.txt').read())
def led(name,state,xd,yd,diam,lvl=1.0):
    cx,cy=T(xd,yd)
    if state!='off':
        h=ld(f'led/{name}_halo_{state}.png'); hs=int(round(diam*3)); h=resize(h,hs,hs); h[...,3]*=lvl*GLOW
        x0=int(round(cx-hs/2)); y0=int(round(cy-hs/2)); sl=canvas[y0:y0+hs,x0:x0+hs]; g=h[...,:3]*h[...,3:]
        sl[...,:3]=1-(1-sl[...,:3])*(1-g)
    paste(resize(ld(f'led/{name}_{state}.png'),int(round(diam)),int(round(diam))),cx,cy,shadow=(diam*0.04,diam*0.05,0.45),ao=(diam*0.06,0.55))
B=72*s*NEWB; F=56*s*NEWB; D=40*s
led('led_lens','amber',998.5,237.5,B); led('led_lens','red',998.5,529.5,B,0.6)   # lens only, same size
for i in range(8): led('led_dome','amber' if i==0 else 'off',1613.5,349+58*i,D)
led('led_lens','red',697.5,1136,F); led('led_lens','off',1157.5,1135,F)
# ---- footswitches (kit photo, Echoflex)
spr,refl,S_,br=pc.footswitch_sprite(150*s/2,2)
fs=spr.astype(np.float32)/255
for xd in [400,1460]: paste(fs,*T(xd,1170),ao=(9,0.45))
# ---- jacks (kit photo): OUT left, IN right, at the height of their labels
jr,_,_=pc.jack_sprite(109.25,2,1); jl,_,_=pc.jack_sprite(109.25,2,-1)   # 50 % smaller, then +15 %
for j,xc,yd in [(jl/255,85+3-jl.shape[1]/2,938),(jr/255,2265-3+jr.shape[1]/2,925.5)]:   # glued 3 px under the edge
    paste(j,xc,T(0,yd)[1],ao=(5,0.5))
# ---- preset knob
sys.path.insert(0,os.path.abspath('knob')); os.chdir('knob'); import sim; os.chdir('..')
f=sim.frame(-105,0,np.zeros((1024,1024,4),np.float32)); S=int(round(2*124/0.8232)); fk=cv2.resize(f,(S,S),interpolation=cv2.INTER_AREA)
x0=int(2076-S/2); y0=int(274.5-S/2); occlude(fk[...,3],x0,y0,10,0.45); sl=canvas[y0:y0+S,x0:x0+S]; sl[:]=fk+sl*(1-fk[...,3:])
# ---- preset bar (reference pill 400 x 38 units = 800 x 76 px), centred under the bottom LEDs
SS=4; PW,PH=800,76; pcx,pcy=1175,1592
pill=Image.new('RGBA',(PW*SS+40,PH*SS+40),(0,0,0,0)); dp=ImageDraw.Draw(pill)
o=20; r=PH*SS/2
dp.rounded_rectangle((o-6,o-6,o+PW*SS+6,o+PH*SS+6),radius=r+6,fill=(20,8,8,150))          # thin dark outline
dp.rounded_rectangle((o,o,o+PW*SS,o+PH*SS),radius=r,fill=(206,198,188,255))               # 1 px light rim
dp.rounded_rectangle((o+4,o+4,o+PW*SS-4,o+PH*SS-4),radius=r-4,fill=(14,14,16,255))        # black face
fnt=ImageFont.truetype('/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf',46*SS)
txt='Organ Pad'; tw=dp.textlength(txt,font=fnt); bb=fnt.getbbox(txt)
hb=fnt.getbbox('H')   # centre the capital height (top of capitals -> baseline), descenders ignored
dp.text((o+PW*SS/2-tw/2,o+PH*SS/2-(hb[1]+hb[3])/2),txt,font=fnt,fill=(238,240,244,255))
tri=5.5*2*SS; ax=34*2*SS/2
for sgn,cx in [(-1,o+ax),(1,o+PW*SS-ax)]:
    cy=o+PH*SS/2; dp.polygon([(cx-sgn*tri*0.8,cy-tri),(cx-sgn*tri*0.8,cy+tri),(cx+sgn*tri*0.8,cy)],fill=(153,153,153,255))
pill=pill.resize((pill.width//SS,pill.height//SS),Image.LANCZOS)
paste(np.asarray(pill).astype(np.float32)/255,pcx,pcy,shadow=(2,2,0.35),ao=(4,0.35))
# ---- logo (official white SVG), bottom centre between PRESET and BYPASS
logo=crop_alpha(ld('logo/logo_white.png'),0); LW=420; lg=resize(logo,LW,int(round(logo.shape[0]*LW/logo.shape[1]))); lg[...,:3]*=0.93
paste(lg,1175,T(0,1300)[1])
out=unpm(canvas)
Image.fromarray((np.clip(out,0,1)*255).astype(np.uint8),'RGBA').save(f'preview_full_glow{int(GLOW*100)}.png')
