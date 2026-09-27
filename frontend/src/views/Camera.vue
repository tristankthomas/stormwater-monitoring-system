<template>
  <v-container fluid class="pa-6">

    <v-row>
      <v-col cols="12" md="8">
        <v-card color="surface" rounded="lg">
          <v-card-title class="pa-4 text-body-1 font-weight-bold">
            <v-icon class="mr-2" color="primary">mdi-camera</v-icon>
            Live Camera Feed
          </v-card-title>
          <v-divider />
          <v-card-text class="d-flex align-center justify-center" style="height: 400px; padding: 0;">

            <!-- live mjpeg stream when camera is available -->
            <img
              v-if="analysis.available"
              :src="streamUrl"
              style="width: 100%; height: 400px; object-fit: cover;"
              alt="Live camera feed"
            />

            <!-- placeholder when camera is not connected -->
            <div v-else class="text-center">
              <v-icon size="80" color="grey-darken-1">mdi-camera-off</v-icon>
              <div class="text-medium-emphasis mt-4">Camera feed unavailable</div>
              <div class="text-caption text-medium-emphasis mt-1">Connect Raspberry Pi camera module to enable live feed</div>
            </div>

          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="4">
        <v-card color="surface" rounded="lg" height="100%">
          <v-card-title class="pa-4 text-body-1 font-weight-bold">
            <v-icon class="mr-2" color="primary">mdi-eye-check</v-icon>
            Detection Results
          </v-card-title>
          <v-divider />
          <v-card-text>

            <!-- turbidity classification from opencv brightness analysis -->
            <div class="mb-4">
              <div class="text-medium-emphasis text-caption mb-1">Turbidity (Visual)</div>
              <div class="d-flex align-center justify-space-between">
                <span class="text-medium-emphasis text-body-2">
                  Brightness: {{ analysis.brightness ?? '—' }}
                </span>
                <v-chip
                  size="small"
                  :color="turbidityChipColor"
                  variant="tonal"
                >
                  {{ analysis.turbidity_class?.toUpperCase() ?? 'AWAITING FEED' }}
                </v-chip>
              </div>
            </div>

            <v-divider class="mb-4" />

            <!-- debris count from contour detection -->
            <div class="mb-4">
              <div class="text-medium-emphasis text-caption mb-1">Debris Detection</div>
              <div class="d-flex align-center justify-space-between">
                <span class="text-medium-emphasis text-body-2">Floating solids detected</span>
                <v-chip
                  size="small"
                  :color="analysis.debris_count > 0 ? 'warning' : 'success'"
                  variant="tonal"
                >
                  {{ analysis.available ? analysis.debris_count : 'AWAITING FEED' }}
                </v-chip>
              </div>
            </div>

            <v-divider class="mb-4" />

            <div class="text-caption text-medium-emphasis mb-1">Detection method</div>
            <v-list bg-color="transparent" density="compact">
              <v-list-item
                prepend-icon="mdi-water-opacity"
                title="Turbidity"
                subtitle="Average pixel brightness thresholding"
                density="compact"
              />
              <v-list-item
                prepend-icon="mdi-trash-can-outline"
                title="Debris"
                subtitle="Contour detection on water surface"
                density="compact"
              />
            </v-list>

            <v-alert
              v-if="!analysis.available"
              type="info"
              variant="tonal"
              class="mt-4"
              density="compact"
            >
              Camera analysis requires Raspberry Pi with CSI camera module attached.
            </v-alert>

          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

  </v-container>
</template>

<script>
import axios from 'axios'

const API_BASE = 'http://localhost:8000'

export default {
  name: 'Camera',

  data() {
    return {
      streamUrl: `${API_BASE}/api/camera/stream`,
      analysis: {
        available: false,
        turbidity_class: null,
        debris_count: 0,
        brightness: null
      },
      interval: null
    }
  },

  computed: {
    turbidityChipColor() {
      const map = { clear: 'success', moderate: 'warning', high: 'error' }
      return map[this.analysis.turbidity_class] ?? 'grey'
    }
  },

  mounted() {
    this.fetchAnalysis()
    // poll analysis results every 2 seconds to stay in sync with camera loop
    this.interval = setInterval(this.fetchAnalysis, 2000)
  },

  beforeUnmount() {
    clearInterval(this.interval)
  },

  methods: {
    async fetchAnalysis() {
      try {
        const res = await axios.get(`${API_BASE}/api/camera/analysis`)
        this.analysis = res.data
      } catch (e) {
        console.error('failed to fetch camera analysis', e)
      }
    }
  }
}
</script>