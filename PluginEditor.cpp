#include "PluginEditor.h"
#include "BinaryData.h"
#include "WigaWindowSize.h"
#include "NineHandsGlow.h"

using namespace juce;

namespace
{
    const Colour inkCol (0xffe2dace);              // serigraphie creme
    const Colour barFace (0xff0e0e10), barRim (0xffcec6bc), barInk (0xffeef0f4);
    const Colour menuAccent (0xffd9483b);          // rouge de la pedale (pastille des en-tetes de menu)
    constexpr float arrowW = 34.0f;
    constexpr float knobStep = 18.0f;              // unites de souris par cran du gros bouton
    const char* dryNames[4] = { "DRY CLEAN", "ATTACK", "ATTACK + LP", "ATTACK + LP + DETUNE" };
    const char* qNames[4]   = { "1 (FLAT)", "2", "3", "4 (PEAK)" };

    Image png (const void* d, int n) { return ImageCache::getFromMemory (d, n); }
    float detentAngle (int sel) { return degreesToRadians (-105.0f + 30.0f * (float) jlimit (0, 7, sel)); }
}

//==============================================================================
FogEditor::FogEditor (FogProcessor& p) : AudioProcessorEditor (p), proc (p)
{
    background = png (BinaryData::background_png, BinaryData::background_pngSize);
    capImg     = png (BinaryData::fader_cap_png, BinaryData::fader_cap_pngSize);
    btnDown    = png (BinaryData::button_down_png, BinaryData::button_down_pngSize);
    lensRed    = png (BinaryData::lens_red_png, BinaryData::lens_red_pngSize);
    lensAmber  = png (BinaryData::lens_amber_png, BinaryData::lens_amber_pngSize);
    lensGreen  = png (BinaryData::lens_green_png, BinaryData::lens_green_pngSize);
    haloRed    = png (BinaryData::halo_red_png, BinaryData::halo_red_pngSize);
    haloAmber  = png (BinaryData::halo_amber_png, BinaryData::halo_amber_pngSize);
    haloGreen  = png (BinaryData::halo_green_png, BinaryData::halo_green_pngSize);
    domeAmber  = png (BinaryData::dome_amber_png, BinaryData::dome_amber_pngSize);
    haloDome   = png (BinaryData::halo_dome_png, BinaryData::halo_dome_pngSize);
    knobLayers[0] = png (BinaryData::knob_shadow_png, BinaryData::knob_shadow_pngSize);
    knobLayers[1] = png (BinaryData::knob_crown_png, BinaryData::knob_crown_pngSize);
    knobLayers[2] = png (BinaryData::knob_cap_png, BinaryData::knob_cap_pngSize);
    knobLayers[3] = png (BinaryData::knob_marker_png, BinaryData::knob_marker_pngSize);
    knobLayers[4] = png (BinaryData::knob_highlight_png, BinaryData::knob_highlight_pngSize);

    regularFace = Typeface::createSystemTypefaceFor (BinaryData::PoppinsRegular_ttf, BinaryData::PoppinsRegular_ttfSize);
    mediumFace  = Typeface::createSystemTypefaceFor (BinaryData::PoppinsMedium_ttf, BinaryData::PoppinsMedium_ttfSize);
    boldFace    = Typeface::createSystemTypefaceFor (BinaryData::PoppinsBold_ttf, BinaryData::PoppinsBold_ttfSize);
    menuLnf.f = { regularFace, mediumFace, boldFace };

    if (auto xml = XmlDocument::parse (String::fromUTF8 (BinaryData::silk_svg, BinaryData::silk_svgSize)))
        silk = Drawable::createFromSVG (*xml);
    if (auto xml = XmlDocument::parse (String::fromUTF8 (BinaryData::NineHandsLogoWhite_svg, BinaryData::NineHandsLogoWhite_svgSize)))
        logo = Drawable::createFromSVG (*xml);

    // textes de la serigraphie : Poppins Bold, centres sur leur point (boite des glyphes), 90 = se lit de bas en haut
    for (const auto& t : layout::texts)
    {
        GlyphArrangement ga;
        ga.addLineOfText (Font (FontOptions (boldFace).withPointHeight (t.em)), t.s, 0.0f, 0.0f);
        Path p; ga.createPath (p);
        const auto b = p.getBounds();
        p.applyTransform (AffineTransform::translation (-b.getCentreX(), -b.getCentreY())
                              .rotated (-degreesToRadians (t.rot)).translated (t.x, t.y));
        textPath.addPath (p);
    }
    {   // hauteur des capitales de la pastille (centrage vertical sur les capitales, jambages ignores)
        GlyphArrangement ga; ga.addLineOfText (Font (FontOptions (mediumFace).withPointHeight (100.0f)), "H", 0.0f, 0.0f);
        Path p; ga.createPath (p); capHeightRatio = p.getBounds().getHeight() / 100.0f;
    }

    glow = (float) NineHandsGlow::percent (JucePlugin_Name) / 100.0f;
    knobAngle = knobTarget = detentAngle (proc.getSelected());
    for (int i = 0; i < 8; ++i) { lastVals[i] = faderValue (i); drawnFader[i] = -1.0f; }
    lastDryFx = roundToInt (proc.apvts.getRawParameterValue (FogIDs::dryFx)->load());
    lastQ = roundToInt (proc.apvts.getRawParameterValue (FogIDs::q)->load());
    lastByp = proc.isBypassed(); lastLoaded = proc.getLoaded(); lastFactory = proc.lastFactory.load();
    presetText = proc.presetLine();

    // taille : 495 px de haut par defaut (« 60 % ») = taille minimale, proportions bloquees ;
    // ouverture a la taille enregistree pour cette instance, sinon a la taille par defaut choisie dans le menu
    const double aspect = (double) baseW / (double) baseH;
    const int saved = proc.uiHeight.load();
    const int h0 = saved > 0 ? jlimit (heightDefault, heightMax, saved)
                             : sizeHeight (WigaWindowSize::defaultIndex (JucePlugin_Name, numSizes));
    setResizable (true, true);
    setResizeLimits (roundToInt (heightDefault * aspect), heightDefault, roundToInt (heightMax * aspect), heightMax);
    getConstrainer()->setFixedAspectRatio (aspect);
    setOpaque (true);
    openHeight = h0;
    setSize (roundToInt (h0 * aspect), h0);
    rebuildCaches();
    startTimerHz (30);
}

