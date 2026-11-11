# Notice Fog Z (NINE HANDS | DSP), francais uniquement, couverture noire « minimale » (gabarit commun a toutes les notices).
# Usage : python3 tools/manual.py <dossier des captures du plugin (n_*.png)> docs/FogZ_Notice_FR_v<version>.pdf
#         (sans dossier de captures : reprend les images de tools/manual_assets)
import os, sys, json, shutil
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (BaseDocTemplate, PageTemplate, NextPageTemplate, Frame, Paragraph, Spacer, Image as RLImage,
                                Table, TableStyle, PageBreak, KeepTogether)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOTS = sys.argv[1] if len(sys.argv) > 2 else None
OUT = sys.argv[-1]
VERSION = "2.0.0"
TMP = os.path.join(os.path.dirname(os.path.abspath(OUT)), "_notice_tmp"); os.makedirs(TMP, exist_ok=True)
ASSETS = os.path.join(ROOT, "tools", "manual_assets")
FONTS = os.path.join(ASSETS, "fonts")
for n, f in (("Pop", "Poppins-Regular"), ("PopL", "Poppins-Light"), ("PopM", "Poppins-Medium"), ("PopB", "Poppins-Bold"),
             ("Title", "BarlowCondensed-ExtraBold")):
    pdfmetrics.registerFont(TTFont(n, os.path.join(FONTS, f + ".ttf")))

ACC = colors.HexColor("#C8372B"); ACC_L = colors.HexColor("#F08A6E")      # rouge de la pedale / LED allumee
DARK = colors.HexColor("#211716"); GREY = colors.HexColor("#6B5F5C"); LIGHT = colors.HexColor("#F6ECE6")
LOGO_PNG = os.path.join(ASSETS, "nine_hands_logo_blanc.png")
NAMES = ["fogz_annotated.png", "fogz_dryfx.png", "fogz_bar.png", "fogz_onoff.png", "fogz_knob.png", "fogz_cover_cutout.png"]

