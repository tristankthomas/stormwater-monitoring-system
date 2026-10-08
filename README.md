<template>
  <v-container fluid class="pa-6">

    <!-- alert banner shown when diverter is active, with the reason(s) -->
    <v-alert
      v-if="data.diverter_active"
      type="error"
      prominent
      class="mb-6"
      icon="mdi-alert-circle"
    >
      <div><strong>Diverter Activated</strong> — stormwater is being diverted.</div>
      <div v-for="(cause, i) in data.causes" :key="i" class="text-body-2">{{ cause }}</div>
    </v-alert>

    <!-- top row: combined pollution score and what it means for the diverter -->
    <v-row class="mb-4">
      <v-col cols="12" md="6">
        <v-card color="surface" rounded="lg" height="100%">
          <v-card-text>
            <div class="text-medium-emphasis text-body-2 mb-2">Pollution Score</div>
            <div class="d-flex align-center mb-4">
              <v-chip
                :color="scoreColor"
                size="x-large"
                class="text-h6 font-weight-bold mr-4"
              >
                {{ data.pollution_score?.toUpperCase() ?? '—' }}
              </v-chip>
              <div>
                <div class="font-weight-bold" :style="{ fontSize: '2rem', lineHeight: 1.1 }">{{ data.pollution_value ?? '—' }}</div>
                <div class="text-caption text-medium-emphasis">diverter triggers at 1.0 or above</div>
              </div>
            </div>
            <!-- zoned bar: green below 0.5, amber 0.5 to 1.0, red from 1.0, marker shows the current score -->
            <div class="position-relative" style="height: 12px; border-radius: 6px; overflow: hidden; display: flex;">
              <div style="width: 25%; background: #66BB6A; opacity: 0.35;"></div>
              <div style="width: 25%; background: #FFA726; opacity: 0.35;"></div>
              <div style="width: 50%; background: #EF5350; opacity: 0.35;"></div>
            </div>
            <div
              class="position-relative"
              style="height: 0;"
            >
              <div
                :style="{
                  position: 'absolute', top: '-16px', width: '4px', height: '20px',
                  borderRadius: '2px', background: '#fff',
                  left: `calc(${scoreMarkerPercent}% - 2px)`
                }"
              ></div>
            </div>
            <div class="position-relative text-caption text-medium-emphasis mt-2" style="height: 18px;">
              <span style="position: absolute; left: 0;">0</span>
              <span style="position: absolute; left: 25%; transform: translateX(-50%);">0.5 medium</span>
              <span style="position: absolute; left: 50%; transform: translateX(-50%);">1.0 diverter</span>
              <span style="position: absolute; right: 0;">2.0+</span>
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="6">
        <v-card color="surface" rounded="lg" height="100%">
          <v-card-text>
            <div class="text-medium-emphasis text-body-2 mb-2">Diverter Status</div>
            <v-chip
              :color="data.diverter_active ? 'error' : 'success'"
              size="x-large"
              class="text-h6 font-weight-bold mb-4"
              :prepend-icon="data.diverter_active ? 'mdi-valve-open' : 'mdi-valve-closed'"
            >
              {{ data.diverter_active ? 'ACTIVE' : 'INACTIVE' }}
            </v-chip>
            <div v-if="data.diverter_active">
              <div v-for="(cause, i) in data.causes" :key="i" class="text-body-2">{{ cause }}</div>
            </div>
            <div v-else class="text-body-2 text-medium-emphasis">
              Monitoring. Activates when the combined score reaches HIGH.
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- sensor cards: conductivity first as the primary quantitative signal, camera clarity as the visual check -->
    <v-row class="mb-4">
      <v-col cols="12" md="6">
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
            <div class="font-weight-bold" :style="{ color: conductivityColor, fontSize: '3.5rem', lineHeight: 1.1 }">
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

      <v-col cols="12" md="6">
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
            <div class="font-weight-bold" :style="{ color: clarityColor, fontSize: '3.5rem', lineHeight: 1.1 }">
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

    <!-- how the score is worked out, using the live readings -->
    <v-card color="surface" rounded="lg" class="mb-4">
      <v-card-title class="pa-4 text-body-1 font-weight-bold">
        <v-icon class="mr-2" color="primary">mdi-function-variant</v-icon>
        How the pollution score is calculated
      </v-card-title>
      <v-divider />
      <v-card-text>
        <v-row>
          <v-col cols="12" md="4">
            <div class="text-caption text-medium-emphasis">Conductivity, as a fraction of its limit</div>
            <div class="font-weight-medium">c = conductivity / limit</div>
            <div class="text-body-2 text-medium-emphasis">
              = {{ fmt(data.conductivity) }} / {{ thresholds.conductivity }} =
              <strong class="text-high-emphasis">{{ fmt(scoreC) }}</strong>
            </div>
          </v-col>
          <v-col cols="12" md="4">
            <div class="text-caption text-medium-emphasis">Clarity index, as a fraction of its limit</div>
            <div class="font-weight-medium">k = clarity index / limit</div>
            <div class="text-body-2 text-medium-emphasis">
              = {{ fmt(data.clarity) }} / {{ thresholds.clarity }} =
              <strong class="text-high-emphasis">{{ fmt(scoreK) }}</strong>
            </div>
          </v-col>
          <v-col cols="12" md="4">
            <div class="text-caption text-medium-emphasis">Score: the worse signal plus half the other</div>
            <div class="font-weight-medium">score = max(c, k) + 0.5 × min(c, k)</div>
            <div class="text-body-2 text-medium-emphasis">
              = {{ fmt(Math.max(scoreC, scoreK)) }} + 0.5 × {{ fmt(Math.min(scoreC, scoreK)) }} =
              <strong class="text-high-emphasis">{{ data.pollution_value ?? '—' }}</strong>
            </div>
          </v-col>
        </v-row>
        <v-divider class="my-3" />
        <div class="text-body-2 text-medium-emphasis">
          A signal of 1.0 is exactly at its limit. The score is
          <span style="color: #66BB6A;">LOW</span> below 0.5,
          <span style="color: #FFA726;">MEDIUM</span> from 0.5 to 1.0 and
          <span style="color: #EF5350;">HIGH</span> from 1.0, and the diverter activates when it is HIGH.
          The score keeps rising past 1.0 the further the water is beyond its limits.
        </div>
      </v-card-text>
    </v-card>

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

    // bar spans 0 to 2, so the 1.0 trigger sits at the midpoint
    scoreMarkerPercent() {
      if (this.data.pollution_value == null) return 0
      return Math.min(this.data.pollution_value / 2, 1) * 100
    },

    // the two normalised inputs to the score (1.0 = at its own limit)
    scoreC() {
      return (this.data.conductivity ?? 0) / this.thresholds.conductivity
    },

    scoreK() {
      return (this.data.clarity ?? 0) / this.thresholds.clarity
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
    fmt(v) {
      return v == null ? '—' : Number(v).toFixed(2)
    },

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