FogEditor::~FogEditor()
{
    PopupMenu::dismissAllActiveMenus();
    stopTimer();
}

//==============================================================================
// Anti-gel v2 (NINE HANDS | DSP) : moteur logiciel sous Windows, caches refaits par le timer seulement,
// chien de garde des redessins, aucun appel a l'hote depuis le thread audio (voir PluginProcessor).
void FogEditor::useSoftwareRenderer()
{
    auto* peer = getPeer();
    if ((void*) peer != lastPeer) { lastPeer = (void*) peer; repaint(); }
   #if JUCE_WINDOWS
    if (peer != nullptr)
    {
        int sw = peer->getAvailableRenderingEngines().indexOf ("Software Renderer");
        if (sw < 0) sw = 0;
        if (peer->getCurrentRenderingEngine() != sw)
            peer->setCurrentRenderingEngine (sw);
    }
   #endif
}

void FogEditor::parentHierarchyChanged() { useSoftwareRenderer(); }
void FogEditor::visibilityChanged()      { useSoftwareRenderer(); if (isShowing()) repaint(); }

float FogEditor::physicalScale() const
{
    if (forcedScale > 0.0f) return forcedScale;
    return jlimit (1.0f, 4.0f, (float) Component::getApproximateScaleFactorForComponent (this));
}

void FogEditor::askRepaint (Rectangle<float> u)
{
    if (repaintAskedMs <= 0.0) repaintAskedMs = Time::getMillisecondCounterHiRes();
    repaint (u.transformedBy (AffineTransform::scale (k())).getSmallestIntegerContainer().expanded (2));
}

void FogEditor::resized()
{
    // jamais de setSize ici ; taille de l'instance enregistree seulement si elle a ete changee
    if (proc.uiHeight.load() > 0 || (openHeight > 0 && std::abs (getHeight() - openHeight) > 2))
        proc.uiHeight.store (jlimit (heightDefault, heightMax, getHeight()));
    resizeSettle = 4;
}

int FogEditor::sizeHeight (int idx)
{
    const int h[numSizes] = { heightDefault, roundToInt (743 * 0.75f), 743 };
    return h[jlimit (0, numSizes - 1, idx)];
}

void FogEditor::setWindowHeight (int h)
{
    h = jlimit (heightDefault, heightMax, h);
    setSize (roundToInt ((double) h * baseW / baseH), h);
}

void FogEditor::setGlowPercent (int pc)
{
    NineHandsGlow::setPercent (JucePlugin_Name, pc);
    glow = (float) jlimit (25, 100, pc) / 100.0f;
    repaint();
}

void FogEditor::flash (const String& t, double seconds)
{
    statusText = t;
    statusUntil = Time::getMillisecondCounterHiRes() + seconds * 1000.0;
}

// fond + serigraphie + logo a la resolution physique de l'ecran, et calques du gros bouton a la bonne taille
void FogEditor::rebuildCaches (float sc)
{
    if (sc <= 0.0f) sc = cacheScale > 0.0f ? cacheScale : physicalScale();
    const int w = getWidth(), h = getHeight();
    if (w <= 0 || h <= 0) return;
    if (w == cacheW && h == cacheH && std::abs (sc - cacheScale) < 0.01f && bgScaled.isValid()) return;
    cacheW = w; cacheH = h; cacheScale = sc;
    const int pw = roundToInt ((float) w * sc), ph = roundToInt ((float) h * sc);
    const float u = (float) ph / baseH;                     // pixels physiques par unite

    bgScaled = Image (Image::ARGB, pw, ph, true);
    {
        Graphics g (bgScaled);
        g.setImageResamplingQuality (Graphics::highResamplingQuality);
        g.drawImage (background, Rectangle<float> (0.0f, 0.0f, (float) pw, (float) ph));
        g.addTransform (AffineTransform::scale (u));
        if (silk != nullptr) silk->draw (g, 0.96f);
        g.setColour (inkCol.withAlpha (0.96f));
        g.fillPath (textPath);
        if (logo != nullptr)
        {
            const auto vb = logo->getDrawableBounds();
            const float lw = layout::logoW, lh = lw * vb.getHeight() / jmax (1.0f, vb.getWidth());
            logo->drawWithin (g, { layout::logoPos.x - lw * 0.5f, layout::logoPos.y - lh * 0.5f, lw, lh }, RectanglePlacement::centred, 0.93f);
        }
    }

    // gros bouton : ombre, pile qui tourne (couronne + chapeau + repere) et reflets fixes, a la taille physique
    const int kp = jmax (8, roundToInt (layout::knobS * u));
    auto fit = [kp] (const Image& src)
    {
        Image out (Image::ARGB, kp, kp, true);
        Graphics g (out); g.setImageResamplingQuality (Graphics::highResamplingQuality);
        g.drawImage (src, Rectangle<float> (0.0f, 0.0f, (float) kp, (float) kp));
        return out;
    };
    knobShadow = fit (knobLayers[0]);
    knobHighlight = fit (knobLayers[4]);
    knobStack = Image (Image::ARGB, kp, kp, true);
    {
        Graphics g (knobStack);
        for (int i = 1; i <= 3; ++i) g.drawImageAt (fit (knobLayers[i]), 0, 0);
    }
    knobFrame = Image (Image::ARGB, kp, kp, true);
    knobScratch = Image (Image::ARGB, kp, kp, true);
    drawnKnobAngle = 1.0e9f;
    renderKnob();
    repaint();
}