# ---------------------------------------------------------------- illustrations (rendus reels du plugin)
if SHOTS:
    def shot(name): return Image.open(os.path.join(SHOTS, name)).convert("RGB")
    src = shot("n_main.png")
    k = src.height / 900.0                                   # repere du plugin v2 : 1133 x 900 unites (fond 2266 x 1800 / 2)
    FX = [132.6, 229.3, 326.1, 422.2, 519.5, 711.0, 805.2, 901.2]
    marks = [(1, FX[0], 128), (2, FX[1], 128), (3, FX[2], 128), (4, FX[3], 128), (5, FX[4], 128),
             (6, 655, 153.9), (7, 667, 231.4), (8, 655, 344.8), (9, 667, 427.5),
             (10, FX[5], 128), (11, FX[6], 128), (12, FX[7], 128), (13, 1017, 46), (14, 1052, 205),
             (15, 418, 712), (16, 290, 763.4), (17, 719, 712), (18, 850, 763.4), (19, 566.5, 828)]
    ann = src.copy(); dr = ImageDraw.Draw(ann)
    fnt = ImageFont.truetype(os.path.join(FONTS, "Poppins-Bold.ttf"), 30)
    for n, x, y in marks:
        cx, cy, r = x * k, y * k, 25
        dr.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(255, 255, 255), outline=(200, 55, 43), width=5)
        dr.text((cx, cy + 1), str(n), font=fnt, fill=(33, 23, 22), anchor="mm")
    ann.save(os.path.join(TMP, NAMES[0]))

    def crop_u(im, box): return im.crop(tuple(int(v * k) for v in box))
    gap = 18
    def strip(parts, path):
        s = Image.new("RGB", (sum(p.width for p in parts) + gap * (len(parts) - 1), max(p.height for p in parts)), (255, 255, 255))
        x = 0
        for p in parts: s.paste(p, (x, 0)); x += p.width + gap
        s.save(path)
    box_fx = (572, 118, 658, 470)                              # colonne DRY FX / Q : 4 etats
    strip([crop_u(shot(n), box_fx) for n in ("n_main.png", "n_fx1.png", "n_fx2.png", "n_fx3.png")], os.path.join(TMP, NAMES[1]))
    box_bar = (356, 767, 777, 825)                             # pastille au repos / pendant un reglage
    strip([crop_u(src, box_bar), crop_u(shot("n_status.png"), box_bar)], os.path.join(TMP, NAMES[2]))
    box_on = (150, 700, 990, 830)                              # effet actif / bypass
    strip([crop_u(src, box_on)], os.path.join(TMP, NAMES[3]))
    box_kn = (930, 55, 1110, 510)                              # gros bouton + LED 1-8 : preset 1 / preset 4
    strip([crop_u(src, box_kn), crop_u(shot("n_preset4.png"), box_kn)], os.path.join(TMP, NAMES[4]))

    # couverture : pedale detouree avec le canal alpha du fond (boitier + jacks), reflet au sol, halo rouge tres doux
    bg_a = Image.open(os.path.join(ROOT, "background.png")).split()[3].resize(src.size, Image.LANCZOS)
    cut = Image.new("RGBA", src.size, (0, 0, 0, 0)); cut.paste(src, (0, 0), bg_a)
    cut = cut.crop(cut.getbbox()); cw, ch = cut.size
    pad = int(cw * 0.16)
    canvas = Image.new("RGBA", (cw + 2 * pad, int(ch * 1.30) + pad), (0, 0, 0, 255))
    yy, xx = np.mgrid[0:canvas.height, 0:canvas.width].astype(np.float64)
    gcx, gcy = canvas.width / 2, pad + ch * 0.45
    glow = np.exp(-(((xx - gcx) / (cw * 0.62)) ** 2 + ((yy - gcy) / (ch * 0.48)) ** 2)) * 30
    edge = np.clip(np.minimum.reduce([xx, canvas.width - 1 - xx, yy, canvas.height - 1 - yy]) / (pad * 0.9), 0, 1)
    glow *= edge ** 2
    halo = np.dstack([glow * 0.95, glow * 0.30, glow * 0.25, np.full_like(glow, 255)]).astype(np.uint8)
    canvas = Image.alpha_composite(canvas, Image.fromarray(halo, "RGBA"))
    refl = cut.transpose(Image.FLIP_TOP_BOTTOM); ra = np.array(refl).astype(np.float64)
    fade = np.clip(1 - np.arange(refl.height) / (refl.height * 0.22), 0, 1) ** 1.6 * 0.22
    ra[..., 3] *= fade[:, None]
    canvas.alpha_composite(Image.fromarray(ra.astype(np.uint8), "RGBA"), (pad, pad + ch + 6))
    canvas.alpha_composite(cut, (pad, pad))
    canvas = canvas.crop((0, 0, canvas.width, pad + int(ch * 1.20)))
    canvas.convert("RGB").save(os.path.join(TMP, NAMES[5]))
    for n in NAMES: shutil.copy(os.path.join(TMP, n), os.path.join(ASSETS, n))
annotated, dryfx_img, bar_img, onoff_img, knob_img, cover = [os.path.join(ASSETS, n) for n in NAMES]

def img(path, width):
    im = Image.open(path); return RLImage(path, width=width, height=width * im.height / im.width)

st = {
    "h1": ParagraphStyle("h1", fontName="PopB", fontSize=20, leading=24, textColor=ACC, spaceAfter=8, spaceBefore=4, keepWithNext=1),
    "h2": ParagraphStyle("h2", fontName="PopM", fontSize=13, leading=17, textColor=DARK, spaceAfter=4, spaceBefore=10, keepWithNext=1),
    "p": ParagraphStyle("p", fontName="Pop", fontSize=9.6, leading=14, textColor=DARK, spaceAfter=5),
    "tip": ParagraphStyle("tip", fontName="Pop", fontSize=9.0, leading=12.4, textColor=DARK, spaceAfter=3),
    "small": ParagraphStyle("small", fontName="Pop", fontSize=8.2, leading=11.5, textColor=GREY),
    "cell": ParagraphStyle("cell", fontName="Pop", fontSize=8.4, leading=11, textColor=DARK),
    "cellb": ParagraphStyle("cellb", fontName="PopM", fontSize=8.4, leading=11, textColor=DARK),
    "cells": ParagraphStyle("cells", fontName="Pop", fontSize=7.6, leading=9.6, textColor=DARK),
    "cellbs": ParagraphStyle("cellbs", fontName="PopM", fontSize=7.6, leading=9.6, textColor=DARK),
}
def P(t, s="p"): return Paragraph(t, st[s])
def bullets(items, s="p"): return [P("&bull;&nbsp;&nbsp;" + i, s) for i in items]
def table(rows, widths, header=True, small=False):
    data = [[P(c, ("cellbs" if small else "cellb") if (header and r == 0) else ("cells" if small else "cell")) for c in row] for r, row in enumerate(rows)]
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    style = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("LINEBELOW", (0, 0), (-1, -1), 0.3, colors.HexColor("#E6D4CD")),
             ("TOPPADDING", (0, 0), (-1, -1), 2 if small else 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 2 if small else 3)]
    if header: style += [("BACKGROUND", (0, 0), (-1, 0), LIGHT), ("LINEBELOW", (0, 0), (-1, 0), 0.8, ACC)]
    t.setStyle(TableStyle(style)); return t

