# FOG Z (NINE HANDS | DSP) - notice PDF bilingue (anglais puis francais), illustree.
# Usage : python3 tools/manual.py <fichier PDF de sortie>
#
# Images sources dans tools/manual_assets/ (reprises de la notice v1.4.0, rendu reel du plugin) :
#   cover_cutout.jpg (pedale detouree + reflet), annotated.jpg (capture numerotee), dryfx_q.png (LED DRY FX / Q),
#   preset_knob.png (bouton et LED de preset), preset_strip.png (footswitchs), learn_bubble.png (bulle MIDI Learn).
# Les menus du clic droit sont redessines ici (menu_img) avec les libelles exacts de PluginEditor.cpp
# (showMainMenu / showFootswitchMenu) : a mettre a jour si le menu change.
# Pas d'historique des versions dans la notice (demande de l'utilisateur).
import os, sys, tempfile
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (BaseDocTemplate, PageTemplate, NextPageTemplate, Frame, Paragraph, Spacer, Image as RLImage,
                                Table, TableStyle, PageBreak, CondPageBreak, KeepTogether)
from reportlab.platypus.flowables import Flowable
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AS = os.path.join(ROOT, "tools", "manual_assets")
FONTS = os.path.join(AS, "fonts")
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "docs", "FogZ_Manual_EN-FR.pdf")
TMP = tempfile.mkdtemp(prefix="fogz_manual_")
VERSION = "1.5.1"     # = version du plugin dans CMakeLists.txt

for n, f in (("Pop", "Poppins-Regular"), ("PopL", "Poppins-Light"), ("PopM", "Poppins-Medium"), ("PopB", "Poppins-Bold"),
             ("PopI", "Poppins-Italic"), ("Mono", "DejaVuSansMono"), ("DjV", "DejaVuSans")):
    pdfmetrics.registerFont(TTFont(n, os.path.join(FONTS, f + ".ttf")))
pdfmetrics.registerFontFamily("Pop", normal="Pop", bold="PopB", italic="PopI", boldItalic="PopB")

ACC = colors.HexColor("#C8352E")          # rouge de la pedale (bandeau)
DARK = colors.HexColor("#1E1E22"); GREY = colors.HexColor("#6B6B70"); LIGHT = colors.HexColor("#F7EEEC")
def A(n): return os.path.join(AS, n)

# ---------- menus (style menuLnF de Fog Z) ----------
MBG, MBORD, MTXT, MDIS, MSEP, MHI, MHEAD = (35, 26, 24), (67, 58, 56), (241, 233, 220), (140, 136, 138), (79, 73, 72), (168, 50, 42), (255, 176, 74)
F_MENU = ImageFont.truetype(os.path.join(FONTS, "Poppins-Regular.ttf"), 26)
F_HEAD = ImageFont.truetype(os.path.join(FONTS, "Poppins-Bold.ttf"), 24)
ROW, SEPH, PADX, PADY = 48, 18, 50, 10
DASH = "\u2014"