// image du gros bouton a l'angle courant : ombre (decalee a 45 deg vers le bas a droite) + pile, floues
// dans le sens de la rotation pendant un saut de cran, puis reflets fixes
void FogEditor::renderKnob()
{
    if (! knobFrame.isValid()) return;
    const int kp = knobFrame.getWidth();
    const float c = (float) kp * 0.5f;
    knobFrame.clear (knobFrame.getBounds());
    auto drawBlurred = [&] (Graphics& g, const Image& img, Point<float> off)
    {
        auto place = [&] (float a) { return AffineTransform::rotation (a, c, c).translated (off.x, off.y); };
        if (knobBlur <= 0.0f) { g.drawImageTransformed (img, place (knobAngle), false); return; }
        const int n = jlimit (4, 16, (int) std::ceil (knobBlur / degreesToRadians (3.0f)) + 1);
        knobScratch.clear (knobScratch.getBounds());
        {
            Graphics gs (knobScratch);
            gs.setImageResamplingQuality (Graphics::highResamplingQuality);
            for (int i = 0; i < n; ++i)
            {
                const float t = (float) i / (float) (n - 1);
                gs.setOpacity (1.0f / (float) (i + 1));                // moyenne progressive exacte
                gs.drawImageTransformed (img, place (knobAngle - knobBlurDir * knobBlur * t), false);
            }
        }
        g.drawImageAt (knobScratch, 0, 0);
    };
    Graphics g (knobFrame);
    g.setImageResamplingQuality (Graphics::highResamplingQuality);
    const float off = 0.025f * (float) kp * 0.8232f;                   // ombre a 45 deg vers le bas a droite
    drawBlurred (g, knobShadow, { off, off });
    drawBlurred (g, knobStack, {});
    g.drawImageAt (knobHighlight, 0, 0);
}

void FogEditor::settleForCapture()
{
    knobAngle = knobTarget = detentAngle (proc.getSelected()); knobBlur = 0.0f; renderKnob();
    statusAlpha = Time::getMillisecondCounterHiRes() < statusUntil ? 1.0f : 0.0f;
    presetText = proc.presetLine();
    timerCallback();
    repaint();
}

void FogEditor::pressForCapture (int what, bool down)
{
    if (what == 0) dryDown = down; else if (what == 1) qDown = down;
    else if (what == 2) fsPreDown = down; else fsBypDown = down;
    repaint();
}

//==============================================================================
float FogEditor::faderValue (int i) const { return proc.apvts.getParameter (FogIDs::faders[i])->getValue(); }
float FogEditor::faderY (int i) const { return layout::travelBot + (layout::travelTop - layout::travelBot) * faderValue (i); }

Rectangle<float> FogEditor::faderArea (int i) const
{
    return Rectangle<float> (layout::capSprW, layout::capSprH).withCentre ({ layout::faderX[i], faderY (i) }).expanded (2.0f);
}

void FogEditor::setFader (int i, float v, bool inGesture)
{
    auto* p = proc.apvts.getParameter (FogIDs::faders[i]);
    if (! inGesture) p->beginChangeGesture();
    p->setValueNotifyingHost (jlimit (0.0f, 1.0f, v));
    if (! inGesture) p->endChangeGesture();
}

String FogEditor::faderText (int i, float v) const
{
    if (i == 5)
    {
        if (v < 0.02f) return "OFF";
        const float s = 0.010f * std::pow (300.0f, (v - 0.02f) / 0.98f);
        return s < 1.0f ? String (roundToInt (s * 1000)) + " ms" : String (s, 2) + " s";
    }
    if (i == 6)
    {
        const float f = 50.0f * std::pow (360.0f, v);
        return f < 1000 ? String (roundToInt (f)) + " Hz" : String (f / 1000.0f, 1) + " kHz";
    }
    return String (roundToInt (v * 100)) + " %";
}

void FogEditor::cycleParam (const char* id, const String& label, const StringArray& names)
{
    auto* prm = proc.apvts.getParameter (id);
    const int cur = roundToInt (prm->convertFrom0to1 (prm->getValue()));
    const int nxt = (cur + 1) % 4;
    prm->beginChangeGesture(); prm->setValueNotifyingHost (prm->convertTo0to1 ((float) nxt)); prm->endChangeGesture();
    flash (label + "  " + names[nxt]);
}

bool FogEditor::knobHoldBlinking() const
{
    return knobDown && ! knobDragged && ! knobSaved && Time::getMillisecondCounter() - knobDownTime >= 2000;
}

