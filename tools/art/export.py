# Fog Z v2 : exporte le fond statique 2266 x 1800, les sprites et Layout.h (repere 1133 x 900 = image / 2)
import numpy as np, cv2, sys, os, json
from PIL import Image
sys.path.insert(0,'/home/claude/nine-hands-dsp/strong-pickle/tools'); import photo_controls as pc
A='/mnt/user-data/attachments/c6160ff2-902c-5093-af99-9dd72239ab62/'
OUT='export/'
def ld(p): return np.asarray(Image.open(p).convert('RGBA')).astype(np.float32)/255
def pm(x): y=x.copy(); y[...,:3]*=y[...,3:]; return y
def unpm(p): p=p.copy(); a=p[...,3:]; p[...,:3]=np.where(a>1e-4,p[...,:3]/np.maximum(a,1e-4),0); return p
def crop_alpha(x,pad=2):
    ys,xs=np.where(x[...,3]>0.004); return x[max(ys.min()-pad,0):ys.max()+pad+1, max(xs.min()-pad,0):xs.max()+pad+1]
def resize(x,w,h): return unpm(cv2.resize(pm(x),(w,h),interpolation=cv2.INTER_AREA))
def save(x,name): Image.fromarray((np.clip(x,0,1)*255).astype(np.uint8),'RGBA').save(OUT+name)
s=1800/1377.0; T=lambda xd,yd:((xd-91)*s+85,(yd-2)*s)
U=lambda X,Y:((X-42)/2.0, Y/2.0)          # canvas px (2350 wide) -> plugin units
canvas=pm(ld('FogZ_boitier_2350x1800.png'))
def occlude(al,x0,y0,r,k):
    h,w=al.shape; pad=int(r*3)+2
    m=np.zeros((h+2*pad,w+2*pad),np.float32); m[pad:pad+h,pad:pad+w]=al
    ao=cv2.GaussianBlur(m,(0,0),r)*k
    sl=canvas[y0-pad:y0-pad+m.shape[0],x0-pad:x0-pad+m.shape[1]]; sl[...,:3]*=(1-np.clip(ao,0,0.9)[...,None])
def shadow_of(img,off,bl,op):
    h,w=img.shape[:2]; pad=int(bl*3+off+2)
    sh=np.zeros((h+2*pad,w+2*pad),np.float32); sh[pad:pad+h,pad:pad+w]=img[...,3]
    sh=cv2.warpAffine(sh,np.float32([[1,0,off],[0,1,off]]),sh.shape[::-1]); return cv2.GaussianBlur(sh,(0,0),bl)*op, pad
def paste(img,cx,cy,shadow=None,ao=None,draw=True):
    h,w=img.shape[:2]; x0=int(round(cx-w/2)); y0=int(round(cy-h/2))
    if ao: occlude(img[...,3],x0,y0,*ao)
    if shadow:
        sh,pad=shadow_of(img,*shadow); sl=canvas[y0-pad:y0-pad+sh.shape[0],x0-pad:x0-pad+sh.shape[1]]; sl[...,:3]*=(1-sh[...,None])
    if draw: p=pm(img); sl=canvas[y0:y0+h,x0:x0+w]; sl[:]=p+sl*(1-p[...,3:])
L={}
# ---- slots (static)
slot=crop_alpha(ld(A+'7e4a6e05-image.png'))
SW=int(round(29.5*s)); SLOT_Y0,SLOT_Y1=280-17,280+47.8*8+17; SL=int(round((SLOT_Y1-SLOT_Y0)*s))
k=SW/slot.shape[1]; endh=int(slot.shape[1]*0.55)
top=resize(slot[:endh],SW,int(endh*k)); bot=resize(slot[-endh:],SW,int(endh*k)); mid=resize(slot[endh:-endh],SW,SL-top.shape[0]-bot.shape[0])
slotT=np.concatenate([top,mid,bot],0)
VOICE=[261,409,557,704,853]; EFFECT=[1146,1290,1437]
for xd in VOICE+EFFECT: paste(slotT,*T(xd,(SLOT_Y0+SLOT_Y1)/2),ao=(4,0.35))
L['faderX']=[U(*T(xd,0))[0] for xd in VOICE+EFFECT]
L['travelTop']=U(0,T(0,280.0)[1])[1]; L['travelBot']=U(0,T(0,280+47.8*8)[1])[1]
# ---- fader cap sprite: cap + its cast shadow, 2 px per unit
cap=crop_alpha(ld(A+'e842650a-image.png')); CW=int(round(44*s)); capT=resize(cap,CW,int(round(cap.shape[0]*CW/cap.shape[1])))
sh,pad=shadow_of(capT,7,5,0.55)
spr=np.zeros((capT.shape[0]+2*pad,capT.shape[1]+2*pad,4),np.float32); spr[...,3]=sh
p=pm(capT); reg=pm(spr); reg[pad:pad+capT.shape[0],pad:pad+capT.shape[1]]=p+reg[pad:pad+capT.shape[0],pad:pad+capT.shape[1]]*(1-p[...,3:])
save(unpm(reg),'fader_cap.png'); L['capSprite']=(spr.shape[1]/2,spr.shape[0]/2); L['capSize']=(capT.shape[1]/2,capT.shape[0]/2)
# ---- push buttons : released baked, pressed sprite drawn over
btnUp=crop_alpha(ld(A+'6e1c3dff-image.png')); btnDn=crop_alpha(ld(A+'9ce5bad3-image.png'))
BD=int(round(122*s)); bu=resize(btnUp,BD,BD); bd=resize(btnDn,BD,BD); save(bd,'button_down.png')
L['btn']=[U(*T(998.5,yd)) for yd in (356,656)]; L['btnS']=BD/2
for yd in (356,656): paste(bu,*T(998.5,yd),shadow=(5,4,0.5),ao=(6,0.5))
# ---- LEDs : off baked, lit sprites + halos drawn by the editor
NEWB=float(open('led/bezel_scale.txt').read()); B=72*s*NEWB; F=56*s*NEWB; D=40*s
def ledspr(name,state,diam): return resize(ld(f'led/{name}_{state}.png'),int(round(diam)),int(round(diam)))
leds={'dry':(998.5,237.5,B,'led_lens'),'q':(998.5,529.5,B,'led_lens'),'pre':(697.5,1136,F,'led_lens'),'byp':(1157.5,1135,F,'led_lens')}
for i in range(8): leds[f'p{i}']=(1613.5,349+58*i,D,'led_dome')
for key,(xd,yd,dm,nm) in leds.items():
    paste(ledspr(nm,'off',dm),*T(xd,yd),shadow=(dm*0.04,dm*0.05,0.45),ao=(dm*0.06,0.55))
    L['led_'+key]=U(*T(xd,yd))
