// genere par tools/make_layout.py (Fog Z v2) - ne pas modifier a la main
// repere 1133 x 900 unites = fond 2266 x 1800 px / 2 (format double, pedale plein cadre, jacks contre les bords)
#pragma once
#include <juce_graphics/juce_graphics.h>
namespace layout
{
    constexpr float frameW = 1133.0f, frameH = 900.0f;
    const float faderX[8] = { 132.61f, 229.34f, 326.08f, 422.15f, 519.54f, 711.04f, 805.16f, 901.24f };
    constexpr float travelTop = 181.70f, travelBot = 431.63f;   // centre du capuchon sur la ligne la plus haute / basse
    constexpr float capW = 29.00f, capH = 51.00f, capSprW = 53.00f, capSprH = 75.00f;   // sprite = capuchon + ombre
    const juce::Point<float> dryBtn { 614.64f, 231.37f }, qBtn { 614.64f, 427.45f }; constexpr float btnS = 79.50f, btnHitR = 33.39f;
    const juce::Point<float> dryLed { 614.64f, 153.92f }, qLed { 614.64f, 344.77f }, preLed { 417.91f, 741.18f }, bypLed { 718.56f, 740.52f };
    constexpr float ledLensS = 38.00f, ledFsS = 29.50f, ledDomeS = 26.00f;   // diametres ; halo = 3 x
    const juce::Point<float> presetLed[8] = { { 1016.60f, 226.80f }, { 1016.60f, 264.71f }, { 1016.60f, 302.61f }, { 1016.60f, 340.52f }, { 1016.60f, 378.43f }, { 1016.60f, 416.34f }, { 1016.60f, 454.25f }, { 1016.60f, 492.16f } };
    const juce::Point<float> fsPre { 223.46f, 763.40f }, fsByp { 916.27f, 763.40f }; constexpr float fsBtnR = 37.14f, fsHitR = 49.02f;
    const juce::Point<float> knobPos { 1017.00f, 137.25f }; constexpr float knobS = 150.50f, knobR = 62.00f;   // calques 512 px, cadre knobS
    const juce::Rectangle<float> presetRect { 366.50f, 777.00f, 400.00f, 38.00f };   // pastille unique : barre de presets / ligne d'etat (400 x 38)
    constexpr float presetFont = 23.0f;
    const juce::Point<float> logoPos { 566.50f, 848.37f }; constexpr float logoW = 210.00f;
    // serigraphie : textes en Poppins Bold (taille em en unites), centres sur (x, y), rotation 90 = se lit de bas en haut
    struct Txt { const char* s; float em, x, y, rot; };
    const Txt texts[] = {
        { "DRY OUTPUT", 22.50f, 106.79f, 306.54f, 90.00f },
        { "-2 OCTAVES", 22.50f, 203.20f, 308.82f, 90.00f },
        { "-1 OCTAVE", 22.50f, 298.62f, 309.80f, 90.00f },
        { "+1 OCTAVE", 22.50f, 394.05f, 307.52f, 90.00f },
        { "+2 OCTAVES", 22.50f, 491.43f, 308.17f, 90.00f },
        { "ATTACK", 20.50f, 751.57f, 310.46f, 90.00f },
        { "LP FILTER", 22.50f, 846.34f, 310.13f, 90.00f },
        { "DETUNE", 22.50f, 942.74f, 310.78f, 90.00f },
        { "DRY FX", 23.00f, 614.64f, 296.42f, 0.00f },
        { "Q", 22.50f, 614.64f, 489.88f, 0.00f },
        { "VOICE MIX", 24.25f, 314.31f, 487.58f, 0.00f },
        { "EFFECTS", 23.50f, 823.13f, 490.20f, 0.00f },
        { "HOLD TO SAVE PRESETS", 19.50f, 1052.22f, 370.92f, 90.00f },
        { "OUTPUT", 22.50f, 80.00f, 611.76f, 90.00f },
        { "INPUT", 20.50f, 1063.66f, 603.59f, 90.00f },
        { "PRESET", 22.00f, 223.46f, 847.71f, 0.00f },
        { "BYPASS", 22.00f, 917.58f, 849.02f, 0.00f },
        { "1", 21.50f, 989.15f, 226.80f, 0.00f },
        { "2", 21.50f, 989.15f, 264.71f, 0.00f },
        { "3", 21.50f, 989.15f, 302.61f, 0.00f },
        { "4", 21.50f, 989.15f, 340.52f, 0.00f },
        { "5", 21.50f, 989.15f, 378.43f, 0.00f },
        { "6", 21.50f, 989.15f, 416.34f, 0.00f },
        { "7", 21.50f, 989.15f, 454.25f, 0.00f },
        { "8", 21.50f, 989.15f, 492.16f, 0.00f }
    };
}