//==============================================================================
void FogEditor::timerCallback()
{
    const double now = Time::getMillisecondCounterHiRes();
    const auto nowMs = Time::getMillisecondCounter();
    if (getPeer() != lastPeer || now - lastRendererCheckMs > 1000.0) { lastRendererCheckMs = now; useSoftwareRenderer(); }
    if (resizeSettle > 0 && --resizeSettle == 0) rebuildCaches (physicalScale());
    else if (resizeSettle == 0 && now - lastScaleCheckMs > 250.0)
    {
        lastScaleCheckMs = now;
        const float sc = physicalScale();
        if (std::abs (sc - cacheScale) > 0.01f) rebuildCaches (sc);
    }
    if (repaintAskedMs > 0.0 && isShowing() && now - repaintAskedMs > 1500.0 && lastPaintMs < repaintAskedMs)
    {
        repaintAskedMs = 0.0; lastPeer = nullptr;
        useSoftwareRenderer(); repaint();
    }
    if (now - lastGlowReadMs > 3000.0 && resizeSettle == 0)
    {
        lastGlowReadMs = now;
        glow = (float) NineHandsGlow::percent (JucePlugin_Name) / 100.0f;     // reglage commun a toutes les fenetres
    }

    // ---- gros bouton : maintenu 3 s = sauvegarde ; saut de cran en deux images avec flou de mouvement
    if (knobDown && ! knobDragged && ! knobSaved && nowMs - knobDownTime >= 3000)
    {
        proc.savePreset (proc.getSelected()); knobSaved = true;
        flash ("Saved to preset " + String (proc.getSelected() + 1));
    }
    knobTarget = detentAngle (proc.getSelected());
    {
        const float before = knobAngle;
        if (std::abs (knobTarget - knobAngle) > 1.0e-4f)
            knobAngle = (knobSnapStep++ == 0) ? knobAngle + (knobTarget - knobAngle) * 0.65f : knobTarget;
        else knobSnapStep = 0;
        const float v = knobAngle - before;
        if (std::abs (v) > 1.0e-5f) knobBlurDir = v > 0.0f ? 1.0f : -1.0f;
        knobBlur = jmax (jmin (std::abs (v), degreesToRadians (40.0f)), knobBlur * 0.6f);
        if (knobBlur < 0.002f) knobBlur = 0.0f;
        if (std::abs (knobAngle - drawnKnobAngle) > 1.0e-4f || knobBlur != drawnKnobBlur)
        {
            renderKnob();
            drawnKnobAngle = knobAngle; drawnKnobBlur = knobBlur;
            askRepaint (Rectangle<float> (layout::knobS, layout::knobS).withCentre (layout::knobPos));
        }
    }

    // ---- reglages qui bougent (souris, automation, MIDI) -> ligne d'etat ; changement de preset -> barre seulement
    const int loaded = proc.getLoaded(), fact = proc.lastFactory.load();
    const bool presetChanged = loaded != lastLoaded || fact != lastFactory;
    int moved = 0, last = -1;
    for (int i = 0; i < 8; ++i)
    {
        const float v = faderValue (i);
        if (std::abs (v - lastVals[i]) > 1.0e-4f) { ++moved; last = i; }
        lastVals[i] = v;
    }
    const int df = roundToInt (proc.apvts.getRawParameterValue (FogIDs::dryFx)->load());
    const int q  = roundToInt (proc.apvts.getRawParameterValue (FogIDs::q)->load());
    const bool byp = proc.isBypassed();
    if (! presetChanged && moved <= 2)
    {
        if (last >= 0) flash (String (FogIDs::faderNames[last]) + "  " + faderText (last, lastVals[last]));
        if (df != lastDryFx && lastDryFx >= 0) flash ("DRY FX  " + String (dryNames[jlimit (0, 3, df)]));
        if (q != lastQ && lastQ >= 0) flash ("FILTER Q  " + String (qNames[jlimit (0, 3, q)]));
    }
    if (byp != lastByp) flash (byp ? "Bypass" : "Effect on", 1.6);
    lastDryFx = df; lastQ = q; lastByp = byp; lastLoaded = loaded; lastFactory = fact;

    if (const int lt = proc.learnTarget.load(); lt >= 0)
        flash ("MIDI LEARN  " + String (FogProcessor::learnDef (lt).name), 0.25);
    if (const int learned = proc.lastLearned.exchange (-1); learned >= 0)
        flash (String (FogProcessor::learnDef (learned).name) + " = CC " + String (proc.ccMap[learned].load()));

    const float st = now < statusUntil ? 1.0f : 0.0f;
    statusAlpha += (st - statusAlpha) * (st > statusAlpha ? 0.45f : 0.30f);      // ~120 ms a l'apparition, ~300 ms au retour
    if (statusAlpha < 0.005f) statusAlpha = 0.0f;
    if (statusAlpha > 0.995f) statusAlpha = 1.0f;
    presetText = proc.presetLine();

    // ---- boutons relaches au plus tot 120 ms apres l'appui (l'enfoncement se voit toujours)
    if (dryDown && dryUpAt > 0.0 && now >= dryUpAt) { dryDown = false; dryUpAt = 0.0; askRepaint (Rectangle<float> (layout::btnS, layout::btnS).withCentre (layout::dryBtn)); }
    if (qDown && qUpAt > 0.0 && now >= qUpAt)       { qDown = false;  qUpAt = 0.0;  askRepaint (Rectangle<float> (layout::btnS, layout::btnS).withCentre (layout::qBtn)); }

    // ---- LED
    LedState s;
    s.dryFx = jlimit (0, 3, df); s.q = jlimit (0, 3, q);
    s.sel = proc.getSelected();
    s.pre = loaded >= 0 && loaded == s.sel;
    if (s.pre && proc.isModified()) s.pre = ((nowMs / 90) % 2) == 0;        // preset modifie : la LED PRESET clignote
    s.byp = ! byp;
    s.presetBlink = knobHoldBlinking() || nowMs - proc.getSaveBlinkStart() < 450;
    s.presetBlinkOn = s.presetBlink ? ((nowMs / 125) % 2) == 0 : false;
    leds = s;
    if (leds != drawnLeds)
    {
        auto haloRect = [] (Point<float> c, float d) { return Rectangle<float> (d * 3.0f, d * 3.0f).withCentre (c); };
        if (leds.dryFx != drawnLeds.dryFx) askRepaint (haloRect (layout::dryLed, layout::ledLensS));
        if (leds.q != drawnLeds.q)         askRepaint (haloRect (layout::qLed, layout::ledLensS));
        if (leds.pre != drawnLeds.pre)     askRepaint (haloRect (layout::preLed, layout::ledFsS));
        if (leds.byp != drawnLeds.byp)     askRepaint (haloRect (layout::bypLed, layout::ledFsS));
        if (leds.sel != drawnLeds.sel || leds.presetBlink != drawnLeds.presetBlink || leds.presetBlinkOn != drawnLeds.presetBlinkOn)
            askRepaint (haloRect (layout::presetLed[0], layout::ledDomeS).getUnion (haloRect (layout::presetLed[7], layout::ledDomeS)));
        drawnLeds = leds;
    }

    // ---- faders
    for (int i = 0; i < 8; ++i)
        if (std::abs (drawnFader[i] - lastVals[i]) > 1.0e-5f)
        {
            const float y0 = layout::travelBot + (layout::travelTop - layout::travelBot) * jmax (0.0f, drawnFader[i]);
            askRepaint (Rectangle<float> (layout::capSprW, layout::capSprH).withCentre ({ layout::faderX[i], y0 }).expanded (2.0f));
            askRepaint (faderArea (i));
            drawnFader[i] = lastVals[i];
        }

    // ---- pastille
    if (std::abs (dStatus - statusAlpha) > 0.003f || statusText != dStatusText || presetText != dPresetText || hover != dHover)
    {
        dStatus = statusAlpha; dStatusText = statusText; dPresetText = presetText; dHover = hover;
        askRepaint (layout::presetRect.expanded (3.0f));
    }
}

