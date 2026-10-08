<template>
  <v-container fluid class="pa-6">

    <!-- alert banner shown when diverter is active -->
    <v-alert
      v-if="data.diverter_active"
      type="error"
      prominent
      class="mb-6"
      icon="mdi-alert-circle"
    >
      <strong>Diverter Activated</strong> — pollution threshold exceeded. Stormwater is being diverted.
    </v-alert>

    <!-- top row: pollution score and diverter status -->
    <v-row class="mb-4">
      <v-col cols="12" md="6">
        <v-card color="surface" rounded="lg" height="120">
          <v-card-text class="d-flex align-center h-100">
            <div>
              <div class="text-medium-emphasis text-body-2 mb-1">Pollution Score</div>
              <v-chip
                :color="scoreColor"
                size="x-large"
                class="text-h6 font-weight-bold"
              >
                {{ data.pollution_score?.toUpperCase() ?? '—' }}
              </v-chip>
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="6">
        <v-card color="surface" rounded="lg" height="120">
          <v-card-text class="d-flex align-center h-100">
            <div>
              <div class="text-medium-emphasis text-body-2 mb-1">Diverter Status</div>
              <v-chip
                :color="data.diverter_active ? 'error' : 'success'"
                size="x-large"
                class="text-h6 font-weight-bold"
                :prepend-icon="data.diverter_active ? 'mdi-valve-open' : 'mdi-valve-closed'"
              >
                {{ data.diverter_active ? 'ACTIVE' : 'INACTIVE' }}
              </v-chip>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- sensor cards: conductivity first as the primary quantitative signal, camera clarity as the visual check -->
    <v-row class="mb-4">
      <v-col cols="12" md="7">
        <v-card color="surface" rounded="lg">
          <v-card-text>
            <div class="d-flex align-center justify-space-between mb-2">
              <div class="text-medium-emphasis text-body-2">Conductivity</div>
              <v-chip
                v-if="data.conductivity_source"
                :color="data.conductivity_source === 'sensor' ? 'success' : 'grey'"
                :prepend-icon="data.conductivity_source === 'sensor' ? 'mdi-access-point' : 'mdi-sine-wave'"
                size="x-small"
                label
              >
                {{ data.conductivity_source === 'sensor' ? 'LIVE SENSOR' : 'SIMULATED' }}
              </v-chip>
            </div>
            <div class="text-h2 font-weight-bold" :style="{ color: conductivityColor }">
              {{ data.conductivity ?? '—' }}
            </div>
            <div class="text-medium-emphasis text-body-2">ppm</div>
            <v-progress-linear
              :model-value="conductivityPercent"
              :color="conductivityColor"
              class="mt-4"
              height="8"
              rounded
              bg-color="grey-darken-3"
            />
            <div class="d-flex justify-space-between text-caption text-medium-emphasis mt-1">
              <span>0</span>
              <span>Threshold: {{ thresholds.conductivity }} ppm</span>
              <span>2000</span>
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="5">
        <v-card color="surface" rounded="lg">
          <v-card-text>
            <div class="d-flex align-center justify-space-between mb-2">
              <div class="text-medium-emphasis text-body-2">Water Clarity</div>
              <v-chip
                v-if="data.clarity_source"
                :color="data.clarity_source === 'camera' ? 'success' : 'grey'"
                :prepend-icon="data.clarity_source === 'camera' ? 'mdi-camera' : 'mdi-sine-wave'"
                size="x-small"
                label
              >
                {{ data.clarity_source === 'camera' ? 'LIVE CAMERA' : 'SIMULATED' }}
              </v-chip>
            </div>
            <div class="text-h4 font-weight-bold" :style="{ color: clarityColor }">
              {{ data.turbidity_class ? data.turbidity_class.toUpperCase() : '—' }}
            </div>
            <div class="text-medium-emphasis text-body-2">
              <span v-if="data.clarity_source === 'camera'">
                Brightness {{ data.brightness }} · Debris {{ data.debris_count }}
              </span>
              <span v-else>Camera not feeding this value</span>
            </div>
            <v-progress-linear
              :model-value="clarityPercent"
              :color="clarityColor"
              class="mt-4"
              height="8"
              rounded
              bg-color="grey-darken-3"
            />
            <div class="d-flex justify-space-between text-caption text-medium-emphasis mt-1">
              <span>Clear</span>
              <span>Index: {{ data.clarity ?? '—' }}</span>
              <span>High turbidity</span>
            </div>
            <v-btn
              to="/camera"
              variant="text"
              size="small"
              class="mt-3 px-0"
              prepend-icon="mdi-camera"
            >
              View live feed
            </v-btn>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- last updated timestamp -->
    <div class="text-medium-emphasis text-caption text-right">
      Last updated: {{ lastUpdated }}
    </div>

  </v-container>
</template>

<script>
import axios from 'axios'

// use relative paths so this works whether served from localhost or the pi's ip
const API_BASE = ''

export default {
  name: 'Dashboard',

  data() {
    return {
      thresholds: { clarity: 1, conductivity: 800 },
      data: {},
      lastUpdated: '—',
      ws: null,
      thresholdInterval: null,
    }
  },

  computed: {
    conductivityPercent() {
      return Math.min((this.data.conductivity / 2000) * 100, 100)
    },

    // the clarity bar fills as the water approaches the "high turbidity" boundary
    clarityPercent() {
      if (this.data.clarity == null) return 0
      return Math.min((this.data.clarity / this.thresholds.clarity) * 100, 100)
    },

    conductivityColor() {
      if (!this.data.conductivity) return 'grey'
      if (this.data.conductivity > this.thresholds.conductivity) return '#EF5350'
      if (this.data.conductivity > this.thresholds.conductivity * 0.7) return '#FFA726'
      return '#66BB6A'
    },

    clarityColor() {
      const map = { clear: '#66BB6A', moderate: '#FFA726', high: '#EF5350' }
      return map[this.data.turbidity_class] ?? 'grey'
    },

    scoreColor() {
      const map = { low: 'success', medium: 'warning', high: 'error' }
      return map[this.data.pollution_score] ?? 'grey'
    }
  },

  mounted() {
    this.fetchThresholds()
    this.fetchInitialStatus()
    this.connectWebSocket()
    this.thresholdInterval = setInterval(this.fetchThresholds, 5000)
  },

  beforeUnmount() {
    if (this.ws) this.ws.close()
    clearInterval(this.thresholdInterval)
  },

  methods: {
    async fetchThresholds() {
      try {
        const res = await axios.get(`${API_BASE}/api/thresholds`)
        this.thresholds = res.data
      } catch (e) {
        console.error('failed to fetch thresholds', e)
      }
    },

    async fetchInitialStatus() {
      try {
        const res = await fetch(`${API_BASE}/api/status`)
        this.data = await res.json()
        this.updateTimestamp()
      } catch (e) {
        console.error('failed to fetch initial status', e)
      }
    },

    connectWebSocket() {
      // build ws url relative to whatever host is serving the page
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const wsUrl = `${protocol}//${window.location.host}/ws/live`
      this.ws = new WebSocket(wsUrl)

      this.ws.onmessage = (event) => {
        this.data = JSON.parse(event.data)
        this.updateTimestamp()
      }

      this.ws.onclose = () => {
        setTimeout(() => this.connectWebSocket(), 3000)
      }
    },

    updateTimestamp() {
      this.lastUpdated = new Date().toLocaleTimeString()
    }
  }
}
</script>