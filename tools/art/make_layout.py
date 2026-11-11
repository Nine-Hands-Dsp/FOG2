import json
L=json.load(open('export/layout.json')); TX=json.load(open('silk_texts.json'))
f=lambda v:f'{v:.2f}f'
P=lambda p:'{ '+f(p[0])+', '+f(p[1])+' }'
o=[]
o.append('// genere par tools/make_layout.py (Fog Z v2) - ne pas modifier a la main')
o.append('// repere 1133 x 900 unites = fond 2266 x 1800 px / 2 (format double, pedale plein cadre, jacks contre les bords)')
o.append('#pragma once\n#include <juce_graphics/juce_graphics.h>\nnamespace layout\n{')
o.append('    constexpr float frameW = 1133.0f, frameH = 900.0f;')
o.append('    const float faderX[8] = { '+', '.join(f(x) for x in L['faderX'])+' };')
o.append(f"    constexpr float travelTop = {f(L['travelTop'])}, travelBot = {f(L['travelBot'])};   // centre du capuchon sur la ligne la plus haute / basse")
o.append(f"    constexpr float capW = {f(L['capSize'][0])}, capH = {f(L['capSize'][1])}, capSprW = {f(L['capSprite'][0])}, capSprH = {f(L['capSprite'][1])};   // sprite = capuchon + ombre")
o.append(f"    const juce::Point<float> dryBtn {P(L['btn'][0])}, qBtn {P(L['btn'][1])}; constexpr float btnS = {f(L['btnS'])}, btnHitR = {f(L['btnS']*0.42)};")
o.append(f"    const juce::Point<float> dryLed {P(L['led_dry'])}, qLed {P(L['led_q'])}, preLed {P(L['led_pre'])}, bypLed {P(L['led_byp'])};")
o.append(f"    constexpr float ledLensS = {f(L['ledLens'])}, ledFsS = {f(L['ledFs'])}, ledDomeS = {f(L['ledDome'])};   // diametres ; halo = 3 x")
o.append('    const juce::Point<float> presetLed[8] = { '+', '.join(P(L[f'led_p{i}']) for i in range(8))+' };')
o.append(f"    const juce::Point<float> fsPre {P(L['fs'][0])}, fsByp {P(L['fs'][1])}; constexpr float fsBtnR = {f(L['fsBtnR'])}, fsHitR = {f(L['fsHitR'])};")
o.append(f"    const juce::Point<float> knobPos {P(L['knob'])}; constexpr float knobS = {f(L['knobS'])}, knobR = {f(L['knobR'])};   // calques 512 px, cadre knobS")
(px,py),pw,ph=L['pill']
o.append(f"    const juce::Rectangle<float> presetRect {{ {f(px)}, {f(py)}, {f(pw)}, {f(ph)} }};   // pastille unique : barre de presets / ligne d'etat (400 x 38)")
o.append('    constexpr float presetFont = 23.0f;')
o.append(f"    const juce::Point<float> logoPos {P(L['logo'])}; constexpr float logoW = {f(L['logoW'])};")
o.append('    // serigraphie : textes en Poppins Bold (taille em en unites), centres sur (x, y), rotation 90 = se lit de bas en haut')
o.append('    struct Txt { const char* s; float em, x, y, rot; };')
o.append('    const Txt texts[] = {')
o.append(',\n'.join(f'        {{ "{t["s"]}", {f(t["em"])}, {f(t["x"])}, {f(t["y"])}, {f(float(t["rot"]))} }}' for t in TX))
o.append('    };\n}')
open('export/Layout.h','w').write('\n'.join(o)+'\n'); print('\n'.join(o[:20]))