//==============================================================================
void FogEditor::paint (Graphics& g)
{
    lastPaintMs = Time::getMillisecondCounterHiRes();
    repaintAskedMs = 0.0;
    g.fillAll (Colour (0xff111112));          // derriere les jacks : le fond de l'image est transparent
    if (bgScaled.isValid())
    {
        g.setImageResamplingQuality (Graphics::lowResamplingQuality);
        g.drawImage (bgScaled, getLocalBounds().toFloat());
    }
    else
    {
        g.setImageResamplingQuality (Graphics::highResamplingQuality);
        g.drawImage (background, getLocalBounds().toFloat());
    }

    g.addTransform (AffineTransform::scale (k()));
    g.setImageResamplingQuality (Graphics::highResamplingQuality);

    // boutons DRY FX / Q enfonces (le bouton relache est dans le fond)
    if (dryDown) g.drawImage (btnDown, Rectangle<float> (layout::btnS, layout::btnS).withCentre (layout::dryBtn));
    if (qDown)   g.drawImage (btnDown, Rectangle<float> (layout::btnS, layout::btnS).withCentre (layout::qBtn));

    // footswitches enfonces : le bouton s'enfonce dans son ecrou (ombre dans la gorge)
    for (auto [down, c] : { std::pair<bool, Point<float>> { fsPreDown, layout::fsPre }, { fsBypDown, layout::fsByp } })
        if (down)
        {
            const float r = layout::fsBtnR;
            ColourGradient sh (Colours::black.withAlpha (0.42f), c.x - r * 0.7f, c.y - r * 0.7f, Colours::black.withAlpha (0.12f), c.x + r * 0.6f, c.y + r * 0.6f, false);
            g.setGradientFill (sh);
            g.fillEllipse (Rectangle<float> (r * 2.0f, r * 2.0f).withCentre (c));
        }

    drawLeds (g);

    // capuchons des faders (sprite = capuchon + ombre)
    for (int i = 0; i < 8; ++i)
        g.drawImage (capImg, Rectangle<float> (layout::capSprW, layout::capSprH).withCentre ({ layout::faderX[i], faderY (i) }));

    // gros bouton PRESET
    if (knobFrame.isValid())
        g.drawImage (knobFrame, Rectangle<float> (layout::knobS, layout::knobS).withCentre (layout::knobPos));

    drawBar (g);
}

void FogEditor::drawLeds (Graphics& g)
{
    // lumiere de la LED : toujours a fond ; halo : dose par le reglage Glow
    auto lit = [&] (const Image& lens, const Image& halo, Point<float> c, float d, float level)
    {
        if (level <= 0.003f) return;
        g.setOpacity (jmin (1.0f, level * glow));
        g.drawImage (halo, Rectangle<float> (d * 3.0f, d * 3.0f).withCentre (c));
        g.setOpacity (jmin (1.0f, level));
        g.drawImage (lens, Rectangle<float> (d, d).withCentre (c));
        g.setOpacity (1.0f);
    };
    const Image* dfLens[4] = { nullptr, &lensRed, &lensGreen, &lensAmber };
    const Image* dfHalo[4] = { nullptr, &haloRed, &haloGreen, &haloAmber };
    if (leds.dryFx > 0) lit (*dfLens[leds.dryFx], *dfHalo[leds.dryFx], layout::dryLed, layout::ledLensS, 1.0f);
    const float ql[4] = { 0.0f, 0.35f, 0.66f, 1.0f };                      // Q : de plus en plus lumineuse
    lit (lensRed, haloRed, layout::qLed, layout::ledLensS, ql[leds.q]);
    for (int i = 0; i < 8; ++i)
    {
        bool on = i == leds.sel;
        if (leds.presetBlink) on = leds.presetBlinkOn;
        if (on) lit (domeAmber, haloDome, layout::presetLed[i], layout::ledDomeS, 1.0f);
    }
    if (leds.pre) lit (lensRed, haloRed, layout::preLed, layout::ledFsS, 1.0f);
    if (leds.byp) lit (lensRed, haloRed, layout::bypLed, layout::ledFsS, 1.0f);
}

void FogEditor::drawBar (Graphics& g)
{
    // pastille unique (400 x 38, reference Strong Pickle) : barre de presets au repos, ligne d'etat pendant les reglages
    const auto r = layout::presetRect;
    const float rr = r.getHeight() * 0.5f;
    const bool barHot = hover == Hit::presetPrev || hover == Hit::presetName || hover == Hit::presetNext;
    g.setColour (Colour (0x96140808)); g.fillRoundedRectangle (r.expanded (0.75f), rr + 0.75f);      // fin contour sombre
    g.setColour (barRim.brighter (barHot && statusAlpha <= 0.0f ? 0.3f : 0.0f)); g.fillRoundedRectangle (r, rr);   // liseré clair
    g.setColour (barFace); g.fillRoundedRectangle (r.reduced (1.0f), rr - 1.0f);

    // texte centre sur la hauteur des capitales (les jambages des g, p, y ne le font pas descendre)
    auto drawCentred = [&] (const String& text, Rectangle<float> area, float alpha, float minScale)
    {
        Graphics::ScopedSaveState s (g);
        float h = layout::presetFont;
        Font f (FontOptions (mediumFace).withPointHeight (h));
        float w = GlyphArrangement::getStringWidth (f, text);
        if (w > area.getWidth()) { h = jmax (h * minScale, h * area.getWidth() / w); f = Font (FontOptions (mediumFace).withPointHeight (h)); }
        String t = text;
        while (GlyphArrangement::getStringWidth (f, t) > area.getWidth() && t.length() > 1) t = t.dropLastCharacters (2) + String (CharPointer_UTF8 ("\xe2\x80\xa6"));
        GlyphArrangement ga;
        ga.addLineOfText (f, t, 0.0f, 0.0f);
        const float tw = GlyphArrangement::getStringWidth (f, t);
        const float baseline = area.getCentreY() + h * capHeightRatio * 0.5f;
        g.setColour (barInk.withAlpha (alpha));
        ga.draw (g, AffineTransform::translation (area.getCentreX() - tw * 0.5f, baseline));
    };

    if (statusAlpha > 0.0f)
        drawCentred (statusText, r.reduced (rr, 0.0f), statusAlpha, 0.6f);
    const float a = 1.0f - statusAlpha;
    if (a <= 0.0f) return;
    auto arrow = [&] (Rectangle<float> ar, bool left, bool hot)
    {
        Path p; const auto c = ar.getCentre(); const float sz = 5.5f;
        if (left) p.addTriangle (c.x + sz * 0.6f, c.y - sz, c.x + sz * 0.6f, c.y + sz, c.x - sz * 0.8f, c.y);
        else      p.addTriangle (c.x - sz * 0.6f, c.y - sz, c.x - sz * 0.6f, c.y + sz, c.x + sz * 0.8f, c.y);
        g.setColour (barInk.withAlpha ((hot ? 1.0f : 0.6f) * a));
        g.fillPath (p);
    };
    arrow (r.withWidth (arrowW), true, hover == Hit::presetPrev);
    arrow (r.withTrimmedLeft (r.getWidth() - arrowW), false, hover == Hit::presetNext);
    drawCentred (presetText, r.reduced (arrowW, 0.0f), (hover == Hit::presetName ? 1.0f : 0.94f) * a, 0.7f);
}