# ---------------------------------------------------------------- contenu
FACTORY = [  # nom, faders (dry, -2, -1, +1, +2, attack, lp, detune), dry fx, q, description
    ("Organ Pad", (60, 26, 70, 62, 30, 45, 62, 35), 3, 0, "Nappe d'orgue chaleureuse : toutes les voix, montée douce, son direct dans toute la chaîne avec un chorus rotatif lent."),
    ("Baritone Growl", (35, 30, 85, 0, 0, 0, 55, 0), 0, 2, "Direct et octaves graves dans un filtre plus sombre : une guitare baryton qui gronde."),
    ("Theremin-ish", (0, 0, 0, 92, 0, 56, 50, 88), 0, 1, "Octave aiguë seule, passe-bas rond, vibrato rapide et entrée lente : voix sinusoïdale façon thérémine. Mélodies lentes, glissés."),
    ("Cello", (0, 0, 86, 10, 0, 50, 40, 12), 1, 1, "Octave grave, attaque d'archet et filtre sombre : lignes en notes seules au milieu du manche."),
    ("Lower + Upper Clean", (80, 0, 62, 58, 0, 0, 100, 0), 0, 0, "Le classique : la guitare avec une octave en dessous et une au-dessus, sans effet."),
    ("Organ Drawbars", (70, 56, 70, 66, 52, 0, 80, 28), 2, 0, "Toutes les voix en avant, comme un orgue toutes tirettes sorties."),
    ("Glass Choir", (56, 0, 40, 68, 82, 60, 74, 40), 1, 1, "Voix aiguës avec swell et léger chorus : chœur aérien, superbe en arpèges."),
    ("Sub Synth Bass", (20, 66, 85, 0, 0, 8, 30, 0), 2, 3, "Énormes octaves graves, filtre résonant (Q 4) et swell court : basse de synthé."),
    ("12-String Shimmer", (80, 0, 0, 62, 0, 0, 100, 22), 0, 0, "La guitare plus l'octave aiguë avec un chorus doux : une 12 cordes scintillante."),
    ("Reverse Swell", (62, 0, 92, 84, 30, 80, 78, 18), 1, 0, "Montée longue et forte : la note sort de nulle part et finit fort."),
    ("Leslie Rotary", (62, 0, 66, 66, 48, 0, 70, 85), 3, 0, "Voicing d'orgue, Detune en haut : cabine rotative rapide sur les voix aiguës et le direct."),
    ("Fog Horn", (0, 80, 55, 25, 0, 30, 25, 15), 2, 3, "Octaves graves seules, filtre grave résonant et attaque lente : un bourdon de corne de brume."),
]
DFX = ["éteinte", "rouge", "verte", "ambre"]