def menu_img(items, width):
    """items : (texte, flags) ; flags : 'sub', 'dis', 'hi', 'chk', 'head', 'sep'."""
    h = PADY * 2 + sum(SEPH if f == "sep" else ROW for _, f in items)
    im = Image.new("RGBA", (width, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, width - 1, h - 1), 12, fill=MBG, outline=MBORD, width=2)
    y = PADY; rows = {}
    for t, f in items:
        if f == "sep":
            d.line((24, y + SEPH // 2, width - 24, y + SEPH // 2), fill=MSEP, width=2); y += SEPH; continue
        if "head" in f:
            d.text((24, y + ROW // 2 + 2), t, font=F_HEAD, fill=MHEAD, anchor="lm"); rows[t] = y; y += ROW; continue
        if "hi" in f:
            d.rectangle((6, y + 1, width - 7, y + ROW - 1), fill=MHI)
        col = MDIS if "dis" in f else MTXT
        d.text((PADX + 6, y + ROW // 2), t, font=F_MENU, fill=col, anchor="lm")
        if "sub" in f:
            d.text((width - 28, y + ROW // 2), "\u203a", font=F_MENU, fill=col, anchor="mm")
        if "chk" in f:
            c = MHEAD
            d.line((24, y + ROW // 2, 31, y + ROW // 2 + 9), fill=c, width=4); d.line((31, y + ROW // 2 + 9, 44, y + ROW // 2 - 10), fill=c, width=4)
        rows[t] = y; y += ROW
    return im, rows

def compose(menus):
    W = max(x + m.width for m, x, y in menus); H = max(y + m.height for m, x, y in menus)
    out = Image.new("RGB", (W, H), (255, 255, 255))
    for m, x, y in menus: out.paste(m, (x, y), m)
    return out

def build_menus():
    main_tail = [("Factory sounds", "sub"), ("Restore factory sounds in presets 1-8", ""), ("MIDI", "sub")]
    # 1) clic droit sur le fader DETUNE : Plugin size > Default size (new windows)
    m1, r1 = menu_img([("Detune", "head"), ("MIDI Learn: Detune (" + DASH + ")", ""), ("Clear MIDI: Detune", "dis"), ("", "sep"),
                       ("Fog Z  -  NINE HANDS | DSP", "head"), ("Plugin size", "sub hi")] + main_tail, 640)
    m2, r2 = menu_img([("60 %  (default)", "chk"), ("75 %", ""), ("100 %", ""), ("125 %", ""), ("", "sep"),
                       ("Default size (new windows)", "sub hi")], 470)
    m3, _ = menu_img([("60 %", "chk"), ("75 %", ""), ("100 %", ""), ("125 %", "")], 220)
    y2 = r1["Plugin size"] - PADY; y3 = y2 + r2["Default size (new windows)"] - PADY
    size_menu = compose([(m1, 0, 0), (m2, 648, y2), (m3, 648 + 478, y3)])
    # 2) clic droit sur le footswitch BYPASS
    f1, _ = menu_img([("Bypass footswitch", "head"), ("MIDI Learn: Bypass footswitch (" + DASH + ")", ""),
                      ("Clear MIDI: Bypass footswitch", "dis"), ("", "sep"), ("Latching MIDI pedals", ""), ("", "sep"), ("More...", "")], 680)
    foot_menu = compose([(f1, 0, 0)])
    # 3) clic droit ailleurs : MIDI
    names = ["Dry Output", "-2 Octaves", "-1 Octave", "+1 Octave", "+2 Octaves", "Attack", "LP Filter", "Detune", "Dry FX",
             "Filter Q", "Preset knob", "Preset footswitch", "Bypass footswitch"]
    g1, q1 = menu_img([("Fog Z  -  NINE HANDS | DSP", "head"), ("Plugin size", "sub")] + main_tail[:2] + [("MIDI", "sub hi")], 640)
    g2, _ = menu_img([("Learn: " + n + " (" + DASH + ")", "") for n in names] +
                     [("", "sep"), ("Clear all MIDI assignments", ""), ("Latching MIDI pedals (127 / 0 on each press)", ""), ("", "sep"),
                      ("Program Change 1-8 loads presets 1-8", "dis")], 760)
    map_menu = compose([(g1, 0, 0), (g2, 648, 0)])
    p = {}
    for n, im in (("menu_size", size_menu), ("menu_foot", foot_menu), ("menu_map", map_menu)):
        p[n] = os.path.join(TMP, "fogz_" + n + ".png"); im.save(p[n])
    return p

MENUS = build_menus()

def img(path, width):
    im = Image.open(path); h = width * im.height / im.width
    return RLImage(path, width=width, height=h)

st = {
    "h1": ParagraphStyle("h1", fontName="PopB", fontSize=18, leading=23, textColor=ACC, spaceAfter=6, spaceBefore=10, keepWithNext=1),
    "h2": ParagraphStyle("h2", fontName="Pop", fontSize=12, leading=16, textColor=DARK, spaceAfter=3, spaceBefore=8, keepWithNext=1),
    "h3": ParagraphStyle("h3", fontName="PopM", fontSize=10, leading=13, textColor=DARK, spaceAfter=1, spaceBefore=6, keepWithNext=1),
    "p": ParagraphStyle("p", fontName="Pop", fontSize=9, leading=13.2, textColor=DARK, spaceAfter=4),
    "b": ParagraphStyle("b", fontName="Pop", fontSize=9, leading=13.2, textColor=DARK, spaceAfter=2.5, leftIndent=10, bulletIndent=1),
    "small": ParagraphStyle("small", fontName="Pop", fontSize=7.6, leading=10.5, textColor=GREY, alignment=TA_CENTER, spaceBefore=2, spaceAfter=6),
    "note": ParagraphStyle("note", fontName="Pop", fontSize=8.2, leading=11.5, textColor=GREY, spaceAfter=4),
    "cell": ParagraphStyle("cell", fontName="Pop", fontSize=8.2, leading=11, textColor=DARK),
    "cellb": ParagraphStyle("cellb", fontName="PopM", fontSize=8.2, leading=11, textColor=DARK),
    "cover": ParagraphStyle("cover", fontName="PopL", fontSize=40, leading=48, textColor=colors.white, alignment=TA_CENTER),
    "coversub": ParagraphStyle("coversub", fontName="Pop", fontSize=11, leading=16, textColor=colors.HexColor("#BDBDBD"), alignment=TA_CENTER),
    "coverlang": ParagraphStyle("coverlang", fontName="PopM", fontSize=8, leading=11, textColor=ACC),
}
def fix(t): return t.replace("&rarr;", "<font name='DjV'>&rarr;</font>")
def P(t, s="p"): return Paragraph(fix(t), st[s])
def bullets(items): return [Paragraph(i, st["b"], bulletText="\u2022") for i in items]
def table(rows, widths, header=True, size=None):
    cs = st["cell"] if size is None else ParagraphStyle("c2", parent=st["cell"], fontSize=size, leading=size + 2.6)
    cb = st["cellb"] if size is None else ParagraphStyle("c3", parent=st["cellb"], fontSize=size, leading=size + 2.6)
    data = [[Paragraph(fix(c), cb if (header and r == 0) else cs) for c in row] for r, row in enumerate(rows)]
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    style = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("LINEBELOW", (0, 0), (-1, -1), 0.3, colors.HexColor("#DCD6D0")),
             ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3), ("LEFTPADDING", (0, 0), (-1, -1), 4)]
    if header: style += [("BACKGROUND", (0, 0), (-1, 0), LIGHT), ("LINEBELOW", (0, 0), (-1, 0), 0.8, ACC)]
    t.setStyle(TableStyle(style)); return t
def mono(s): return "<font name='Mono' size='8.2'>" + s + "</font>"

# ---------- sons d'usine (identiques a PluginProcessor.cpp) : faders en %, DRY FX, Q ----------
FAC = [("Organ Pad", 60, 26, 70, 62, 30, 45, 62, 35, 3, 1), ("Baritone Growl", 35, 30, 85, 0, 0, 0, 55, 0, 0, 3),
       ("Theremin-ish", 0, 0, 0, 92, 0, 56, 50, 88, 0, 2), ("Cello", 0, 0, 86, 10, 0, 50, 40, 12, 1, 2),
       ("Lower + Upper Clean", 80, 0, 62, 58, 0, 0, 100, 0, 0, 1), ("Organ Drawbars", 70, 56, 70, 66, 52, 0, 80, 28, 2, 1),
       ("Glass Choir", 56, 0, 40, 68, 82, 60, 74, 40, 1, 2), ("Sub Synth Bass", 20, 66, 85, 0, 0, 8, 30, 0, 2, 4),
       ("12-String Shimmer", 80, 0, 0, 62, 0, 0, 100, 22, 0, 1), ("Reverse Swell", 62, 0, 92, 84, 30, 80, 78, 18, 1, 1),
       ("Leslie Rotary", 62, 0, 66, 66, 48, 0, 70, 85, 3, 1), ("Fog Horn", 0, 80, 55, 25, 0, 30, 25, 15, 2, 4)]
DFX = {"en": ["OFF", "RED", "GREEN", "AMBER"], "fr": ["ÉTEINTE", "ROUGE", "VERTE", "AMBRE"]}

T = {
"en": dict(
 lang="ENGLISH", sub="Polyphonic Octave Generator &middot; VST3 &middot; Windows &amp; macOS", ver="User manual &middot; version " + VERSION,
 foot="Fog Z (NINE HANDS | DSP) &middot; User manual &middot; v" + VERSION,
 pres_t="1. Presentation",
 pres=["<b>Fog Z</b> is a VST3 effect by NINE HANDS | DSP that recreates the <b>Electro-Harmonix POG2</b> (Polyphonic Octave Generator). From a single guitar it builds two octaves below and two octaves above every string of a chord, mixes them freely with your dry signal and lets you sculpt them with a swell, a resonant low-pass filter and a detune / rotary effect. Organs, cellos, 12-strings, synth basses, theremins&hellip; one fader movement away."],
 feat_t="Main features",
 feat=["<b>4 polyphonic voices</b>: -2, -1, +1 and +2 octaves, each with its own fader; chords track cleanly.",
       "<b>3 shaping effects</b>: Attack (note-by-note swell), LP Filter (2-pole, 4 resonances), Detune (chorus to rotary vibrato).",
       "<b>DRY FX routing</b>: four modes send the dry signal through the effects too, shown by a 3-colour LED.",
       "<b>8 preset memories</b> on the pedal and <b>12 factory sounds</b> in the host preset menu.",
       "<b>MIDI Learn on every control</b> (right-click on the control); no CC is assigned by default; Program Change 1-8.",
       "Mono or stereo in / out. Plugin size 60 %, 75 %, 100 % or 125 %, with a default size of your choice for new windows; never smaller than 60 %."],
 sig_h="Signal path",
 sig="The input is summed to mono and analysed by the octave engine. The four octave voices are mixed with their faders; the upper voices go through Detune. Everything goes through the LP Filter, and the dry signal joins it depending on the DRY FX mode. A soft limiter protects the output and the BYPASS footswitch crossfades in 15 ms.",
 inst_t="2. Installation",
 inst=[("Windows 11", "Copy <b>Fog Z.vst3</b> into " + mono("C:\\Program Files\\Common Files\\VST3\\") + "."),
       ("macOS", "Copy <b>Fog Z.vst3</b> into " + mono("~/Library/Audio/Plug-Ins/VST3/") + ", then once, in Terminal: " + mono("xattr -cr ~/Library/Audio/Plug-Ins/VST3/\"Fog Z.vst3\"") + " (removes the download quarantine). Universal binary: Apple Silicon and Intel."),
       ("Reaper", "Options &gt; Preferences &gt; Plug-ins &gt; VST &gt; <b>Re-scan</b>. Fog Z appears as <b>Fog Z (NINE HANDS | DSP)</b>."),
       ("Build from GitHub", "Push all files to the root of the repository: the <i>Actions</i> tab produces <b>FogZ-VST3-Windows</b> and <b>FogZ-VST3-macOS</b>.")],
 ov_t="3. Interface overview",
 ov_i="All the controls of the real pedal are here, at the same place. Faders slide, buttons sink, the big knob clicks from preset to preset and the LEDs light up. Hover or move a fader to read its exact value.",
 ov1=[["#", "Element", "Role"], ["1", "Dry Output", "Level of your clean signal."], ["2", "-2 Octaves", "Two octaves down."],
      ["3", "-1 Octave", "One octave down."], ["4", "+1 Octave", "One octave up."], ["5", "+2 Octaves", "Two octaves up."],
      ["6", "DRY FX LED", "Off / red / green / amber."], ["7", "DRY FX button", "Sends the dry signal through the effects."],
      ["8", "Q LED", "Brightness = filter resonance."], ["9", "Q button", "4 resonance levels."]],
 ov2=[["#", "Element", "Role"], ["10", "Attack", "Swell time of each note."], ["11", "LP Filter", "Low-pass cutoff."],
      ["12", "Detune", "Chorus / rotary on the upper voices."], ["13", "Preset knob", "8 notches: turn = load the preset, hold 3 s = save."],
      ["14", "Preset LEDs 1-8", "Selected memory."], ["15", "PRESET LED", "On = loaded, fast blink = edited."],
      ["16", "PRESET footswitch", "Load / next preset."], ["17", "BYPASS LED", "On = effect active."], ["18", "BYPASS footswitch", "Effect on / off."]],
 ov_note="Double-click a fader to go back to its default value. Right-click a control for its MIDI Learn; right-click anywhere opens the menu (Plugin size, factory sounds, MIDI).",
 ctl_t="4. Controls in detail",
 mix_h="Voice mix",
 mix="Every fader goes from silence (bottom) to +3.9 dB (top); the 80 % mark is unity gain, exactly like the original pedal where the dry fader at the top gives back your level.",
 voices=["<b>DRY OUTPUT</b> &mdash; Your clean, untouched guitar. Lower it to hear only the octaves (cello, synth, theremin sounds). With DRY FX on, the dry signal also goes through Attack / LP / Detune.",
         "<b>-2 OCTAVES</b> &mdash; Two octaves down (&frac14; of the frequency): deep sub, 16' organ foot or synth bass. Very powerful, use it gently with chords.",
         "<b>-1 OCTAVE</b> &mdash; One octave down (&frac12; of the frequency): bass guitar, baritone, cello. The most natural of the voices.",
         "<b>+1 OCTAVE</b> &mdash; One octave up (&times;2): 12-string, mandolin, glassy organ. The base of theremin and choir sounds.",
         "<b>+2 OCTAVES</b> &mdash; Two octaves up (&times;4): bells, whistle, harmonics. Goes through Detune together with +1."],
 lvl=[["Position", "0 %", "25 %", "50 %", "64 %", "80 %", "100 %"], ["Level", "off", "-20.2 dB", "-8.2 dB", "-3.9 dB", "0.0 dB", "+3.9 dB"]],
 ch_h="Playing chords",
 ch="The engine splits your guitar into about 190 narrow bands and only lets the strongest band of each partial speak, so every string of a chord gets its own octave. Open chords and power chords track very well. Close intervals in the low register (a minor second on the low strings) can beat slightly, like on the hardware: lower -2 or play the low part as a single note.",
 att_h="ATTACK",
 att="Fade-in time of the octave voices, note by note: every new note swells in on its own, even inside a chord. The curve starts slowly and finishes firmly, and the note is held up while it swells (up to +9.5 dB) so the swell really ends loud: the famous reverse / violin effect. At the bottom, Attack is off.",
 att_t=[["Position", "0 %", "2 %", "25 %", "50 %", "75 %", "100 %"], ["Attack", "OFF", "10 ms", "38 ms", "163 ms", "700 ms", "3.00 s"]],
 lp_h="LP FILTER",
 lp="Cutoff of the 2-pole resonant low-pass filter. All octave voices go through it (and the dry signal in DRY FX green or amber). Low settings give round organ and cello tones, high settings leave everything open.",
 lp_t=[["Position", "0 %", "25 %", "50 %", "75 %", "100 %"], ["Cutoff", "50 Hz", "218 Hz", "949 Hz", "4.1 kHz", "18.0 kHz"]],
 det_h="DETUNE",
 det="Acts on the +1 and +2 voices only (and the dry signal in DRY FX amber). Speed and depth rise together: slow chorus for 12-string sounds at the bottom, fast chorus then real pitch vibrato (rotary speaker, theremin) at the top.",
 det_t=[["Position", "Rate", "Depth", "Vibrato", "Pitch swing"], ["0 %", "&mdash;", "&mdash;", "&mdash;", "&mdash;"],
        ["25 %", "0.56 Hz", "1.03 ms", "0 %", "&plusmn;0.03 st"], ["50 %", "1.77 Hz", "1.41 ms", "0 %", "&plusmn;0.14 st"],
        ["75 %", "3.81 Hz", "1.55 ms", "49 %", "&plusmn;0.32 st"], ["88 %", "5.18 Hz", "1.53 ms", "80 %", "&plusmn;0.43 st"],
        ["100 %", "6.65 Hz", "1.45 ms", "85 %", "&plusmn;0.52 st"]],
 dfx_h="DRY FX button and LED",
 dfx="Each press cycles through four routings of the dry signal; a message bubble names the new mode. The LED above the button shows it:",
 dfx_t=[["LED", "Routing"], ["OFF", "Dry signal clean, the effects only act on the octaves"], ["RED", "Dry &rarr; Attack"],
        ["GREEN", "Dry &rarr; Attack + LP Filter"], ["AMBER", "Dry &rarr; Attack + LP Filter + Detune"]],
 dfx_cap="DRY FX LED off, red, green, amber (top), Q LED brightness (bottom).",
 q_h="Q button and LED",
 q="Four resonance levels for the LP Filter. The LED gets brighter with the resonance: off = flat (Q 0.7), then 1.5, 3.2 and 7.5 for a vocal, wah-like peak. The level is automatically compensated so high Q doesn't jump out.",
 pk_t="5. Preset knob, LEDs and footswitches",
 pk_i="Fog Z has eight preset memories, like the pedal. Each one stores the eight faders and the DRY FX and Q modes (not the bypass).",
 pk_g=[["Gesture", "Effect"], ["Turn", "Drag up / right, or use the mouse wheel. The knob is a rotary switch: it jumps from notch to notch and loads that preset at once. Stops at 1 and 8."],
       ["Click", "Reloads the current preset (handy after editing it)."],
       ["Hold 3 s", "Saves the current sound into the selected memory. After 2 s all preset LEDs blink, at 3 s the sound is stored."]],
 pk_l=[["Preset LEDs 1-8", "The lit LED shows the selected memory. They all blink while saving."],
       ["PRESET LED (red)", "On: the selected preset is loaded. Fast blink: a fader or a button has changed since (the preset is edited)."],
       ["PRESET footswitch", "Loads the selected preset. If it is already loaded, goes to the next one (8 &rarr; 1). If it was edited, reloads it."],
       ["BYPASS footswitch", "Effect on / off with a 15 ms crossfade, no click. The BYPASS LED is on when the effect is active."]],
 midi_t="6. MIDI",
 midi_i="Fog Z receives MIDI on its track, on any channel (in Reaper: arm the track and pick your MIDI input, with monitoring on, or route a MIDI item to it).",
 learn_h="MIDI Learn",
 learn=["<b>No CC is assigned by default</b>: every control you want to drive from your controller, footswitches included, is assigned with MIDI Learn.",
        "<b>Right-click a control</b> (any fader, DRY FX, Q, the preset knob or a footswitch): the menu starts with the control's name and <b>MIDI Learn: &lt;control&gt; (CC n)</b>, or a dash (&mdash;) when the control is not assigned. Choose it, then move an expression pedal or press a MIDI button: the first CC received is assigned. For a footswitch, the press (value 64 or more) is what gets learnt. The learning message itself does not change the sound.",
        "While waiting, the message bubble shows <b>MIDI LEARN: move a control for &lt;control&gt;</b>, then <b>&lt;control&gt; = CC n</b> for 2 seconds.",
        "<b>Clear MIDI: &lt;control&gt;</b> removes the assignment; <b>Cancel MIDI learn</b> (or choosing the same MIDI Learn again) stops waiting.",
        "A CC number drives only one control: learning a CC already used elsewhere removes it from the other control.",
        "Right-click anywhere else &gt; <b>MIDI</b>: <b>Learn: &lt;control&gt; (CC n)</b> for all 13 controls, <b>Cancel MIDI learn</b> (while waiting), <b>Clear all MIDI assignments</b> and <b>Latching MIDI pedals</b>.",
        "Assignments are <b>saved with your project</b>. A project saved with an earlier version whose MIDI table was never changed (footswitches still on the former factory CCs, nothing else learnt) opens with no assignment; a project in which you had changed or added an assignment keeps all its assignments."],
 mtab=[["Control", "Type"], ["Dry Output, -2 Octaves, -1 Octave, +1 Octave, +2 Octaves", "Continuous: 0-127 = 0-100 % (smoothed)"],
       ["Attack, LP Filter, Detune", "Continuous: 0-127 = 0-100 % (smoothed)"],
       ["Dry FX", "Selector, 4 positions (0-31 off, 32-63 red, 64-95 green, 96-127 amber)"],
       ["Filter Q", "Selector, 4 positions (0-31, 32-63, 64-95, 96-127)"],
       ["Preset knob", "Selector, 8 notches (16 values each): loads preset 1-8 when the notch changes"],
       ["Preset footswitch", "Footswitch, momentary (each press); latching option"],
       ["Bypass footswitch", "Footswitch, momentary (each press toggles); latching option"],
       ["Presets 1-8", "Program Change 1-8: loads pedal memories 1 to 8 (fixed, no learning needed)"]],
 latch="<b>Latching MIDI pedals</b> (right-click on a footswitch or MIDI menu): for controllers whose buttons send 127 / 0 on alternate presses. Off (default): a footswitch acts when the value goes to 64 or more (momentary button). On: every change of state counts as a press.",
 menus_cap="Left: right-click on the DETUNE fader (not assigned yet), with Plugin size &gt; Default size (new windows) open. Right: right-click on the BYPASS footswitch (More... opens the full menu).",
 map_cap="Right-click elsewhere: MIDI menu with all 13 learnable controls and Clear all MIDI assignments.",
 bub_cap="Message bubble during MIDI Learn: waiting, then confirmation.",
 auto_h="Automatable parameters",
 auto=[["Parameter", "Range"], ["Dry Output, -2, -1, +1, +2", "0 &ndash; 100 %"], ["Attack", "Off, 10 ms &ndash; 3 s"], ["LP Filter", "50 Hz &ndash; 18 kHz"],
       ["Detune", "0 &ndash; 100 %"], ["Dry FX", "4 modes"], ["Filter Q", "4 levels"], ["Bypass", "on / off"]],
 win_t="7. Window",
 win=["A new Fog Z window opens at the default size, 60 % at first, and can never be made smaller than 60 %. Right-click &gt; <b>Plugin size</b>: <b>60 %</b>, <b>75 %</b>, <b>100 %</b> or <b>125 %</b> for this window, with <b>(default)</b> next to the default size; or drag the bottom-right corner (proportions kept, up to 125 %).",
      "<b>Plugin size &gt; Default size (new windows)</b> chooses the size at which every new Fog Z window opens: the setting is shared by all instances and saved on your computer. The open window takes that size at once and follows the default size again.",
      "<b>Size saved with the project</b>: a size you choose for an instance (in Plugin size or by dragging the corner) is saved with the project and takes priority over the default size when the project is reopened. Choosing Default size (new windows) puts that instance back on the default size.",
      "There is no permanent status line: a message bubble shows the value of the fader you move or hover, the new DRY FX / Q mode, and the MIDI Learn messages.",
      "Also saved with your project: faders, the 8 memories, the selected preset, MIDI assignments and the latching option."],
 gest_h="Gesture cheat sheet",
 gest=[["Gesture", "Effect"], ["Drag a fader", "Change the value"], ["Double-click a fader", "Default value"], ["Hover a fader", "Show its value"],
       ["Click DRY FX / Q", "Next mode"], ["Drag / wheel on the knob", "Change preset (loaded at once)"], ["Click the knob", "Reload the preset"],
       ["Hold the knob 3 s", "Save"], ["Right-click a control", "MIDI Learn / Clear MIDI for that control, then the menu"],
       ["Right-click elsewhere", "Menu: Plugin size, factory sounds, MIDI"]],
 pre_t="8. Presets",
 pre_i="Fog Z ships with twelve sounds. They are listed in the preset drop-down of the plug-in window (top-left in Reaper) and in right-click &gt; <b>Factory sounds</b>: choosing one loads it on the faders without changing the 8 memories. Sounds 1 to 8 are also stored in the eight memories of the pedal; right-click &gt; <b>Restore factory sounds in presets 1-8</b> puts them back.",
 pre_tab="Table: fader positions in %, DRY FX colour and Q level (1 to 4).",
 pre_hdr=["#", "Name", "Dry", "-2", "-1", "+1", "+2", "Att", "LP", "Det", "Dry FX", "Q"],
 mem="Pedal memory", host="Host menu only",
 pdesc=["A warm organ pad: every voice, a soft swell, dry signal through the whole effect chain with a slow rotary chorus.",
        "Dry and lower octaves through a darker filter: a baritone guitar with a growl.",
        "Only the upper octave, a round low-pass and a fast vibrato with a slow fade-in: a theremin-like sine voice. Play slow melodies on the high strings.",
        "The lower octave alone, a slow bow-like attack and a dark filter: play single lines in the middle of the neck.",
        "The classic: your guitar with one octave below and one above, no effect. Thick, clean and natural.",
        "All voices up, like an organ with every drawbar pulled out. Dry through Attack + LP.",
        "Upper voices with a swell and a light chorus: an airy choir / glass harmonica. Great with arpeggios.",
        "Huge sub octaves, a resonant filter (Q 4) and a short swell: a synth bass from your guitar's low strings.",
        "Your guitar plus the upper octave with a gentle chorus: a shimmering 12-string.",
        "Long, strong swell on the octaves and the dry: the note comes from nowhere and ends loud. Play a chord and let it bloom.",
        "Organ voicing with the Detune near the top: fast rotary speaker on the upper voices and the dry signal.",
        "Sub octaves only, a resonant low filter and a slow attack: a foghorn-like drone."],
 tips_t="9. Tips",
 tips=["<b>Reaper chain</b>: guitar track &gt; tuner &gt; <b>Fog Z</b> &gt; drive / fuzz &gt; amp sim &gt; delay / reverb. Octave generators track best on a clean, unprocessed guitar: put Fog Z first, before any distortion.",
       "<b>Low-tuned 7-string</b>: -2 on a low B or A goes below the useful range; keep -2 low or off and use -1 for weight, or add +1 for a 12-string sheen on riffs. Sub Synth Bass and Fog Horn work on single low notes rather than chords.",
       "<b>Octave fuzz</b>: put a fuzz after Fog Z and raise +1: the classic octave-up fuzz, but polyphonic.",
       "<b>Hammond-ish</b>: Dry 70 % &middot; -1 70 % &middot; +1 65 % &middot; +2 45 % &middot; Detune 85 % &middot; DRY FX amber.",
       "<b>Violin section</b>: Dry 0 &middot; -1 50 % &middot; +1 70 % &middot; Attack 70 % &middot; Detune 40 %.",
       "<b>Wah filter</b>: LP at 55 % with Q 4, then put the LP Filter on an expression pedal with MIDI Learn.",
       "<b>Live with a Chocolate Plus</b>: learn BYPASS and PRESET on two buttons, Attack or Detune on an expression pedal."],
 trb_h="Troubleshooting",
 trb=[["Problem", "Solution"], ["No octave, only dry", "Raise the octave faders; check that the BYPASS LED is on."],
      ["Too much low end", "Lower -2, or close the LP Filter a little. Fog Z already cuts below 16 Hz."],
      ["Beeps when not playing", "The idle gate keeps octaves silent until 12 dB above the background noise. If a very loud hum remains, lower it at the source."],
      ["Octaves warble on chords", "Normal for very close low intervals; lower -2, play the low part as single notes, or put Fog Z before distortion."],
      ["Notes don't swell", "Attack is at the bottom (OFF). Raise it; for the dry too, set DRY FX red / green / amber."],
      ["PRESET LED blinks", "The loaded preset was edited. Click the knob or press PRESET to reload it, or hold the knob 3 s to save."],
      ["A footswitch fires twice / every other press", "Toggle Latching MIDI pedals to match your controller."],
      ["MIDI does nothing", "Check that the track receives MIDI, then right-click the control &gt; MIDI Learn (no CC is assigned by default)."],
      ["The window is too small", "Right-click &gt; Plugin size &gt; 75 %, 100 % or 125 %, or drag the corner. For every new window: Plugin size &gt; Default size (new windows)."],
      ["macOS: plug-in not found", "Run the xattr command of the installation section, then rescan."]],
 spec_t="10. Specifications",
 spec=[["Format", "VST3, 64-bit &middot; Windows 10/11 &middot; macOS 10.13+ universal (Apple Silicon + Intel)"],
       ["Channels", "Mono or stereo input, mono or stereo output"], ["Sample rates", "44.1 to 192 kHz (lower internal rate above 88 kHz)"],
       ["Latency", "0 sample reported &middot; dry untouched &middot; octave voices &asymp; 1.3 ms internal delay"],
       ["Octave engine", "&asymp; 190 complex band-pass filters (3-stage), about 3 bands per semitone above 360 Hz; per-band noise gate, stop follower, idle gate"],
       ["Voices", "Dry, -2, -1, +1, +2 octaves, each 0 &hellip; +3.9 dB (0 dB at the 80 % mark)"],
       ["Effects", "Attack 10 ms &hellip; 3 s &middot; LP 50 Hz &hellip; 18 kHz, 4 Q &middot; Detune 0.15 &hellip; 6.6 Hz"],
       ["Presets", "8 memories on the pedal &middot; 12 factory sounds &middot; saved with the project"],
       ["MIDI", "MIDI Learn on 13 controls (no CC assigned by default), latching option, Program Change 1-8, any channel"],
       ["Window", "Plugin size 60 % (minimum), 75 %, 100 %, 125 %; default size for new windows selectable; size chosen for an instance saved with the project; resizable by the corner"],
       ["Stability", "Windows anti-freeze v2: the interface never blocks the host"], ["Name in the DAW", "Fog Z (NINE HANDS | DSP) &middot; version " + VERSION]],
 legal="Inspired by the Electro-Harmonix POG2. Electro-Harmonix and POG are trademarks of their owners; Fog Z is an independent tribute by NINE HANDS | DSP and is not affiliated with them. Built with JUCE."),
"fr": dict(
 lang="FRANÇAIS", sub="Générateur d'octaves polyphonique &middot; VST3 &middot; Windows &amp; macOS", ver="Notice d'utilisation &middot; version " + VERSION,
 foot="Fog Z (NINE HANDS | DSP) &middot; Notice d'utilisation &middot; v" + VERSION,
 pres_t="1. Présentation",
 pres=["<b>Fog Z</b> est un effet VST3 NINE HANDS | DSP qui reproduit l'<b>Electro-Harmonix POG2</b> (Polyphonic Octave Generator). À partir d'une seule guitare, il crée deux octaves en dessous et deux octaves au-dessus de chaque corde d'un accord, les mélange librement avec ton son direct et te laisse les sculpter avec une montée de volume, un filtre passe-bas résonant et un detune / effet rotatif. Orgues, violoncelles, 12 cordes, basses synthé, thérémines&hellip; à un mouvement de fader."],
 feat_t="Points forts",
 feat=["<b>4 voix polyphoniques</b> : -2, -1, +1 et +2 octaves, chacune avec son fader ; les accords sont suivis proprement.",
       "<b>3 effets</b> : Attack (montée note par note), LP Filter (2 pôles, 4 résonances), Detune (du chorus au vibrato rotatif).",
       "<b>Routage DRY FX</b> : quatre modes envoient aussi le son direct dans les effets, indiqués par une LED 3 couleurs.",
       "<b>8 mémoires</b> sur la pédale et <b>12 sons d'usine</b> dans le menu de presets de l'hôte.",
       "<b>MIDI Learn sur toutes les commandes</b> (clic droit sur la commande) ; aucun CC assigné d'office ; Program Change 1-8.",
       "Entrée / sortie mono ou stéréo. Taille du plugin 60 %, 75 %, 100 % ou 125 %, avec une taille d'ouverture au choix pour les nouvelles fenêtres ; jamais plus petite que 60 %."],
 sig_h="Chemin du signal",
 sig="L'entrée est sommée en mono puis analysée par le moteur d'octaves. Les quatre voix sont dosées par leurs faders ; les voix aiguës passent par le Detune. Le tout traverse le LP Filter, que le son direct rejoint selon le mode DRY FX. Un limiteur doux protège la sortie et le footswitch BYPASS fait un fondu de 15 ms.",
 inst_t="2. Installation",
 inst=[("Windows 11", "Copie <b>Fog Z.vst3</b> dans " + mono("C:\\Program Files\\Common Files\\VST3\\") + "."),
       ("macOS", "Copie <b>Fog Z.vst3</b> dans " + mono("~/Library/Audio/Plug-Ins/VST3/") + ", puis une seule fois, dans le Terminal : " + mono("xattr -cr ~/Library/Audio/Plug-Ins/VST3/\"Fog Z.vst3\"") + " (retire la quarantaine du téléchargement). Binaire universel : Apple Silicon et Intel."),
       ("Reaper", "Options &gt; Preferences &gt; Plug-ins &gt; VST &gt; <b>Re-scan</b>. Fog Z apparaît sous le nom <b>Fog Z (NINE HANDS | DSP)</b>."),
       ("Compilation GitHub", "Pousse tous les fichiers à la racine du dépôt : l'onglet <i>Actions</i> produit <b>FogZ-VST3-Windows</b> et <b>FogZ-VST3-macOS</b>.")],
 ov_t="3. Vue d'ensemble de l'interface",
 ov_i="Toutes les commandes de la vraie pédale sont là, au même endroit. Les faders glissent, les boutons s'enfoncent, le gros bouton passe d'un cran à l'autre et les LED s'allument. Survole ou bouge un fader pour lire sa valeur exacte.",
 ov1=[["#", "Élément", "Rôle"], ["1", "Dry Output", "Niveau du son direct."], ["2", "-2 Octaves", "Deux octaves plus bas."],
      ["3", "-1 Octave", "Une octave plus bas."], ["4", "+1 Octave", "Une octave plus haut."], ["5", "+2 Octaves", "Deux octaves plus haut."],
      ["6", "LED DRY FX", "Éteinte / rouge / verte / ambre."], ["7", "Bouton DRY FX", "Envoie le son direct dans les effets."],
      ["8", "LED Q", "Luminosité = résonance du filtre."], ["9", "Bouton Q", "4 niveaux de résonance."]],
 ov2=[["#", "Élément", "Rôle"], ["10", "Attack", "Temps de montée de chaque note."], ["11", "LP Filter", "Coupure du passe-bas."],
      ["12", "Detune", "Chorus / rotatif sur les voix aiguës."], ["13", "Bouton de preset", "8 crans : tourner = charger le preset, maintenir 3 s = sauvegarder."],
      ["14", "LED de preset 1-8", "Mémoire sélectionnée."], ["15", "LED PRESET", "Fixe = chargé, clignote vite = modifié."],
      ["16", "Footswitch PRESET", "Charger / preset suivant."], ["17", "LED BYPASS", "Allumée = effet actif."], ["18", "Footswitch BYPASS", "Effet / bypass."]],
 ov_note="Double-clic sur un fader : retour à la valeur par défaut. Clic droit sur une commande : son MIDI Learn ; clic droit ailleurs : le menu (Plugin size, sons d'usine, MIDI).",
 ctl_t="4. Les commandes en détail",
 mix_h="Mélange des voix",
 mix="Chaque fader va du silence (en bas) à +3,9 dB (en haut) ; le repère 80 % correspond au gain unité, comme sur la pédale d'origine où le fader direct en haut rend ton niveau.",
 voices=["<b>DRY OUTPUT</b> &mdash; Ta guitare, propre et intacte. Baisse-le pour n'entendre que les octaves (violoncelle, synthé, thérémine). Avec DRY FX actif, le son direct passe aussi par Attack / LP / Detune.",
         "<b>-2 OCTAVES</b> &mdash; Deux octaves plus bas (&frac14; de la fréquence) : sub profond, pied de 16' d'orgue ou basse synthé. Très puissant, à doser avec les accords.",
         "<b>-1 OCTAVE</b> &mdash; Une octave plus bas (&frac12; de la fréquence) : basse, baryton, violoncelle. La plus naturelle des voix.",
         "<b>+1 OCTAVE</b> &mdash; Une octave plus haut (&times;2) : 12 cordes, mandoline, orgue cristallin. La base des sons de thérémine et de chœur.",
         "<b>+2 OCTAVES</b> &mdash; Deux octaves plus haut (&times;4) : cloches, sifflet, harmoniques. Passe dans le Detune avec +1."],
 lvl=[["Position", "0 %", "25 %", "50 %", "64 %", "80 %", "100 %"], ["Niveau", "coupé", "-20,2 dB", "-8,2 dB", "-3,9 dB", "0,0 dB", "+3,9 dB"]],
 ch_h="Jouer des accords",
 ch="Le moteur découpe ta guitare en environ 190 bandes étroites et ne laisse parler que la bande la plus forte de chaque partiel : chaque corde d'un accord obtient sa propre octave. Les accords ouverts et les power chords sont très bien suivis. Les intervalles serrés dans le grave (seconde mineure sur les cordes graves) peuvent battre légèrement, comme sur la pédale : baisse -2 ou joue la partie grave en note seule.",
 att_h="ATTACK",
 att="Temps de montée des voix d'octave, note par note : chaque nouvelle note monte seule, même dans un accord. La courbe démarre lentement et finit franchement, et la note est soutenue pendant la montée (jusqu'à +9,5 dB) pour finir fort : le fameux effet reverse / violon. En bas, Attack est coupé.",
 att_t=[["Position", "0 %", "2 %", "25 %", "50 %", "75 %", "100 %"], ["Attack", "COUPÉ", "10 ms", "38 ms", "163 ms", "700 ms", "3,00 s"]],
 lp_h="LP FILTER",
 lp="Fréquence de coupure du filtre passe-bas résonant 2 pôles. Toutes les voix d'octave le traversent (et le son direct en DRY FX vert ou ambre). Réglages bas : sons ronds d'orgue et de violoncelle ; réglages hauts : tout reste ouvert.",
 lp_t=[["Position", "0 %", "25 %", "50 %", "75 %", "100 %"], ["Coupure", "50 Hz", "218 Hz", "949 Hz", "4,1 kHz", "18,0 kHz"]],
 det_h="DETUNE",
 det="Agit seulement sur les voix +1 et +2 (et le son direct en DRY FX ambre). Vitesse et profondeur montent ensemble : chorus lent pour les sons de 12 cordes en bas, chorus rapide puis vrai vibrato de hauteur (cabine rotative, thérémine) en haut.",
 det_t=[["Position", "Vitesse", "Profondeur", "Vibrato", "Écart de hauteur"], ["0 %", "&mdash;", "&mdash;", "&mdash;", "&mdash;"],
        ["25 %", "0,56 Hz", "1,03 ms", "0 %", "&plusmn;0,03 dt"], ["50 %", "1,77 Hz", "1,41 ms", "0 %", "&plusmn;0,14 dt"],
        ["75 %", "3,81 Hz", "1,55 ms", "49 %", "&plusmn;0,32 dt"], ["88 %", "5,18 Hz", "1,53 ms", "80 %", "&plusmn;0,43 dt"],
        ["100 %", "6,65 Hz", "1,45 ms", "85 %", "&plusmn;0,52 dt"]],
 dfx_h="Bouton et LED DRY FX",
 dfx="Chaque appui passe au routage suivant du son direct ; une bulle de message nomme le nouveau mode. La LED au-dessus du bouton l'indique :",
 dfx_t=[["LED", "Routage"], ["ÉTEINTE", "Son direct propre, les effets n'agissent que sur les octaves"], ["ROUGE", "Direct &rarr; Attack"],
        ["VERTE", "Direct &rarr; Attack + LP Filter"], ["AMBRE", "Direct &rarr; Attack + LP Filter + Detune"]],
 dfx_cap="LED DRY FX éteinte, rouge, verte, ambre (en haut), luminosité de la LED Q (en bas).",
 q_h="Bouton et LED Q",
 q="Quatre niveaux de résonance pour le LP Filter. La LED brille de plus en plus avec la résonance : éteinte = plat (Q 0,7), puis 1,5, 3,2 et 7,5 pour un pic vocal façon wah. Le niveau est compensé automatiquement pour qu'un Q élevé ne ressorte pas trop.",
 pk_t="5. Bouton de preset, LED et footswitchs",
 pk_i="Fog Z a huit mémoires de presets, comme la pédale. Chacune garde les huit faders et les modes DRY FX et Q (pas le bypass).",
 pk_g=[["Geste", "Effet"], ["Tourner", "Glisser vers le haut / la droite, ou molette. Le bouton est un sélecteur à crans : il passe d'un cran à l'autre et charge aussitôt le preset. Butées en 1 et 8."],
       ["Clic", "Recharge le preset en cours (pratique après l'avoir modifié)."],
       ["Maintenir 3 s", "Sauvegarde le son actuel dans la mémoire sélectionnée. Après 2 s toutes les LED de preset clignotent, à 3 s le son est enregistré."]],
 pk_l=[["LED de preset 1-8", "La LED allumée indique la mémoire sélectionnée. Elles clignotent toutes pendant la sauvegarde."],
       ["LED PRESET (rouge)", "Fixe : le preset sélectionné est chargé. Clignotement rapide : un fader ou un bouton a changé depuis (preset modifié)."],
       ["Footswitch PRESET", "Charge le preset sélectionné. S'il est déjà chargé, passe au suivant (8 &rarr; 1). S'il a été modifié, le recharge."],
       ["Footswitch BYPASS", "Effet / bypass avec un fondu de 15 ms, sans clic. La LED BYPASS est allumée quand l'effet est actif."]],
 midi_t="6. MIDI",
 midi_i="Fog Z reçoit le MIDI de sa piste, sur tous les canaux (dans Reaper : arme la piste et choisis ton entrée MIDI, monitoring actif, ou envoie-lui un item MIDI).",
 learn_h="MIDI Learn",
 learn=["<b>Aucun CC n'est assigné d'office</b> : chaque commande à piloter depuis ton contrôleur, footswitchs compris, s'assigne avec le MIDI Learn.",
        "<b>Clic droit sur une commande</b> (un fader, DRY FX, Q, le bouton de preset ou un footswitch) : le menu commence par le nom de la commande et <b>MIDI Learn: &lt;commande&gt; (CC n)</b>, ou un tiret (&mdash;) si la commande n'est pas assignée. Choisis-le puis bouge une pédale d'expression ou appuie sur un bouton MIDI : le premier CC reçu est affecté. Pour un footswitch, c'est l'appui (valeur 64 ou plus) qui est appris. Ce message d'apprentissage ne modifie pas le son.",
        "Pendant l'attente, la bulle de message affiche <b>MIDI LEARN: move a control for &lt;commande&gt;</b>, puis <b>&lt;commande&gt; = CC n</b> pendant 2 secondes.",
        "<b>Clear MIDI: &lt;commande&gt;</b> retire l'affectation ; <b>Cancel MIDI learn</b> (ou un nouveau choix du même MIDI Learn) annule l'attente.",
        "Un numéro de CC ne pilote qu'une commande : apprendre un CC déjà utilisé le retire de l'autre commande.",
        "Clic droit ailleurs &gt; <b>MIDI</b> : <b>Learn: &lt;commande&gt; (CC n)</b> pour les 13 commandes, <b>Cancel MIDI learn</b> (pendant l'attente), <b>Clear all MIDI assignments</b> et <b>Latching MIDI pedals</b>.",
        "Les affectations sont <b>sauvegardées avec le projet</b>. Un projet enregistré avec une version précédente dont la table MIDI n'avait jamais été modifiée (footswitchs restés sur les anciens CC d'usine, rien d'autre d'appris) s'ouvre sans aucune affectation ; un projet où tu avais changé ou ajouté une affectation garde toutes ses affectations."],
 mtab=[["Commande", "Type"], ["Dry Output, -2 Octaves, -1 Octave, +1 Octave, +2 Octaves", "Continu : 0-127 = 0-100 % (lissé)"],
       ["Attack, LP Filter, Detune", "Continu : 0-127 = 0-100 % (lissé)"],
       ["Dry FX", "Sélecteur 4 positions (0-31 éteinte, 32-63 rouge, 64-95 verte, 96-127 ambre)"],
       ["Filter Q", "Sélecteur 4 positions (0-31, 32-63, 64-95, 96-127)"],
       ["Bouton de preset", "Sélecteur 8 crans (16 valeurs chacun) : charge le preset 1-8 quand le cran change"],
       ["Footswitch PRESET", "Footswitch momentané (chaque appui) ; option à accrochage"],
       ["Footswitch BYPASS", "Footswitch momentané (chaque appui bascule) ; option à accrochage"],
       ["Presets 1-8", "Program Change 1-8 : charge les mémoires 1 à 8 (fixe, sans apprentissage)"]],
 latch="<b>Latching MIDI pedals</b> (clic droit sur un footswitch ou menu MIDI) : pour les contrôleurs dont les boutons envoient 127 / 0 en alternance. Désactivé (par défaut) : un footswitch agit quand la valeur passe à 64 ou plus (bouton momentané). Activé : chaque changement d'état compte comme un appui.",
 menus_cap="À gauche : clic droit sur le fader DETUNE (pas encore assigné), avec Plugin size &gt; Default size (new windows) ouvert. À droite : clic droit sur le footswitch BYPASS (More... ouvre le menu complet).",
 map_cap="Clic droit ailleurs : menu MIDI avec les 13 commandes apprenables et Clear all MIDI assignments.",
 bub_cap="Bulle de message pendant le MIDI Learn : attente, puis confirmation.",
 auto_h="Paramètres automatisables",
 auto=[["Paramètre", "Plage"], ["Dry Output, -2, -1, +1, +2", "0 &ndash; 100 %"], ["Attack", "Coupé, 10 ms &ndash; 3 s"], ["LP Filter", "50 Hz &ndash; 18 kHz"],
       ["Detune", "0 &ndash; 100 %"], ["Dry FX", "4 modes"], ["Filter Q", "4 niveaux"], ["Bypass", "actif / coupé"]],
 win_t="7. Fenêtre",
 win=["Une nouvelle fenêtre de Fog Z s'ouvre à la taille par défaut, 60 % au départ, et ne peut jamais être réduite sous 60 %. Clic droit &gt; <b>Plugin size</b> : <b>60 %</b>, <b>75 %</b>, <b>100 %</b> ou <b>125 %</b> pour cette fenêtre, avec <b>(default)</b> à côté de la taille par défaut ; ou tire le coin inférieur droit (proportions conservées, jusqu'à 125 %).",
      "<b>Plugin size &gt; Default size (new windows)</b> choisit la taille d'ouverture de toutes les nouvelles fenêtres de Fog Z : le réglage est commun à toutes les instances et enregistré sur l'ordinateur. La fenêtre ouverte prend aussitôt cette taille et suit de nouveau la taille par défaut.",
      "<b>Taille enregistrée avec le projet</b> : une taille choisie pour une instance (dans Plugin size ou en tirant le coin) est sauvegardée avec le projet et reste prioritaire sur la taille par défaut quand le projet est rouvert. Choisir une Default size (new windows) remet cette instance sur la taille par défaut.",
      "Il n'y a pas de ligne d'état permanente : une bulle de message affiche la valeur du fader que tu bouges ou survoles, le nouveau mode DRY FX / Q et les messages du MIDI Learn.",
      "Aussi enregistrés avec le projet : les faders, les 8 mémoires, le preset sélectionné, les affectations MIDI et l'option à accrochage."],
 gest_h="Aide-mémoire des gestes",
 gest=[["Geste", "Effet"], ["Glisser un fader", "Changer la valeur"], ["Double-clic sur un fader", "Valeur par défaut"], ["Survoler un fader", "Afficher sa valeur"],
       ["Clic sur DRY FX / Q", "Mode suivant"], ["Glisser / molette sur le bouton", "Changer de preset (chargé aussitôt)"], ["Clic sur le bouton", "Recharger le preset"],
       ["Maintenir le bouton 3 s", "Sauvegarder"], ["Clic droit sur une commande", "MIDI Learn / Clear MIDI de cette commande, puis le menu"],
       ["Clic droit ailleurs", "Menu : Plugin size, sons d'usine, MIDI"]],
 pre_t="8. Presets",
 pre_i="Fog Z est livré avec douze sons. Ils sont dans le menu déroulant de presets de la fenêtre du plugin (en haut à gauche dans Reaper) et dans clic droit &gt; <b>Factory sounds</b> : en choisir un le charge sur les faders sans changer les 8 mémoires. Les sons 1 à 8 sont aussi rangés dans les huit mémoires de la pédale ; clic droit &gt; <b>Restore factory sounds in presets 1-8</b> les remet en place.",
 pre_tab="Tableau : positions des faders en %, couleur DRY FX et niveau de Q (1 à 4).",
 pre_hdr=["#", "Nom", "Dry", "-2", "-1", "+1", "+2", "Att", "LP", "Det", "Dry FX", "Q"],
 mem="Mémoire de la pédale", host="Menu de l'hôte seulement",
 pdesc=["Nappe d'orgue chaude : toutes les voix, une montée douce, le direct dans toute la chaîne d'effets avec un chorus rotatif lent.",
        "Direct et octaves graves dans un filtre plus sombre : une guitare baryton qui gronde.",
        "Seulement l'octave aiguë, un passe-bas rond et un vibrato rapide avec une montée lente : une voix sinusoïdale façon thérémine. Joue des mélodies lentes sur les cordes aiguës.",
        "L'octave grave seule, une attaque lente comme un archet et un filtre sombre : joue des lignes en notes seules au milieu du manche.",
        "Le classique : ta guitare avec une octave en dessous et une au-dessus, sans effet. Épais, propre et naturel.",
        "Toutes les voix ouvertes, comme un orgue tous tirants sortis. Direct dans Attack + LP.",
        "Voix aiguës avec une montée et un léger chorus : un chœur aérien / harmonica de verre. Superbe en arpèges.",
        "Octaves graves énormes, filtre résonant (Q 4) et montée courte : une basse synthé avec les cordes graves de ta guitare.",
        "Ta guitare plus l'octave aiguë avec un chorus doux : une 12 cordes scintillante.",
        "Montée longue et forte sur les octaves et le direct : la note sort de nulle part et finit fort. Joue un accord et laisse-le s'épanouir.",
        "Registration d'orgue avec le Detune presque en haut : cabine rotative rapide sur les voix aiguës et le direct.",
        "Octaves graves seules, filtre grave résonant et attaque lente : un bourdon de corne de brume."],
 tips_t="9. Conseils d'utilisation",
 tips=["<b>Chaîne Reaper</b> : piste guitare &gt; accordeur &gt; <b>Fog Z</b> &gt; overdrive / fuzz &gt; simulateur d'ampli &gt; delay / reverb. Un générateur d'octaves suit mieux une guitare propre et non traitée : place Fog Z en premier, avant toute saturation.",
       "<b>7 cordes accordée grave</b> : -2 sur un si ou un la grave descend sous la zone utile ; garde -2 bas ou coupé et utilise -1 pour le poids, ou ajoute +1 pour un brillant de 12 cordes sur les riffs. Sub Synth Bass et Fog Horn fonctionnent sur des notes graves seules plutôt que sur des accords.",
       "<b>Fuzz octave</b> : place une fuzz après Fog Z et monte +1 : la fuzz octave classique, mais polyphonique.",
       "<b>Façon Hammond</b> : Dry 70 % &middot; -1 70 % &middot; +1 65 % &middot; +2 45 % &middot; Detune 85 % &middot; DRY FX ambre.",
       "<b>Section de violons</b> : Dry 0 &middot; -1 50 % &middot; +1 70 % &middot; Attack 70 % &middot; Detune 40 %.",
       "<b>Filtre wah</b> : LP à 55 % avec Q 4, puis mets le LP Filter sur une pédale d'expression avec le MIDI Learn.",
       "<b>En live avec un Chocolate Plus</b> : apprends BYPASS et PRESET sur deux boutons, Attack ou Detune sur une pédale d'expression."],
 trb_h="Dépannage",
 trb=[["Problème", "Solution"], ["Pas d'octave, seulement le direct", "Monte les faders d'octave ; vérifie que la LED BYPASS est allumée."],
      ["Trop de grave", "Baisse -2 ou ferme un peu le LP Filter. Fog Z coupe déjà sous 16 Hz."],
      ["Des bips quand on ne joue pas", "La porte de repos garde les octaves muettes jusqu'à 12 dB au-dessus du bruit de fond. Si un ronflement très fort reste, réduis-le à la source."],
      ["Les octaves ondulent sur les accords", "Normal pour des intervalles graves très serrés ; baisse -2, joue la partie grave en notes seules, ou place Fog Z avant la distorsion."],
      ["Les notes ne montent pas", "Attack est en bas (coupé). Monte-le ; pour le direct aussi, mets DRY FX en rouge / vert / ambre."],
      ["La LED PRESET clignote", "Le preset chargé a été modifié. Clique sur le bouton ou appuie sur PRESET pour le recharger, ou maintiens le bouton 3 s pour sauvegarder."],
      ["Un footswitch agit deux fois / un appui sur deux", "Change l'option Latching MIDI pedals selon ton contrôleur."],
      ["Le MIDI ne fait rien", "Vérifie que la piste reçoit le MIDI, puis clic droit sur la commande &gt; MIDI Learn (aucun CC n'est assigné d'office)."],
      ["La fenêtre est trop petite", "Clic droit &gt; Plugin size &gt; 75 %, 100 % ou 125 %, ou tire le coin. Pour toutes les nouvelles fenêtres : Plugin size &gt; Default size (new windows)."],
      ["macOS : plugin introuvable", "Lance la commande xattr de la section installation, puis rescanne."]],
 spec_t="10. Caractéristiques techniques",
 spec=[["Format", "VST3, 64 bits &middot; Windows 10/11 &middot; macOS 10.13+ universel (Apple Silicon + Intel)"],
       ["Canaux", "Entrée mono ou stéréo, sortie mono ou stéréo"], ["Fréquences", "44,1 à 192 kHz (fréquence interne réduite au-dessus de 88 kHz)"],
       ["Latence", "0 échantillon annoncé &middot; direct intact &middot; voix d'octave &asymp; 1,3 ms de retard interne"],
       ["Moteur", "&asymp; 190 filtres passe-bande complexes (3 étages), environ 3 bandes par demi-ton au-dessus de 360 Hz ; porte de bruit par bande, suiveur d'arrêt, porte de repos"],
       ["Voix", "Direct, -2, -1, +1, +2 octaves, chacune 0 &hellip; +3,9 dB (0 dB au repère 80 %)"],
       ["Effets", "Attack 10 ms &hellip; 3 s &middot; LP 50 Hz &hellip; 18 kHz, 4 Q &middot; Detune 0,15 &hellip; 6,6 Hz"],
       ["Presets", "8 mémoires sur la pédale &middot; 12 sons d'usine &middot; enregistrés avec le projet"],
       ["MIDI", "MIDI Learn sur 13 commandes (aucun CC assigné d'office), option à accrochage, Program Change 1-8, tous canaux"],
       ["Fenêtre", "Plugin size 60 % (minimum), 75 %, 100 %, 125 % ; taille d'ouverture des nouvelles fenêtres au choix ; taille choisie pour une instance enregistrée avec le projet ; redimensionnable par le coin"],
       ["Stabilité", "Anti-gel v2 de la fenêtre sous Windows : l'interface ne bloque jamais l'hôte"], ["Nom dans le DAW", "Fog Z (NINE HANDS | DSP) &middot; version " + VERSION]],
 legal="Inspiré de l'Electro-Harmonix POG2. Electro-Harmonix et POG sont des marques de leurs propriétaires ; Fog Z est un hommage indépendant de NINE HANDS | DSP, sans lien avec eux. Construit avec JUCE."),
}

W = A4[0] - 36 * mm
CUR = {"foot": ""}
class SetFoot(Flowable):
    def __init__(self, s): Flowable.__init__(self); self.s = s
    def wrap(self, *a): return (0, 0)
    def draw(self): CUR["foot"] = self.s

def side(a, b, wa):
    t = Table([[a, b]], colWidths=[wa, W - wa])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0)]))
    return t

def section(lang):
    t = T[lang]; f = []
    f.append(NextPageTemplate("p"))
    f.append(Spacer(1, 4 * mm)); f.append(P(t["lang"], "coverlang")); f.append(Spacer(1, 6 * mm))
    f.append(img(A("cover_cutout.jpg"), W * 0.70)); f.append(Spacer(1, 4 * mm))
    f.append(P("F O G &nbsp; Z", "cover")); f.append(Spacer(1, 2 * mm))
    f.append(P(t["sub"], "coversub")); f.append(P(t["ver"], "coversub")); f.append(Spacer(1, 7 * mm))
    f.append(img(A("logo_studio_wiga_blanc.png"), 44 * mm))
    f.append(SetFoot(t["foot"])); f.append(PageBreak())
    # 1-2
    f.append(P(t["pres_t"], "h1")); f += [P(x) for x in t["pres"]]
    f.append(P(t["feat_t"], "h2")); f += bullets(t["feat"])
    f.append(P(t["sig_h"], "h2")); f.append(P(t["sig"]))
    f.append(P(t["inst_t"], "h1"))
    for h, x in t["inst"]: f.append(P(h, "h2")); f.append(P(x))
    f.append(PageBreak())
    # 3
    f.append(P(t["ov_t"], "h1")); f.append(P(t["ov_i"])); f.append(img(A("annotated.jpg"), W * 0.86)); f.append(Spacer(1, 3 * mm))
    hw = (W - 4 * mm) / 2
    f.append(side(table(t["ov1"], [7 * mm, 25 * mm, hw - 32 * mm]), table(t["ov2"], [7 * mm, 27 * mm, hw - 34 * mm]), hw + 4 * mm))
    f.append(Spacer(1, 3 * mm)); f.append(P(t["ov_note"], "note"))
    f.append(PageBreak())
    # 4
    f.append(P(t["ctl_t"], "h1")); f.append(P(t["mix_h"], "h2")); f.append(P(t["mix"])); f += [P(x) for x in t["voices"]]
    cw = (W - 22 * mm) / 6
    f.append(table(t["lvl"], [22 * mm] + [cw] * 6))
    f.append(P(t["ch_h"], "h2")); f.append(P(t["ch"]))
    f.append(P(t["att_h"], "h3")); f.append(P(t["att"])); f.append(table(t["att_t"], [22 * mm] + [cw] * 6))
    f.append(P(t["lp_h"], "h3")); f.append(P(t["lp"])); f.append(table(t["lp_t"], [22 * mm] + [(W - 22 * mm) / 5] * 5))
    f.append(KeepTogether([P(t["det_h"], "h3"), P(t["det"]), table(t["det_t"], [W / 5] * 5)]))
    f.append(KeepTogether([P(t["dfx_h"], "h3"), P(t["dfx"]), table(t["dfx_t"], [24 * mm, W - 24 * mm])]))
    f.append(KeepTogether([Spacer(1, 2 * mm), img(A("dryfx_q.png"), W * 0.42), P(t["dfx_cap"], "small")]))
    f.append(KeepTogether([P(t["q_h"], "h3"), P(t["q"])]))
    f.append(PageBreak())
    # 5
    f.append(P(t["pk_t"], "h1")); f.append(P(t["pk_i"]))
    f.append(side(img(A("preset_knob.png"), 26 * mm), table(t["pk_g"], [20 * mm, W - 52 * mm]), 32 * mm))
    f.append(Spacer(1, 4 * mm)); f.append(img(A("preset_strip.png"), W * 0.8)); f.append(Spacer(1, 3 * mm))
    f.append(table(t["pk_l"], [36 * mm, W - 36 * mm], header=False))
    # 6
    f.append(CondPageBreak(120 * mm))
    f.append(P(t["midi_t"], "h1")); f.append(P(t["midi_i"]))
    f.append(P(t["learn_h"], "h2")); f += bullets(t["learn"])
    f.append(Spacer(1, 2 * mm))
    f.append(KeepTogether([table(t["mtab"], [52 * mm, W - 52 * mm]), Spacer(1, 2 * mm), P(t["latch"], "note")]))
    mt = side(img(MENUS["menu_size"], W * 0.63), img(MENUS["menu_foot"], W * 0.33), W * 0.66)
    f.append(KeepTogether([Spacer(1, 3 * mm), mt, P(t["menus_cap"], "small")]))
    f.append(KeepTogether([img(MENUS["menu_map"], W * 0.62), P(t["map_cap"], "small")]))
    f.append(KeepTogether([img(A("learn_bubble.png"), W * 0.55), P(t["bub_cap"], "small")]))
    f.append(KeepTogether([P(t["auto_h"], "h2"), table(t["auto"], [52 * mm, W - 52 * mm])]))
    # 7
    f.append(CondPageBreak(120 * mm))
    f.append(P(t["win_t"], "h1")); f += [P(x) for x in t["win"]]
    f.append(KeepTogether([P(t["gest_h"], "h2"), table(t["gest"], [55 * mm, W - 55 * mm])]))
    f.append(PageBreak())
    # 8
    f.append(P(t["pre_t"], "h1")); f.append(P(t["pre_i"])); f.append(P(t["pre_tab"], "note"))
    rows = [t["pre_hdr"]]
    for i, r in enumerate(FAC):
        rows.append([str(i + 1), r[0]] + [str(v) for v in r[1:9]] + [DFX[lang][r[9]], str(r[10])])
    nw = 9 * mm
    f.append(table(rows, [7 * mm, 36 * mm] + [nw] * 8 + [16 * mm, W - 59 * mm - 8 * nw], size=7.8))
    f.append(Spacer(1, 3 * mm))
    for i, r in enumerate(FAC):
        tag = (t["mem"] + " " + str(i + 1)) if i < 8 else t["host"]
        f.append(KeepTogether([P("%d. %s <font name='Pop' color='#6B6B70' size='8'>&middot; %s</font>" % (i + 1, r[0], tag), "h3"), P(t["pdesc"][i])]))
    f.append(CondPageBreak(100 * mm))
    # 9-10
    f.append(P(t["tips_t"], "h1")); f += bullets(t["tips"])
    f.append(KeepTogether([P(t["trb_h"], "h2"), table(t["trb"], [52 * mm, W - 52 * mm])]))
    f.append(CondPageBreak(95 * mm))
    f.append(KeepTogether([P(t["spec_t"], "h1"), table(t["spec"], [32 * mm, W - 32 * mm], header=False), Spacer(1, 3 * mm), P(t["legal"], "note")]))
    f.append(PageBreak())
    return f

def deco(c, doc):
    c.saveState()
    c.setFillColor(ACC); c.rect(0, A4[1] - 3 * mm, A4[0], 3 * mm, stroke=0, fill=1)
    c.setFont("Pop", 7.5); c.setFillColor(GREY)
    c.drawString(18 * mm, 10 * mm, CUR["foot"].replace("&middot;", "\u00b7"))
    c.drawRightString(A4[0] - 18 * mm, 10 * mm, str(doc.page))
    c.restoreState()

def cover_bg(c, doc):
    c.saveState(); c.setFillColor(colors.black); c.rect(0, 0, A4[0], A4[1], stroke=0, fill=1)
    c.setFillColor(ACC); c.rect(0, A4[1] - 3 * mm, A4[0], 3 * mm, stroke=0, fill=1); c.restoreState()

doc = BaseDocTemplate(OUT, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm, bottomMargin=18 * mm,
                      title="Fog Z - User manual / Notice v" + VERSION, author="NINE HANDS | DSP")
doc.addPageTemplates([PageTemplate(id="cover", frames=[Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="fc")], onPage=cover_bg),
                      PageTemplate(id="p", frames=[Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="f")], onPage=deco)])
en = section("en"); fr = section("fr")
en[-1:] = [NextPageTemplate("cover"), PageBreak()]
doc.build(en + fr[:-1])
print(OUT)
