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

          <v-card-text v-if="events.length === 0" class="text-center text-medium-emphasis py-8">
            No diverter events recorded yet.
          </v-card-text>

          <v-list v-else bg-color="transparent">
            <v-list-item
              v-for="(event, i) in events"
              :key="i"
              :subtitle="event.message"
            >
              <template #prepend>
                <v-icon :color="eventColor(event)" class="mr-4">{{ eventIcon(event) }}</v-icon>
              </template>
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

// use relative paths so this works whether served from localhost or the pi's ip
const API_BASE = ''

export default {
  name: 'History',
  components: { apexchart: VueApexCharts },

  data() {
    return {
      events: [],
      readings: [],
      thresholds: { clarity: 1, conductivity: 800 },
    }
  },

  computed: {
    chartSeries() {
      const reversed = [...this.readings].reverse()
      return [
        {
          name: 'Conductivity (ppm)',
          data: reversed.map(r => ({ x: r.timestamp * 1000, y: r.conductivity }))
        },
        {
          name: 'Clarity index',
          data: reversed.map(r => ({ x: r.timestamp * 1000, y: r.clarity }))
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
        colors: ['#FFA726', '#00BCD4'],
        xaxis: {
          type: 'datetime',
          // show local time, ApexCharts defaults to UTC
          labels: { datetimeUTC: false, style: { colors: '#9e9e9e' } }
        },
        // two axes since conductivity (ppm) and the clarity index (0-2) are on very different scales
        yaxis: [
          {
            seriesName: 'Conductivity (ppm)',
            min: 0,
            title: { text: 'ppm', style: { color: '#9e9e9e' } },
            labels: { style: { colors: '#9e9e9e' }, formatter: v => Math.round(v) }
          },
          {
            seriesName: 'Clarity index',
            opposite: true,
            min: 0,
            max: 2,
            tickAmount: 4,
            title: { text: 'clarity index (1 = high turbidity)', style: { color: '#9e9e9e' } },
            labels: { style: { colors: '#9e9e9e' }, formatter: v => v.toFixed(1) }
          }
        ],
        annotations: {
          yaxis: [
            {
              y: this.thresholds.conductivity,
              yAxisIndex: 0,
              borderColor: '#FFA726',
              label: { text: 'Conductivity Threshold', style: { color: '#FFA726', background: 'transparent' } }
            },
            {
              y: this.thresholds.clarity,
              yAxisIndex: 1,
              borderColor: '#00BCD4',
              label: { text: 'High turbidity', style: { color: '#00BCD4', background: 'transparent' } }
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
    this.interval = setInterval(this.fetchData, 3000)
  },

  beforeUnmount() {
    clearInterval(this.interval)
  },

  methods: {
    async fetchData() {
      try {
        const [readingsRes, eventsRes, thresholdsRes] = await Promise.all([
          axios.get(`${API_BASE}/api/readings?limit=100`),
          axios.get(`${API_BASE}/api/events`),
          axios.get(`${API_BASE}/api/thresholds`)
        ])
        this.readings = readingsRes.data
        this.events = eventsRes.data
        this.thresholds = thresholdsRes.data
      } catch (e) {
        console.error('failed to fetch history data', e)
      }
    },

    eventIcon(event) {
      return event.event_type === 'DIVERTER_CLEARED' ? 'mdi-check-circle-outline' : 'mdi-alert-circle-outline'
    },

    eventColor(event) {
      return event.event_type === 'DIVERTER_CLEARED' ? 'success' : 'error'
    },

    formatTimestamp(ts) {
      return new Date(ts * 1000).toLocaleString()
    },

    async clearDatabase() {
      try {
        await axios.delete(`${API_BASE}/api/clear`)
        this.readings = []
        this.events = []
      } catch (e) {
        console.error('failed to clear database', e)
      }
    }
  }
}
</script>