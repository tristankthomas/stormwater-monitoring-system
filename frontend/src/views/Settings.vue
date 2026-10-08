<template>
  <v-container fluid class="pa-6">

    <v-row justify="center">

      <!-- conductivity threshold -->
      <v-col cols="12" md="5">
        <v-card color="surface" rounded="lg" height="100%">
          <v-card-title class="pa-4 text-body-1 font-weight-bold">
            <v-icon class="mr-2" color="primary">mdi-tune</v-icon>
            Sensor Threshold
          </v-card-title>
          <v-divider />
          <v-card-text class="pa-6">

            <div class="mb-6">
              <div class="d-flex justify-space-between mb-2">
                <span class="text-body-2">Conductivity Threshold</span>
                <span class="text-primary font-weight-bold">{{ localConductivity }} ppm</span>
              </div>
              <v-slider
                v-model="localConductivity"
                :min="100"
                :max="2000"
                :step="10"
                color="primary"
                track-color="grey-darken-3"
                thumb-label
              />
              <div class="text-caption text-medium-emphasis">
                Diverter activates when conductivity exceeds this value. Elevated conductivity indicates dissolved salts and pollutants. Background urban stormwater is typically 200-600 ppm.
              </div>
            </div>

            <v-alert
              v-if="sensorSaved"
              type="success"
              variant="tonal"
              density="compact"
              class="mb-4"
            >
              {{ sensorMessage }}
            </v-alert>

            <div class="d-flex gap-3">
              <v-btn
                color="primary"
                class="flex-grow-1"
                :loading="sensorSaving"
                @click="saveSensor"
              >
                Apply Threshold
              </v-btn>
              <v-btn
                color="grey"
                variant="tonal"
                :loading="sensorResetting"
                @click="resetSensor"
              >
                Reset to Default
              </v-btn>
            </div>

          </v-card-text>
        </v-card>
      </v-col>

      <!-- camera thresholds -->
      <v-col cols="12" md="7">
        <v-card color="surface" rounded="lg" height="100%">
          <v-card-title class="pa-4 text-body-1 font-weight-bold">
            <v-icon class="mr-2" color="primary">mdi-camera-iris</v-icon>
            Camera Analysis Thresholds
          </v-card-title>
          <v-divider />
          <v-card-text class="pa-6">

            <!-- live readout so the cutoffs can be set against what the camera actually sees -->
            <div class="d-flex align-center justify-space-between mb-6">
              <div>
                <div class="text-medium-emphasis text-caption">Current brightness</div>
                <div class="text-h5 font-weight-bold">
                  {{ analysis.available ? analysis.brightness : '—' }}
                </div>
              </div>
              <v-chip :color="classColor" variant="tonal">
                {{ analysis.available ? analysis.turbidity_class?.toUpperCase() : 'NO CAMERA' }}
              </v-chip>
            </div>

            <div class="mb-6">
              <div class="d-flex justify-space-between mb-2">
                <span class="text-body-2">Clear above (brightness)</span>
                <span class="text-primary font-weight-bold">{{ localClear }}</span>
              </div>
              <v-slider
                v-model="localClear"
                :min="0"
                :max="255"
                :step="1"
                color="primary"
                track-color="grey-darken-3"
                thumb-label
              />
              <div class="text-caption text-medium-emphasis">
                Frames brighter than this are classed as clear water.
              </div>
            </div>

            <div class="mb-6">
              <div class="d-flex justify-space-between mb-2">
                <span class="text-body-2">High turbidity below (brightness)</span>
                <span class="text-primary font-weight-bold">{{ localTurbid }}</span>
              </div>
              <v-slider
                v-model="localTurbid"
                :min="0"
                :max="255"
                :step="1"
                color="primary"
                track-color="grey-darken-3"
                thumb-label
              />
              <div class="text-caption text-medium-emphasis">
                Frames darker than this are classed as high turbidity and activate the diverter. Between the two values the water is moderate.
              </div>
            </div>

            <div class="mb-6">
              <div class="d-flex justify-space-between mb-2">
                <span class="text-body-2">Debris minimum area</span>
                <span class="text-primary font-weight-bold">{{ localDebris }} px</span>
              </div>
              <v-slider
                v-model="localDebris"
                :min="50"
                :max="5000"
                :step="50"
                color="primary"
                track-color="grey-darken-3"
                thumb-label
              />
              <div class="text-caption text-medium-emphasis">
                Contours smaller than this are ignored as noise.
              </div>
            </div>

            <v-alert
              v-if="cameraInvalid"
              type="warning"
              variant="tonal"
              density="compact"
              class="mb-4"
            >
              The high turbidity value must be below the clear value.
            </v-alert>

            <v-alert
              v-if="cameraSaved"
              type="success"
              variant="tonal"
              density="compact"
              class="mb-4"
            >
              {{ cameraMessage }}
            </v-alert>

            <div class="d-flex gap-3">
              <v-btn
                color="primary"
                class="flex-grow-1"
                :loading="cameraSaving"
                :disabled="cameraInvalid"
                @click="saveCamera"
              >
                Apply Thresholds
              </v-btn>
              <v-btn
                color="grey"
                variant="tonal"
                :loading="cameraResetting"
                @click="resetCamera"
              >
                Reset to Default
              </v-btn>
            </div>

          </v-card-text>
        </v-card>
      </v-col>

    </v-row>

  </v-container>