//==============================================================================
// Souris
//==============================================================================
FogEditor::Hit FogEditor::hitAt (Point<float> u, int& fi) const
{
    fi = -1;
    if (u.getDistanceFrom (layout::knobPos) <= layout::knobR) return Hit::knob;
    if (u.getDistanceFrom (layout::dryBtn) <= layout::btnHitR) return Hit::dryBtn;
    if (u.getDistanceFrom (layout::qBtn) <= layout::btnHitR) return Hit::qBtn;
    if (u.getDistanceFrom (layout::fsPre) <= layout::fsHitR) return Hit::fsPre;
    if (u.getDistanceFrom (layout::fsByp) <= layout::fsHitR) return Hit::fsByp;
    for (int i = 0; i < 8; ++i)
        if (std::abs (u.x - layout::faderX[i]) <= layout::capW * 0.75f
            && u.y >= layout::travelTop - layout::capH * 0.6f && u.y <= layout::travelBot + layout::capH * 0.6f)
        { fi = i; return Hit::fader; }
    const auto r = layout::presetRect;
    if (r.contains (u))
        return u.x < r.getX() + arrowW ? Hit::presetPrev : (u.x > r.getRight() - arrowW ? Hit::presetNext : Hit::presetName);
    return Hit::none;
}

void FogEditor::mouseMove (const MouseEvent& e)
{
    int fi = -1;
    hover = hitAt (toUnits (e.position), fi);
    hoverFader = fi;
    setMouseCursor (hover == Hit::none ? MouseCursor::NormalCursor
                  : hover == Hit::fader ? MouseCursor::UpDownResizeCursor : MouseCursor::PointingHandCursor);
}

void FogEditor::mouseExit (const MouseEvent&) { hover = Hit::none; hoverFader = -1; }

void FogEditor::mouseDown (const MouseEvent& e)
{
    int fi = -1;
    const auto u = toUnits (e.position);
    const auto h = hitAt (u, fi);
    if (e.mods.isPopupMenu())
    {
        // clic droit sur une commande : son MIDI Learn en tete du menu
        showContextMenu (h == Hit::fader ? fi : h == Hit::dryBtn ? FogProcessor::learnDryFx : h == Hit::qBtn ? FogProcessor::learnQ
                         : h == Hit::knob ? FogProcessor::learnKnob : h == Hit::fsPre ? FogProcessor::learnPresetFs
                         : h == Hit::fsByp ? FogProcessor::learnBypassFs : -1);
        return;
    }
    if (statusAlpha > 0.0f && layout::presetRect.contains (u))
    {   // la ligne d'etat ne bloque pas : un clic fait revenir la barre de presets
        statusUntil = 0.0;
        return;
    }
    dragging = h;
    const double now = Time::getMillisecondCounterHiRes();
    switch (h)
    {
        case Hit::fader:
            dragFader = fi; dragStart = u; dragStartV = faderValue (fi);
            proc.apvts.getParameter (FogIDs::faders[fi])->beginChangeGesture();
            flash (String (FogIDs::faderNames[fi]) + "  " + faderText (fi, dragStartV));
            break;
        case Hit::dryBtn:
            dryDown = true; dryUpAt = 0.0; repaint();
            cycleParam (FogIDs::dryFx, "DRY FX", { dryNames[0], dryNames[1], dryNames[2], dryNames[3] });
            dryUpAt = -(now + 120.0);
            break;
        case Hit::qBtn:
            qDown = true; qUpAt = 0.0; repaint();
            cycleParam (FogIDs::q, "FILTER Q", { qNames[0], qNames[1], qNames[2], qNames[3] });
            qUpAt = -(now + 120.0);
            break;
        case Hit::knob:
            knobDown = true; knobDragged = false; knobSaved = false;
            knobDownTime = Time::getMillisecondCounter();
            knobLast = u; knobAcc = 0.0f; knobTravel = 0.0f;
            break;
        case Hit::fsPre: fsPreDown = true; repaint(); proc.presetFootswitch(); break;
        case Hit::fsByp: fsBypDown = true; repaint(); proc.toggleBypass(); break;
        case Hit::presetPrev: stepPreset (-1); break;
        case Hit::presetNext: stepPreset (1); break;
        case Hit::presetName: showPresetMenu(); break;
        case Hit::none: break;
    }
}