L['ledLens']=int(round(B))/2; L['ledFs']=int(round(F))/2; L['ledDome']=int(round(D))/2
for st in ('red','amber','green'):
    save(ledspr('led_lens',st,128),f'lens_{st}.png')
    save(resize(ld(f'led/led_lens_halo_{st}.png'),384,384),f'halo_{st}.png')
save(ledspr('led_dome','amber',96),'dome_amber.png')
save(resize(ld('led/led_dome_halo_amber.png'),288,288),'halo_dome.png')
# ---- footswitches (kit photo, Echoflex) baked ; pressed = shade drawn by the editor
spr,refl,S_,br=pc.footswitch_sprite(150*s/2,2); fs=spr.astype(np.float32)/255
for xd in (400,1460): paste(fs,*T(xd,1170),ao=(9,0.45))
L['fs']=[U(*T(xd,1170)) for xd in (400,1460)]; L['fsBtnR']=br*2/2/1.0; L['fsHitR']=S_/1.9/2*2/2
# ---- jacks
jr,_,_=pc.jack_sprite(109.25,2,1); jl,_,_=pc.jack_sprite(109.25,2,-1)
for j,xc,yd in [(jl/255,85+3-jl.shape[1]/2,938),(jr/255,2265-3+jr.shape[1]/2,925.5)]: paste(j,xc,T(0,yd)[1],ao=(5,0.5))
# ---- preset knob : AO baked, layers drawn by the editor (they include their own shadow)
sys.path.insert(0,os.path.abspath('knob')); os.chdir('knob'); import sim; os.chdir('..')
f=sim.frame(-105,0,np.zeros((1024,1024,4),np.float32)); S=int(round(2*124/0.8232)); fk=cv2.resize(f,(S,S),interpolation=cv2.INTER_AREA)
occlude(fk[...,3],int(2076-S/2),int(274.5-S/2),10,0.45)
L['knob']=U(2076,274.5); L['knobS']=S/2; L['knobR']=124/2
for n in ('shadow','crown','cap','marker','highlight'):
    im=Image.open(f'knob/preset_{n}.png').resize((512,512),Image.LANCZOS); im.save(OUT+f'knob_{n}.png')
# ---- preset pill : shadow + AO baked, pill drawn by the editor
PW,PH=800,76; pcx,pcy=1175,1592
pill=np.zeros((PH+12,PW+12,4),np.float32); cv2.rectangle(pill,(6+PH//2,6),(6+PW-PH//2,6+PH),(0,0,0,1),-1)
for cx in (6+PH//2,6+PW-PH//2): cv2.circle(pill,(cx,6+PH//2),PH//2,(0,0,0,1),-1)
paste(pill,pcx,pcy,shadow=(2,2,0.35),ao=(4,0.35),draw=False)
L['pill']=(U(pcx-PW/2,pcy-PH/2),PW/2,PH/2)
L['logo']=U(1175,T(0,1300)[1]); L['logoW']=210
# ---- background, cropped on case + jacks
bg=unpm(canvas)[:,42:2308]
Image.fromarray((np.clip(bg,0,1)*255).astype(np.uint8),'RGBA').save(OUT+'background.png')
json.dump(L,open(OUT+'layout.json','w'),indent=1)
print({k:v for k,v in L.items() if not k.startswith('led_p')})