W = A4[0] - 36 * mm
def story():
    f = [NextPageTemplate("p"), Spacer(1, 1), PageBreak()]
    f.append(P("1. Présentation", "h1"))
    f.append(P("<b>Fog Z</b> est un générateur d'octaves <b>polyphonique</b> inspiré de l'Electro-Harmonix POG2. À partir d'une seule guitare, il fabrique deux octaves en dessous et deux octaves au-dessus de <b>chaque corde d'un accord</b>, les mélange à votre son direct et les sculpte avec une montée de volume (Attack), un filtre passe-bas résonant et un désaccord qui va du chorus au vibrato rotatif. Orgues, violoncelles, 12 cordes, basses de synthé, thérémines : tout se règle aux faders, comme sur la pédale."))
    f.append(P("Huit mémoires sont rangées sur la pédale (gros bouton PRESET) et douze sons d'usine sont proposés dans le menu de presets de votre DAW."))
    f.append(P("2. Installation", "h1"))
    for h, x in [("Windows", "Copiez <i>Fog Z.vst3</i> dans <i>C:\\Program Files\\Common Files\\VST3</i>."),
                 ("macOS", "Copiez <i>Fog Z.vst3</i> dans <i>~/Library/Audio/Plug-Ins/VST3</i>, puis une seule fois dans le Terminal : <i>xattr -cr ~/Library/Audio/Plug-Ins/VST3/\"Fog Z.vst3\"</i> (retire la quarantaine du téléchargement)."),
                 ("Reaper", "Options &gt; Preferences &gt; Plug-ins &gt; VST &gt; <b>Re-scan</b>. Le plugin s'appelle <b>Fog Z (NINE HANDS | DSP)</b>.")]:
        f.append(P(h, "h2")); f.append(P(x))
    f.append(PageBreak())
    f.append(P("3. Vue d'ensemble", "h1"))
    f.append(img(annotated, W))
    rows = [["N°", "Commande", "Rôle"],
            ["1", "DRY OUTPUT", "niveau du son direct"], ["2", "-2 OCTAVES", "deux octaves en dessous"], ["3", "-1 OCTAVE", "une octave en dessous"],
            ["4", "+1 OCTAVE", "une octave au-dessus"], ["5", "+2 OCTAVES", "deux octaves au-dessus"],
            ["6", "LED DRY FX", "routage du son direct (éteinte / rouge / verte / ambre)"], ["7", "Bouton DRY FX", "mode de routage suivant"],
            ["8", "LED Q", "plus elle brille, plus le filtre résonne"], ["9", "Bouton Q", "résonance suivante (4 niveaux)"],
            ["10", "ATTACK", "montée de volume note par note"], ["11", "LP FILTER", "coupure du passe-bas"], ["12", "DETUNE", "chorus / vibrato rotatif des voix aiguës"],
            ["13", "Gros bouton PRESET", "8 crans : tourner charge le preset, clic recharge, maintien 3 s sauvegarde"],
            ["14", "LED 1 à 8", "mémoire sélectionnée"], ["15", "LED PRESET", "fixe : preset chargé ; clignote : modifié"],
            ["16", "Footswitch PRESET", "charge le preset / passe au suivant"], ["17", "LED BYPASS", "allumée : effet actif"],
            ["18", "Footswitch BYPASS", "effet / bypass"], ["19", "Barre de presets", "preset en cours, flèches, menu ; valeurs en direct pendant un réglage"]]
    f.append(Spacer(1, 3 * mm)); f.append(table(rows, [10 * mm, 38 * mm, W - 48 * mm], small=True))
    f.append(PageBreak())
    f.append(P("4. Le mélange des voix", "h1"))
    f.append(P("Le panneau VOICE MIX est la table de mixage des cinq voix. Chaque fader va du silence (en bas) à +3,9 dB (en haut) ; <b>le repère 80 % correspond au gain unité</b>, comme sur la pédale d'origine. Le capuchon s'arrête sur la ligne la plus haute et sur la plus basse. Glisser = régler (Maj = réglage fin), molette = pas à pas, double-clic = valeur par défaut."))
    f += bullets(["<b>DRY OUTPUT</b> : votre guitare intacte. Baissez-le pour n'entendre que les octaves (violoncelle, synthé, thérémine).",
                  "<b>-2 OCTAVES</b> : un quart de la fréquence. Sub profond, orgue 16 pieds, basse de synthé ; à doser sur les accords.",
                  "<b>-1 OCTAVE</b> : la moitié de la fréquence. Basse, baryton, violoncelle : la voix la plus naturelle.",
                  "<b>+1 OCTAVE</b> : le double. 12 cordes, mandoline, orgue cristallin.",
                  "<b>+2 OCTAVES</b> : quatre fois la fréquence. Cloches, sifflet, harmoniques."])
    f.append(P("Les accords", "h2"))
    f.append(P("Le moteur découpe la guitare en environ 190 bandes étroites et ne laisse parler que les bandes qui sont un pic du spectre : chaque corde reçoit sa propre octave. Accords ouverts et power chords sont très bien suivis ; des intervalles très serrés dans le grave peuvent légèrement battre, comme sur la pédale. Baissez alors le -2 ou jouez la partie grave en notes seules."))
    f.append(P("5. Les effets", "h1"))
    f.append(P("Le panneau EFFECTS met en forme les voix d'octave ; le bouton DRY FX décide si le son direct y passe aussi."))
    for h, x in [("ATTACK", "Montée de volume <b>note par note</b> (en bas : coupé, jusqu'à 3 s en haut). La courbe démarre lentement puis s'affirme, et la note est soutenue pendant la montée (jusqu'à +9,5 dB) pour finir fort : l'effet violon / reverse."),
                 ("LP FILTER", "Passe-bas résonant 2 pôles, de 50 Hz à 18 kHz. En bas : orgue et violoncelle ronds ; en haut : tout reste ouvert."),
                 ("DETUNE", "Agit sur les voix +1 et +2 (et sur le direct en DRY FX ambre). Vitesse et profondeur montent ensemble : chorus lent en bas, chorus rapide puis vrai vibrato rotatif en haut.")]:
        f.append(P(h, "h2")); f.append(P(x))
    f.append(P("DRY FX et Q", "h2"))
    f.append(P("Chaque appui sur un bouton passe au mode suivant ; la LED au-dessus l'indique."))
    f.append(table([["LED DRY FX", "Le son direct passe par"], ["éteinte", "rien : direct propre, les effets n'agissent que sur les octaves"], ["rouge", "Attack"],
                    ["verte", "Attack + LP Filter"], ["ambre", "Attack + LP Filter + Detune"]], [28 * mm, W - 28 * mm], small=True))
    f.append(Spacer(1, 2 * mm))
    f.append(P("<b>Q</b> : quatre résonances du LP Filter (plat, 1,5, 3,2 puis 7,5 pour un pic vocal façon wah). La LED Q brille de plus en plus fort ; le niveau est compensé pour que les Q élevés ne sautent pas."))
    f.append(KeepTogether([Spacer(1, 2 * mm), img(dryfx_img, W * 0.34), P("DRY FX / Q : éteintes, puis rouge / Q 2, verte / Q 3, ambre / Q 4.", "small")]))
    f.append(P("6. Presets, footswitches et MIDI", "h1"))
    f.append(P("Fog Z possède huit mémoires, comme la pédale. Chacune garde les huit faders et les modes DRY FX et Q."))
    f.append(table([["Geste", "Effet"],
                    ["Tourner le gros bouton", "glisser vers le haut / la droite ou molette : le bouton saute de cran en cran (butées en 1 et 8) et <b>charge aussitôt</b> le preset"],
                    ["Clic sur le gros bouton", "recharge le preset en cours"],
                    ["Maintien 3 s", "enregistre le son actuel dans la mémoire sélectionnée (les LED 1-8 clignotent à partir de 2 s)"],
                    ["Footswitch PRESET", "charge le preset sélectionné ; déjà chargé : passe au suivant (8 → 1) ; modifié : le recharge"],
                    ["Footswitch BYPASS", "effet / bypass, fondu de 15 ms sans clic ; LED BYPASS allumée = effet actif"],
                    ["LED PRESET", "fixe : preset chargé ; clignote vite : un réglage a changé depuis"]], [42 * mm, W - 42 * mm], small=True))
    f.append(KeepTogether([Spacer(1, 3 * mm), img(knob_img, W * 0.26), P("Gros bouton et LED 1-8 : preset 1, puis preset 4.", "small")]))
    f.append(P("MIDI", "h2"))
    f += bullets(["<b>Aucune commande n'a de CC assigné par défaut</b> : tout passe par le MIDI Learn. Clic droit sur un fader, DRY FX, Q, le gros bouton ou un footswitch &gt; <b>MIDI Learn</b>, puis bougez votre pédale d'expression ou appuyez sur le bouton MIDI. La barre affiche <i>MIDI LEARN</i>, puis confirme (ex. <i>LP FILTER = CC 11</i>).",
                  "<b>Clear MIDI</b> retire une assignation ; clic droit &gt; MIDI &gt; <b>Clear all MIDI assignments</b> les retire toutes. Les assignations sont sauvegardées avec le projet.",
                  "<b>Latching MIDI pedals</b> (clic droit &gt; MIDI) : pour les pédales qui envoient 127 / 0 à chaque appui alterné.",
                  "<b>Program Change 1 à 8</b> : charge les presets 1 à 8. Tous les paramètres sont automatisables dans le DAW."])
    f.append(P("7. Fenêtre et barre de presets", "h1"))
    f.append(P("Fog Z s'ouvre à la hauteur de Ring Think (« 60 % ») et ne peut jamais être plus petite. Clic droit &gt; <b>Plugin size</b> : <b>60 %</b>, <b>75 %</b> ou <b>100 %</b> ; <b>Default size (new windows)</b> choisit la taille d'ouverture de toutes les nouvelles fenêtres de Fog Z. Vous pouvez aussi tirer le coin en bas à droite (proportions conservées). Une taille choisie pour une instance est gardée avec le projet."))
    f.append(P("Clic droit &gt; <b>Glow (halo of the lights)</b> : 25, 50, 75 ou 100 % règle le halo des LED sur la façade (la LED elle-même reste à pleine intensité). Réglage commun à toutes les fenêtres de Fog Z."))
    wt = Table([[[P("La <b>barre de presets</b> et la <b>ligne d'état</b> partagent la même pastille. Au repos, elle affiche le preset en cours (ex. <i>1. Organ Pad</i>, <i>(edited)</i> s'il a été modifié) ; les flèches passent au preset précédent / suivant et un clic sur le nom ouvre le menu des presets (mémoires 1-8, sons d'usine, sauvegarde). Dès qu'un réglage bouge (souris, automation, MIDI), la ligne d'état prend sa place avec la valeur en direct (ex. <i>LP FILTER 310 Hz</i>), puis s'efface au bout de 2,5 s.")],
                 [img(bar_img, 72 * mm), P("Au repos (presets) et pendant un réglage (ligne d'état).", "small")]]], colWidths=[W - 76 * mm, 76 * mm])
    wt.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (0, 0), 0)]))
    f.append(wt)
    f.append(P("8. Presets d'usine", "h1"))
    f.append(P("Les sons 1 à 8 sont rangés dans les mémoires de la pédale ; les 12 apparaissent dans le menu de presets du DAW et dans clic droit &gt; <b>Factory sounds</b>. <b>Restore factory sounds in presets 1-8</b> remet les sons d'usine dans les mémoires."))
    rows = [["N°", "Preset", "Dry / -2 / -1 / +1 / +2", "Att. / LP / Det.", "DRY FX · Q", "Description"]]
    for i, (n, v, d, q, desc) in enumerate(FACTORY):
        rows.append([str(i + 1), "<b>" + n + "</b>", " / ".join(str(x) for x in v[:5]), " / ".join(str(x) for x in v[5:]), f"{DFX[d]} · {q + 1}", desc])
    f.append(table(rows, [7 * mm, 26 * mm, 27 * mm, 20 * mm, 18 * mm, W - 98 * mm], small=True))
    f.append(P("9. Conseils d'utilisation", "h1"))
    f += bullets(["Dans Reaper, placez Fog Z <b>avant</b> la distorsion et le simulateur d'ampli : le suivi des octaves est meilleur sur un signal propre. Une fuzz <b>après</b> Fog Z avec la +1 donne une fuzz octave polyphonique.",
                  "Sur une 7 cordes en Sol ou plus bas, gardez le -2 bas sur les accords et fermez un peu le LP Filter : le grave reste défini.",
                  "Pour une basse : Dry à 0, -1 vers 85 %, LP vers 40 %. Pour un pupitre de violons : Dry à 0, -1 50 %, +1 70 %, Attack 70 %, Detune 40 %.",
                  "Aucune octave ne sort quand vous ne jouez pas : ronflement et souffle d'une guitare branchée sont ignorés."], "tip")
    tech = [["Format", "VST3 (Windows 64 bits, macOS universel Apple Silicon + Intel)"], ["Canaux", "entrée et sortie mono ou stéréo"],
            ["Moteur", "≈ 190 filtres passe-bande complexes à 3 étages, phase multipliée (+1, +2) ou divisée (-1, -2) dans chaque bande ; bandes sous 1 kHz à ≈ 12 kHz"],
            ["Voix", "direct, -2, -1, +1, +2 : de 0 à +3,9 dB (0 dB au repère 80 %)"],
            ["Effets", "Attack 10 ms à 3 s · LP 50 Hz à 18 kHz, 4 Q · Detune 0,15 à 6,6 Hz"],
            ["Presets", "8 mémoires sur la pédale, 12 sons d'usine, sauvegardés avec le projet"],
            ["MIDI", "MIDI Learn sur les 13 commandes (rien d'assigné par défaut), pédales à verrouillage, Program Change 1-8"],
            ["Fenêtre", "60 % (taille minimale) / 75 % / 100 %, jusqu'à 150 % en tirant le coin ; réglage Glow 25 à 100 % ; anti-gel v2 sous Windows"]]
    f.append(KeepTogether([P("10. Caractéristiques techniques", "h1"), table(tech, [26 * mm, W - 26 * mm], header=False, small=True)]))
    return f