void FogEditor::mouseDrag (const MouseEvent& e)
{
    const auto u = toUnits (e.position);
    if (dragging == Hit::fader && dragFader >= 0)
    {
        // le capuchon suit la souris 1:1 (Maj = 5x plus fin)
        const float range = (layout::travelBot - layout::travelTop) * (e.mods.isShiftDown() ? 5.0f : 1.0f);
        setFader (dragFader, dragStartV - (u.y - dragStart.y) / range, true);
    }
    else if (dragging == Hit::knob && knobDown)
    {
        const float d = (u.x - knobLast.x) - (u.y - knobLast.y);        // droite / haut = sens horaire
        knobLast = u;
        knobTravel += std::abs (d);
        if (! knobDragged && knobTravel > 4.0f) knobDragged = true;
        if (! knobDragged) return;
        knobAcc += d;
        const int sel = proc.getSelected();
        // un cran retient le bouton jusqu'a ce que la souris l'ait vraiment pousse ; le preset se charge aussitot
        if (knobAcc >= knobStep && sel < 7)       { proc.loadPreset (sel + 1); knobAcc = 0.0f; }
        else if (knobAcc <= -knobStep && sel > 0) { proc.loadPreset (sel - 1); knobAcc = 0.0f; }
        if ((sel == 7 && knobAcc > 0) || (sel == 0 && knobAcc < 0)) knobAcc = jlimit (-knobStep * 0.3f, knobStep * 0.3f, knobAcc);
    }
}

void FogEditor::mouseUp (const MouseEvent&)
{
    if (dragging == Hit::fader && dragFader >= 0)
        proc.apvts.getParameter (FogIDs::faders[dragFader])->endChangeGesture();
    if (dragging == Hit::knob && knobDown)
    {
        if (! knobDragged && ! knobSaved && Time::getMillisecondCounter() - knobDownTime < 2000)
            proc.loadPreset (proc.getSelected());                      // clic = recharger
        knobDown = false; knobDragged = false; knobAcc = 0.0f;
    }
    // boutons : relaches 120 ms au moins apres l'appui
    const double now = Time::getMillisecondCounterHiRes();
    if (dryUpAt < 0.0) dryUpAt = jmax (now, -dryUpAt);
    if (qUpAt < 0.0)   qUpAt = jmax (now, -qUpAt);
    if (fsPreDown || fsBypDown)
    {
        fsPreDown = fsBypDown = false;
        askRepaint (Rectangle<float> (layout::fsBtnR * 2.2f, layout::fsBtnR * 2.2f).withCentre (layout::fsPre));
        askRepaint (Rectangle<float> (layout::fsBtnR * 2.2f, layout::fsBtnR * 2.2f).withCentre (layout::fsByp));
    }
    dragging = Hit::none; dragFader = -1;
}

void FogEditor::mouseDoubleClick (const MouseEvent& e)
{
    int fi = -1;
    if (hitAt (toUnits (e.position), fi) == Hit::fader && fi >= 0)
        setFader (fi, proc.apvts.getParameter (FogIDs::faders[fi])->getDefaultValue(), false);
}

void FogEditor::mouseWheelMove (const MouseEvent& e, const MouseWheelDetails& w)
{
    int fi = -1;
    const auto h = hitAt (toUnits (e.position), fi);
    const float step = (std::abs (w.deltaY) > 1.0e-6f ? w.deltaY : -w.deltaX) * (w.isReversed ? -1.0f : 1.0f);
    if (h == Hit::fader && fi >= 0) setFader (fi, faderValue (fi) + step * (e.mods.isShiftDown() ? 0.01f : 0.04f), false);
    else if (h == Hit::knob)
    {
        const auto now = Time::getMillisecondCounter();
        wheelAcc += step;
        if (std::abs (wheelAcc) >= 0.10f && now - knobClickTime > 110)         // un cran par cran de molette
        {
            const int dir = wheelAcc > 0 ? 1 : -1; wheelAcc = 0;
            const int sel = jlimit (0, 7, proc.getSelected() + dir);
            if (sel != proc.getSelected()) { proc.loadPreset (sel); knobClickTime = now; }
        }
    }
}

//==============================================================================
// Presets
//==============================================================================
void FogEditor::stepPreset (int delta)
{
    const int l = proc.getLoaded();
    const int base = l >= 0 ? l : proc.getSelected();
    proc.loadPreset ((base + delta + 8) % 8);
}

void FogEditor::showPresetMenu()
{
    PopupMenu m;
    m.setLookAndFeel (&menuLnf);
    NineHandsMenu::addHeader (m, menuLnf.f, NineHandsMenu::icoPreset, menuAccent, "Presets", proc.presetLine());
    const auto& list = getFactoryPresets();
    m.addSectionHeader ("Pedal presets (knob 1-8)");
    for (int i = 0; i < 8; ++i)
        m.addItem (1 + i, "Preset " + String (i + 1) + "  " + String (list[(size_t) i].name), true, proc.getLoaded() == i);
    m.addSeparator();
    PopupMenu fac;
    for (int i = 0; i < (int) list.size(); ++i) fac.addItem (200 + i, String (i + 1) + ". " + list[(size_t) i].name, true, proc.lastFactory.load() == i);
    m.addSubMenu ("Factory sounds", fac);
    PopupMenu save;
    for (int i = 0; i < 8; ++i) save.addItem (100 + i, "Save to preset " + String (i + 1));
    m.addSubMenu ("Save current sound", save);
    m.addItem (300, "Restore factory sounds in presets 1-8");
    const auto area = layout::presetRect.transformedBy (AffineTransform::scale (k())).getSmallestIntegerContainer();
    m.showMenuAsync (PopupMenu::Options().withTargetScreenArea (localAreaToGlobal (area)),
        [safe = Component::SafePointer<FogEditor> (this)] (int r)
        {
            if (safe == nullptr || r == 0) return;
            auto& pr = safe->proc;
            if (r >= 1 && r <= 8) pr.loadPreset (r - 1);
            else if (r >= 100 && r < 108) { pr.savePreset (r - 100); safe->flash ("Saved to preset " + String (r - 99)); }
            else if (r >= 200 && r < 300) pr.applyFactory (r - 200);
            else if (r == 300) { pr.restoreFactorySlots(); safe->flash ("Factory sounds restored in presets 1-8"); }
        });
}

