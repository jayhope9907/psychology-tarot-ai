/**
 * NeurodevelopmentalCognitiveMatrix
 *
 * Non-diagnostic wellness indicator derived from the UnifiedEmotionalSpectrumEngine.
 * Backend source: `app/services/emotional_spectrum.py` → `to_neurodevelopmental_matrix()`
 * SSE key: `neurodevelopmental_matrix` (in the `done` event payload)
 */
export interface NeurodevelopmentalCognitiveMatrix {
  cognitive_disorganization_score: number; // 0 - 100

  spectrum_mapping: {
    // ASD Factors
    social_blindness: number;   // word-card avoidance rate
    rigid_fixation: number;     // same pattern/topic repetition

    // Schizotypy Factors
    cognitive_fragmentation: number; // mindmap disorganization
    reality_detachment: number;      // context drift
  };

  three_d_room_fx: {
    wall_texture: 'rigid-grid' | 'wireframe-dissolve' | 'isolated-island';
    sound_muffling_factor: number; // 0.0 ~ 1.0
  };
}