def deco(c, doc):
    c.saveState()
    c.setFillColor(DARK); c.rect(0, A4[1] - 6 * mm, A4[0], 6 * mm, stroke=0, fill=1)
    c.setFillColor(ACC); c.rect(0, A4[1] - 6.8 * mm, A4[0], 0.8 * mm, stroke=0, fill=1)
    c.setFont("Pop", 7.5); c.setFillColor(GREY)
    c.drawString(18 * mm, 10 * mm, "Fog Z (NINE HANDS | DSP) · v" + VERSION)
    c.drawRightString(A4[0] - 18 * mm, 10 * mm, str(doc.page))
    c.restoreState()

# ---- Couverture « minimale » (gabarit fixe commun a toutes les notices, mesures en mm depuis le haut ; logo et bandeau depuis le bas)
PEDAL_H, PEDAL_MAXW, PEDAL_TOP = 82 * mm, 115 * mm, 84 * mm
LANG_TOP = 18 * mm; NAME_TOP, NAME_PT = 194 * mm, 30; SUB_TOP, SUB_PT = 208 * mm, 10
LOGO_W, LOGO_BOTTOM = 38 * mm, 22 * mm; BAND_H = 3 * mm
def cover_bg(c, doc):
    c.saveState(); c.setFillColor(colors.black); c.rect(0, 0, A4[0], A4[1], stroke=0, fill=1)
    c.setFillColor(ACC); c.rect(0, 0, A4[0], BAND_H, stroke=0, fill=1)
    def line(text, top, font, size, cs, col):
        w = pdfmetrics.stringWidth(text, font, size) + cs * (len(text) - 1)
        t = c.beginText((A4[0] - w) / 2, A4[1] - top - size * 0.8); t.setFont(font, size); t.setCharSpace(cs)
        t.setFillColor(col); t.textOut(text); c.drawText(t)
    line("FRANÇAIS", LANG_TOP, "PopM", 8.5, 0, ACC_L)
    ci = Image.open(cover); iw, ih = ci.size
    cw = iw / 1.32; ch = (ih - int(cw * 0.16)) / 1.2; pad = int(cw * 0.16)
    k = min(PEDAL_H / ch, PEDAL_MAXW / cw)
    dw, dh = iw * k, ih * k
    y0 = A4[1] - (PEDAL_TOP + (PEDAL_H - ch * k) / 2) + pad * k
    c.drawImage(cover, (A4[0] - dw) / 2, y0 - dh, dw, dh)
    line("FOG Z", NAME_TOP - NAME_PT * 0.02, "Title", NAME_PT, NAME_PT * 0.5, colors.white)
    line("Octaves polyphoniques", SUB_TOP, "Pop", SUB_PT, 1.5, colors.HexColor("#BDC4B8"))
    lw, lh = Image.open(LOGO_PNG).size
    c.drawImage(LOGO_PNG, (A4[0] - LOGO_W) / 2, LOGO_BOTTOM, LOGO_W, LOGO_W * lh / lw, mask="auto")
    c.restoreState()

doc = BaseDocTemplate(OUT, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm, bottomMargin=18 * mm,
                      title="FOG Z - Notice v" + VERSION, author="NINE HANDS | DSP")
doc.addPageTemplates([PageTemplate(id="cover", frames=[Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="fc")], onPage=cover_bg),
                      PageTemplate(id="p", frames=[Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="f")], onPage=deco)])
doc.build(story())
shutil.rmtree(TMP, ignore_errors=True)
print(OUT)