//==============================================================================
// Menu clic droit (design d'Octopus, NineHandsMenu.h), toujours ouvert a l'endroit du clic
//==============================================================================
void FogEditor::showContextMenu (int learnIdx)
{
    using namespace NineHandsMenu;
    PopupMenu menu;
    menu.setLookAndFeel (&menuLnf);
    auto ccText = [this] (int i) { const int cc = proc.ccMap[i].load(); return cc >= 0 ? "CC " + String (cc) : String ("not assigned"); };
    const int lt = proc.learnTarget.load();
    if (learnIdx >= 0)
    {
        const String name = FogProcessor::learnDef (learnIdx).name;
        const int ico = learnIdx < 8 ? icoKnob : (learnIdx == FogProcessor::learnPresetFs || learnIdx == FogProcessor::learnBypassFs) ? icoPedal
                      : learnIdx == FogProcessor::learnKnob ? icoPreset : icoSwitch;
        addHeader (menu, menuLnf.f, ico, menuAccent, name, "MIDI: " + ccText (learnIdx));
        menu.addItem (1000 + learnIdx, "MIDI Learn: " + name, true, lt == learnIdx);
        menu.addItem (1100 + learnIdx, "Clear MIDI: " + name, proc.ccMap[learnIdx].load() >= 0);
        if (lt >= 0) menu.addItem (1200, "Cancel MIDI learn");
        menu.addSeparator();
    }
    else
        addHeader (menu, menuLnf.f, icoPedal, menuAccent, "Fog Z", "Polyphonic octaves  v" + String (JucePlugin_VersionString));

    PopupMenu sizes, defSizes;
    {
        const char* names[numSizes] = { "60 %", "75 %", "100 %" };
        const int def = WigaWindowSize::defaultIndex (JucePlugin_Name, numSizes);
        for (int i = 0; i < numSizes; ++i)
        {
            sizes.addItem (1 + i, String (names[i]) + (i == def ? "  (default)" : ""), true, std::abs (getHeight() - sizeHeight (i)) <= 2);
            defSizes.addItem (20 + i, names[i], true, i == def);
        }
        sizes.addSeparator();
        sizes.addSubMenu ("Default size (new windows)", defSizes);
    }
    menu.addSubMenu ("Plugin size", sizes);
    PopupMenu glowM;                   // reglage du halo des lumieres (regle des skills, nov. 2026)
    {
        const int now = roundToInt (glow * 100.0f);
        for (int i = 0; i < NineHandsGlow::numSteps; ++i)
        {
            const int pc = NineHandsGlow::steps[i];
            glowM.addItem (60 + i, "Glow " + String (pc) + " %" + (pc == 100 ? "  (default)" : ""), true, now == pc);
        }
    }
    menu.addSubMenu ("Glow (halo of the lights)", glowM);
    menu.addSeparator();

    const auto& list = getFactoryPresets();
    PopupMenu fac;
    for (int i = 0; i < (int) list.size(); ++i) fac.addItem (200 + i, String (i + 1) + ". " + list[(size_t) i].name, true, proc.lastFactory.load() == i);
    menu.addSubMenu ("Factory sounds", fac);
    menu.addItem (300, "Restore factory sounds in presets 1-8");
    menu.addSeparator();

    PopupMenu midi;
    midi.addSectionHeader ("MIDI Learn");
    for (int i = 0; i < FogProcessor::numLearn; ++i)
        midi.addItem (1000 + i, "Learn: " + String (FogProcessor::learnDef (i).name) + "  (" + ccText (i) + ")", true, lt == i);
    midi.addSeparator();
    if (lt >= 0) midi.addItem (1200, "Cancel MIDI learn");
    midi.addItem (1201, "Clear all MIDI assignments");
    midi.addSeparator();
    midi.addItem (403, "Latching MIDI pedals (127 / 0 on each press)", true, proc.latchingPedals.load());
    midi.addItem (404, "Program Change 1-8 loads presets 1-8", false);
    menu.addSubMenu ("MIDI", midi);
    menu.addSeparator();
    menu.addItem (999, "Fog Z v" + String (JucePlugin_VersionString) + "  NINE HANDS | DSP", false);

    menu.showMenuAsync (PopupMenu::Options().withMousePosition(),       // toujours la ou l'on clique
        [safe = Component::SafePointer<FogEditor> (this)] (int r)
        {
            if (safe == nullptr || r == 0) return;
            auto& ed = *safe;
            auto& pr = ed.proc;
            if      (r >= 1 && r < 1 + numSizes) ed.setWindowHeight (sizeHeight (r - 1));
            else if (r >= 20 && r < 20 + numSizes)
            {
                WigaWindowSize::setDefaultIndex (JucePlugin_Name, r - 20);   // toutes les nouvelles fenetres de ce plugin
                ed.setWindowHeight (sizeHeight (r - 20));
            }
            else if (r >= 60 && r < 60 + NineHandsGlow::numSteps)
            {
                ed.setGlowPercent (NineHandsGlow::steps[r - 60]);
                ed.flash ("Glow  " + String (NineHandsGlow::steps[r - 60]) + " %");
            }
            else if (r >= 200 && r < 300) pr.applyFactory (r - 200);
            else if (r == 300) { pr.restoreFactorySlots(); ed.flash ("Factory sounds restored in presets 1-8"); }
            else if (r == 403) pr.latchingPedals = ! pr.latchingPedals.load();
            else if (r >= 1000 && r < 1000 + FogProcessor::numLearn)
            {
                const int t = r - 1000;
                pr.learnTarget.store (pr.learnTarget.load() == t ? -1 : t);       // re-cliquer annule
            }
            else if (r >= 1100 && r < 1100 + FogProcessor::numLearn)
            {
                pr.ccMap[r - 1100].store (-1);
                ed.flash (String (FogProcessor::learnDef (r - 1100).name) + "  MIDI cleared");
            }
            else if (r == 1200) pr.learnTarget.store (-1);
            else if (r == 1201) { pr.learnTarget.store (-1); pr.clearMidiMap(); ed.flash ("All MIDI cleared"); }
        });
}

void FogEditor::showMenuForCapture (int which)
{
    if (which == 0) showContextMenu (-1);
    else if (which == 1) showContextMenu (FogProcessor::learnKnob);
    else showPresetMenu();
}
