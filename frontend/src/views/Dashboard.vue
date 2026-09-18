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

    <!-- rain event banner -->
    <v-alert
      v-if="data.rain_event"
      type="warning"
      class="mb-6"
      icon="mdi-weather-rainy"
    >
      <strong>Rain Event Detected</strong> — high-frequency sampling active.
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

    <!-- sensor reading cards -->
    <v-row class="mb-4">
      <v-col cols="12" md="6">
        <v-card color="surface" rounded="lg">
          <v-card-text>
            <div class="text-medium-emphasis text-body-2 mb-2">Turbidity</div>
            <div class="text-h3 font-weight-bold" :style="{ color: turbidityColor }">
              {{ data.turbidity ?? '—' }}
            </div>
            <div class="text-medium-emphasis text-body-2">NTU</div>
            <v-progress-linear
              :model-value="turbidityPercent"
              :color="turbidityColor"
              class="mt-4"
              height="8"
              rounded
              bg-color="grey-darken-3"
            />
            <div class="d-flex justify-space-between text-caption text-medium-emphasis mt-1">
              <span>0</span>
              <span>Threshold: {{ thresholds.turbidity }} NTU</span>
              <span>150</span>
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="6">
        <v-card color="surface" rounded="lg">
          <v-card-text>
            <div class="text-medium-emphasis text-body-2 mb-2">Conductivity</div>
            <div class="text-h3 font-weight-bold" :style="{ color: conductivityColor }">
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
    </v-row>

    <!-- last updated timestamp -->
    <div class="text-medium-emphasis text-caption text-right">
      Last updated: {{ lastUpdated }}
    </div>

  </v-container>
</template>

<script>
import axios from 'axios'

export default {
  name: 'Dashboard',

  data() {
    return {
      thresholds: { turbidity: 50, conductivity: 800 },
      data: {},
      lastUpdated: '—',
      ws: null,
    }
  },

  computed: {
    turbidityPercent() {
      // cap bar at 150 NTU for display purposes
      return Math.min((this.data.turbidity / 150) * 100, 100)
    },

    conductivityPercent() {
      // cap bar at 2000 ppm for display purposes
      return Math.min((this.data.conductivity / 2000) * 100, 100)
    },

    turbidityColor() {
      if (!this.data.turbidity) return 'grey'
      if (this.data.turbidity > this.thresholds.turbidity) return '#EF5350'
      if (this.data.turbidity > this.thresholds.turbidity * 0.7) return '#FFA726'
      return '#66BB6A'
    },

    conductivityColor() {
      if (!this.data.conductivity) return 'grey'
      if (this.data.conductivity > this.thresholds.conductivity) return '#EF5350'
      if (this.data.conductivity > this.thresholds.conductivity * 0.7) return '#FFA726'
      return '#66BB6A'
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
  },

  beforeUnmount() {
    // clean up websocket when leaving the view
    if (this.ws) this.ws.close()
  },

  methods: {
    async fetchThresholds() {
      // load current thresholds from backend so dashboard reflects any settings changes
      try {
        const res = await axios.get('http://localhost:8000/api/thresholds')
        this.thresholds = res.data
      } catch (e) {
        console.error('failed to fetch thresholds', e)
      }
    },

    async fetchInitialStatus() {
      // fetch current sensor state on page load before websocket connects
      try {
        const res = await fetch('http://localhost:8000/api/status')
        this.data = await res.json()
        this.updateTimestamp()
      } catch (e) {
        console.error('failed to fetch initial status', e)
      }
    },

    connectWebSocket() {
      this.ws = new WebSocket('ws://localhost:8000/ws/live')

      this.ws.onmessage = (event) => {
        // update reactive data on each incoming reading
        this.data = JSON.parse(event.data)
        this.updateTimestamp()
      }

      this.ws.onclose = () => {
        // reconnect after 3 seconds if connection drops
        setTimeout(() => this.connectWebSocket(), 3000)
      }
    },

    updateTimestamp() {
      this.lastUpdated = new Date().toLocaleTimeString()
    }
  }
}
</script>