</template>

<script>
import axios from 'axios'

// use relative paths so this works whether served from localhost or the pi's ip
const API_BASE = ''

export default {
  name: 'Settings',

  data() {
    return {
      localConductivity: 800,
      sensorSaving: false,
      sensorResetting: false,
      sensorSaved: false,
      sensorMessage: '',

      localClear: 100,
      localTurbid: 60,
      localDebris: 500,
      cameraSaving: false,
      cameraResetting: false,
      cameraSaved: false,
      cameraMessage: '',

      analysis: { available: false, brightness: null, turbidity_class: null },
      analysisInterval: null,
    }
  },

  computed: {
    cameraInvalid() {
      return this.localTurbid >= this.localClear
    },

    classColor() {
      const map = { clear: 'success', moderate: 'warning', high: 'error' }
      return map[this.analysis.turbidity_class] ?? 'grey'
    }
  },

  mounted() {
    this.fetchThresholds()
    this.fetchCameraThresholds()
    this.fetchAnalysis()
    this.analysisInterval = setInterval(this.fetchAnalysis, 2000)
  },

  beforeUnmount() {
    clearInterval(this.analysisInterval)
  },

  methods: {
    async fetchThresholds() {
      try {
        const res = await axios.get(`${API_BASE}/api/thresholds`)
        this.localConductivity = res.data.conductivity
      } catch (e) {
        console.error('failed to fetch thresholds', e)
      }
    },

    async fetchCameraThresholds() {
      try {
        const res = await axios.get(`${API_BASE}/api/camera/thresholds`)
        this.localClear = res.data.clear_brightness
        this.localTurbid = res.data.turbid_brightness
        this.localDebris = res.data.debris_min_area
      } catch (e) {
        console.error('failed to fetch camera thresholds', e)
      }
    },

    async fetchAnalysis() {
      try {
        const res = await axios.get(`${API_BASE}/api/camera/analysis`)
        this.analysis = res.data
      } catch (e) {
        console.error('failed to fetch camera analysis', e)
      }
    },

    async saveSensor() {
      this.sensorSaving = true
      this.sensorSaved = false
      try {
        await axios.post(`${API_BASE}/api/thresholds?conductivity=${this.localConductivity}`)
        this.sensorMessage = 'Threshold updated successfully.'
        this.sensorSaved = true
        setTimeout(() => { this.sensorSaved = false }, 3000)
      } catch (e) {
        console.error('failed to save threshold', e)
      } finally {
        this.sensorSaving = false
      }
    },

    async resetSensor() {
      this.sensorResetting = true
      this.sensorSaved = false
      try {
        const res = await axios.post(`${API_BASE}/api/thresholds/reset`)
        this.localConductivity = res.data.conductivity
        this.sensorMessage = 'Threshold reset to default value.'
        this.sensorSaved = true
        setTimeout(() => { this.sensorSaved = false }, 3000)
      } catch (e) {
        console.error('failed to reset threshold', e)
      } finally {
        this.sensorResetting = false
      }
    },

    async saveCamera() {
      this.cameraSaving = true
      this.cameraSaved = false
      try {
        await axios.post(
          `${API_BASE}/api/camera/thresholds?clear_brightness=${this.localClear}&turbid_brightness=${this.localTurbid}&debris_min_area=${this.localDebris}`
        )
        this.cameraMessage = 'Camera thresholds updated successfully.'
        this.cameraSaved = true
        setTimeout(() => { this.cameraSaved = false }, 3000)
      } catch (e) {
        console.error('failed to save camera thresholds', e)
      } finally {
        this.cameraSaving = false
      }
    },

    async resetCamera() {
      this.cameraResetting = true
      this.cameraSaved = false
      try {
        const res = await axios.post(`${API_BASE}/api/camera/thresholds/reset`)
        this.localClear = res.data.clear_brightness
        this.localTurbid = res.data.turbid_brightness
        this.localDebris = res.data.debris_min_area
        this.cameraMessage = 'Camera thresholds reset to default values.'
        this.cameraSaved = true
        setTimeout(() => { this.cameraSaved = false }, 3000)
      } catch (e) {
        console.error('failed to reset camera thresholds', e)
      } finally {
        this.cameraResetting = false
      }
    }
  }
}
</script>