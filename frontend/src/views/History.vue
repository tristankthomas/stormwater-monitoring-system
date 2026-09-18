<template>
  <v-container fluid class="pa-6">

    <v-row class="mb-4">
      <v-col cols="12">
        <v-card color="surface" rounded="lg">
          <v-card-title class="pa-4 text-body-1 font-weight-bold">
            <v-icon class="mr-2" color="primary">mdi-chart-line</v-icon>
            Sensor History
          </v-card-title>
          <v-divider />
          <v-card-text>
            <!-- apexcharts time series for turbidity and conductivity -->
            <apexchart
              type="line"
              height="300"
              :options="chartOptions"
              :series="chartSeries"
            />
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="12">
        <v-card color="surface" rounded="lg">
          <v-card-title class="pa-4 text-body-1 font-weight-bold d-flex align-center justify-space-between">
            <div>
              <v-icon class="mr-2" color="error">mdi-alert-circle</v-icon>
              Event Log
            </div>
            <v-btn
              color="error"
              variant="tonal"
              size="small"
              prepend-icon="mdi-delete"
              @click="clearDatabase"
            >
              Clear Database
            </v-btn>
          </v-card-title>
          <v-divider />

          <!-- empty state when no events have been logged yet -->
          <v-card-text v-if="events.length === 0" class="text-center text-medium-emphasis py-8">
            No threshold breach events recorded yet.
          </v-card-text>

          <v-list v-else bg-color="transparent">
            <v-list-item
              v-for="(event, i) in events"
              :key="i"
              :subtitle="event.message"
              :prepend-icon="'mdi-alert-circle-outline'"
              prepend-icon-color="error"
            >
              <template #title>
                <span class="text-caption text-medium-emphasis">
                  {{ formatTimestamp(event.timestamp) }}
                </span>
              </template>
            </v-list-item>
          </v-list>
        </v-card>
      </v-col>
    </v-row>

  </v-container>
</template>

<script>
import VueApexCharts from 'vue3-apexcharts'
import axios from 'axios'

export default {
  name: 'History',
  components: { apexchart: VueApexCharts },

  data() {
    return {
      events: [],
      readings: [],
      thresholds: { turbidity: 50, conductivity: 800 },
    }
  },

  computed: {
    chartSeries() {
      // reverse so chart shows oldest to newest left to right
      const reversed = [...this.readings].reverse()
      return [
        {
          name: 'Turbidity (NTU)',
          data: reversed.map(r => ({ x: r.timestamp * 1000, y: r.turbidity }))
        },
        {
          name: 'Conductivity (ppm)',
          data: reversed.map(r => ({ x: r.timestamp * 1000, y: r.conductivity }))
        }
      ]
    },

    chartOptions() {
      return {
        chart: {
          background: 'transparent',
          toolbar: { show: false },
          animations: { enabled: false }
        },
        theme: { mode: 'dark' },
        stroke: { curve: 'smooth', width: 2 },
        colors: ['#00BCD4', '#FFA726'],
        xaxis: {
          type: 'datetime',
          labels: { style: { colors: '#9e9e9e' } }
        },
        yaxis: {
          labels: { style: { colors: '#9e9e9e' } }
        },
        // threshold reference lines pulled from backend settings
        annotations: {
          yaxis: [
            {
              y: this.thresholds.turbidity,
              borderColor: '#EF5350',
              label: { text: 'Turbidity Threshold', style: { color: '#EF5350', background: 'transparent' } }
            },
            {
              y: this.thresholds.conductivity,
              borderColor: '#FFA726',
              label: { text: 'Conductivity Threshold', style: { color: '#FFA726', background: 'transparent' } }
            }
          ]
        },
        grid: { borderColor: '#1e2a3a' },
        legend: { labels: { colors: '#9e9e9e' } },
        tooltip: { theme: 'dark', x: { format: 'HH:mm:ss' } }
      }
    }
  },

  mounted() {
    this.fetchData()
    // refresh history and thresholds every 3 seconds
    this.interval = setInterval(this.fetchData, 3000)
  },

  beforeUnmount() {
    clearInterval(this.interval)
  },

  methods: {
    async fetchData() {
      try {
        const [readingsRes, eventsRes, thresholdsRes] = await Promise.all([
          axios.get('http://localhost:8000/api/readings?limit=100'),
          axios.get('http://localhost:8000/api/events'),
          axios.get('http://localhost:8000/api/thresholds')
        ])
        this.readings = readingsRes.data
        this.events = eventsRes.data
        this.thresholds = thresholdsRes.data
      } catch (e) {
        console.error('failed to fetch history data', e)
      }
    },

    formatTimestamp(ts) {
      return new Date(ts * 1000).toLocaleString()
    },

    async clearDatabase() {
      // wipe all data and refresh the view
      try {
        await axios.delete('http://localhost:8000/api/clear')
        this.readings = []
        this.events = []
      } catch (e) {
        console.error('failed to clear database', e)
      }
    }
  }
}
</script>