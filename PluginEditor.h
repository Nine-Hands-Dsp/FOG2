#pragma once
#include <juce_gui_basics/juce_gui_basics.h>
#include <juce_audio_processors/juce_audio_processors.h>
#include "PluginProcessor.h"
#include "Layout.h"
#include "NineHandsMenu.h"
#include "NineHandsWindow.h"

//==============================================================================
// FOG Z v2 (NINE HANDS | DSP) : pedale double, fond 2266 x 1800 px plein cadre (repere 1133 x 900, Layout.h).
// Le fond contient le boitier, les fentes, les boutons DRY FX / Q relaches, les LED eteintes, les footswitches
// et les jacks (pieces photo), avec leurs ombres et leur occlusion. L'editeur dessine par-dessus :
// serigraphie vectorielle (silk.svg + textes Poppins), logo NINE HANDS | DSP, capuchons des faders,
// boutons enfonces, LED allumees et leurs halos (doses par le reglage Glow), gros bouton PRESET en calques
// (rotation + flou de mouvement, reflets fixes), pastille presets / ligne d'etat.
//==============================================================================
class FogEditor : public juce::AudioProcessorEditor,
                  private juce::Timer
{
public:
    explicit FogEditor (FogProcessor&);
    ~FogEditor() override;

    void paint (juce::Graphics&) override;
    void resized() override;
    void parentHierarchyChanged() override;

    void mouseDown (const juce::MouseEvent&) override;
    void mouseDrag (const juce::MouseEvent&) override;
    void mouseUp (const juce::MouseEvent&) override;
    void mouseDoubleClick (const juce::MouseEvent&) override;
    void mouseMove (const juce::MouseEvent&) override;
    void mouseExit (const juce::MouseEvent&) override;
    void mouseWheelMove (const juce::MouseEvent&, const juce::MouseWheelDetails&) override;

    static constexpr float baseW = layout::frameW, baseH = layout::frameH;
    static constexpr int heightDefault = 495, heightMax = 1123;      // « 60 % » = taille minimale (hauteur de Ring Think)
    static constexpr int numSizes = 3;                               // 60 % (defaut) / 75 % / 100 %
    static int sizeHeight (int idx);
    void setWindowHeight (int h);
    void setGlowPercent (int pc);
    void flash (const juce::String& text, double seconds = 2.5);

    // outil de rendu (captures)
    void forceRenderScale (float sc) { forcedScale = sc; rebuildCaches (sc); }
    void settleForCapture();
    void setGlowForCapture (float g) { glow = g; repaint(); }
    void pressForCapture (int what, bool down);       // 0 = DRY FX, 1 = Q, 2 = footswitch PRESET, 3 = footswitch BYPASS
    void showMenuForCapture (int which);              // 0 = menu principal, 1 = menu d'une commande, 2 = menu presets

private:
    void timerCallback() override;
    void visibilityChanged() override;
    void useSoftwareRenderer();
    float physicalScale() const;
    void askRepaint (juce::Rectangle<float> unitsRect);
    void rebuildCaches (float sc = 0.0f);
    void renderKnob();
    float k() const { return (float) getHeight() / baseH; }
    juce::Point<float> toUnits (juce::Point<float> p) const { return p / k(); }

    enum class Hit { none, fader, dryBtn, qBtn, knob, fsPre, fsByp, presetPrev, presetName, presetNext };
    Hit hitAt (juce::Point<float> u, int& faderIdx) const;
    float faderY (int i) const;
    juce::Rectangle<float> faderArea (int i) const;
    float faderValue (int i) const;
    void setFader (int i, float v01, bool inGesture);
    void cycleParam (const char* id, const juce::String& label, const juce::StringArray& names);
    juce::String faderText (int i, float v) const;

public:
    juce::PopupMenu buildContextMenu (int learnIdx = -1);   // menu clic droit (aussi pour l'outil de controle des menus)
private:
    void showContextMenu (int learnIdx = -1);
    void showPresetMenu();
    void stepPreset (int delta);

    void drawPrint (juce::Graphics&);
    void drawLeds (juce::Graphics&);
    void drawBar (juce::Graphics&);

    FogProcessor& proc;
    NineHandsMenu::MenuLnf menuLnf;
    NineHandsWindow::HostLock hostLock;    // fenetre du DAW : jamais sous 60 %, jamais au-dela de 150 %
    juce::Typeface::Ptr regularFace, mediumFace, boldFace;
    std::unique_ptr<juce::Drawable> silk, logo;
    juce::Path textPath;                               // textes de la serigraphie (unites)
    float capHeightRatio = 0.7f;                       // hauteur des capitales / taille de la police (Poppins Medium)

    juce::Image background, bgScaled, capImg, btnDown, lensRed, lensAmber, lensGreen, haloRed, haloAmber, haloGreen,
                domeAmber, haloDome;
    juce::Image knobShadow, knobStack, knobHighlight, knobFrame, knobScratch;   // gros bouton : calques prets a la bonne taille
    juce::Image knobLayers[5];                          // shadow, crown, cap, marker, highlight (512 px)
    int cacheW = 0, cacheH = 0;
    float cacheScale = 0.0f, forcedScale = 0.0f;
    int resizeSettle = 0, openHeight = 0;
    void* lastPeer = nullptr;
    double lastPaintMs = 0.0, repaintAskedMs = 0.0, lastScaleCheckMs = 0.0, lastRendererCheckMs = 0.0, lastGlowReadMs = 0.0;

    // ---- etat
    float glow = 1.0f;
    Hit dragging = Hit::none, hover = Hit::none;
    int dragFader = -1, hoverFader = -1;
    float dragStartV = 0.0f; juce::Point<float> dragStart;
    bool dryDown = false, qDown = false, fsPreDown = false, fsBypDown = false;
    double dryUpAt = 0.0, qUpAt = 0.0;

    // gros bouton PRESET : rotation par crans, flou de mouvement
    float knobAngle = 0.0f, knobTarget = 0.0f, knobBlur = 0.0f, knobBlurDir = 1.0f, drawnKnobAngle = 1.0e9f, drawnKnobBlur = -1.0f;
    int knobSnapStep = 0;
    bool knobDown = false, knobDragged = false, knobSaved = false;
    juce::uint32 knobDownTime = 0, knobClickTime = 0;
    float knobAcc = 0.0f, knobTravel = 0.0f, wheelAcc = 0.0f;
    juce::Point<float> knobLast;
    bool knobHoldBlinking() const;

    // LED (etat affiche)
    struct LedState
    {
        int dryFx = 0, q = 0, sel = 0; bool pre = false, byp = false, presetBlink = false, presetBlinkOn = false;
        bool operator!= (const LedState& o) const
        { return dryFx != o.dryFx || q != o.q || sel != o.sel || pre != o.pre || byp != o.byp || presetBlink != o.presetBlink || presetBlinkOn != o.presetBlinkOn; }
    } leds, drawnLeds;

    // pastille unique : barre de presets au repos, ligne d'etat pendant les reglages
    juce::String statusText, presetText;
    double statusUntil = 0.0;
    float statusAlpha = 0.0f;
    float lastVals[8] {};
    int lastDryFx = -1, lastQ = -1; bool lastByp = false; int lastLoaded = -2, lastFactory = -2;
    float dStatus = -1.0f; juce::String dStatusText, dPresetText; Hit dHover = Hit::none;
    float drawnFader[8];

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (FogEditor)
};
