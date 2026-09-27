<template>
  <v-container fluid class="pa-6">

    <v-row justify="center">
      <v-col cols="12" md="6">
        <v-card color="surface" rounded="lg">
          <v-card-title class="pa-4 text-body-1 font-weight-bold">
            <v-icon class="mr-2" color="primary">mdi-tune</v-icon>
            Detection Thresholds
          </v-card-title>
          <v-divider />
          <v-card-text class="pa-6">

            <div class="mb-6">
              <div class="d-flex justify-space-between mb-2">
                <span class="text-body-2">Turbidity Threshold</span>
                <span class="text-primary font-weight-bold">{{ localTurbidity }} NTU</span>
              </div>
              <v-slider
                v-model="localTurbidity"
                :min="5"
                :max="200"
                :step="1"
                color="primary"
                track-color="grey-darken-3"
                thumb-label
              />
              <div class="text-caption text-medium-emphasis">
                Diverter activates when turbidity exceeds this value. WHO drinking water guideline is 4 NTU; first-flush events typically reach 50-150 NTU.
              </div>
            </div>

            <v-divider class="mb-6" />

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
                Elevated conductivity indicates dissolved salts and pollutants. Background urban stormwater is typically 200-600 ppm.
              </div>
            </div>

            <v-alert
              v-if="saved"
              type="success"
              variant="tonal"
              density="compact"
              class="mb-4"
            >
              {{ savedMessage }}
            </v-alert>

            <div class="d-flex gap-3">
              <v-btn
                color="primary"
                class="flex-grow-1"
                :loading="saving"
                @click="saveThresholds"
              >
                Apply Thresholds
              </v-btn>
              <v-btn
                color="grey"
                variant="tonal"
                :loading="resetting"
                @click="resetThresholds"
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
      localTurbidity: 50,
      localConductivity: 800,
      saving: false,
      resetting: false,
      saved: false,
      savedMessage: '',
    }
  },

  mounted() {
    this.fetchThresholds()
  },

  methods: {
    async fetchThresholds() {
      try {
        const res = await axios.get(`${API_BASE}/api/thresholds`)
        this.localTurbidity = res.data.turbidity
        this.localConductivity = res.data.conductivity
      } catch (e) {
        console.error('failed to fetch thresholds', e)
      }
    },

    async saveThresholds() {
      this.saving = true
      this.saved = false
      try {
        await axios.post(
          `${API_BASE}/api/thresholds?turbidity=${this.localTurbidity}&conductivity=${this.localConductivity}`
        )
        this.savedMessage = 'Thresholds updated successfully.'
        this.saved = true
        setTimeout(() => { this.saved = false }, 3000)
      } catch (e) {
        console.error('failed to save thresholds', e)
      } finally {
        this.saving = false
      }
    },

    async resetThresholds() {
      this.resetting = true
      this.saved = false
      try {
        const res = await axios.post(`${API_BASE}/api/thresholds/reset`)
        this.localTurbidity = res.data.turbidity
        this.localConductivity = res.data.conductivity
        this.savedMessage = 'Thresholds reset to default values.'
        this.saved = true
        setTimeout(() => { this.saved = false }, 3000)
      } catch (e) {
        console.error('failed to reset thresholds', e)
      } finally {
        this.resetting = false
      }
    }
  }
}
</script>
