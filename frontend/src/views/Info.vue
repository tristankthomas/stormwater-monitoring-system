<template>
  <v-container fluid class="pa-6" style="max-width: 1100px;">

    <!-- overview -->
    <v-card color="surface" rounded="lg" class="mb-4">
      <v-card-title class="pa-4 text-body-1 font-weight-bold">
        <v-icon class="mr-2" color="primary">mdi-information-outline</v-icon>
        How the system works
      </v-card-title>
      <v-divider />
      <v-card-text class="text-body-2">
        <p class="mb-3">
          The monitor sits at a stormwater drain outlet and watches for the first flush, the initial burst of
          runoff that carries most of the pollutants. Two sensors are read every two seconds and combined
          into a single pollution score. When the score reaches HIGH, the diverter activates so the polluted
          water can be kept out of the Yarra.
        </p>
        <v-row>
          <v-col cols="12" md="6">
            <div class="font-weight-bold mb-1">Conductivity (primary signal)</div>
            Measures dissolved salts and ions, which rise sharply in contaminated runoff. It is read from a
            probe through an ADS1115 converter and shown in ppm. Each probe needs its own calibration.
          </v-col>
          <v-col cols="12" md="6">
            <div class="font-weight-bold mb-1">Water clarity (secondary signal)</div>
            A camera looks at the water and its average brightness is turned into a clarity index. Darker
            water gives a higher index. It is a visual check, and it also responds to lighting changes.
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <!-- score calculation with live numbers -->
    <v-card color="surface" rounded="lg" class="mb-4">
      <v-card-title class="pa-4 text-body-1 font-weight-bold">
        <v-icon class="mr-2" color="primary">mdi-function-variant</v-icon>
        How the pollution score is calculated
      </v-card-title>
      <v-divider />
      <v-card-text>
        <div class="text-body-2 mb-4">
          Each signal is scaled so that 1.0 means exactly at its own limit. The score is the worse of the two,
          plus half of the other.
        </div>

        <v-row>
          <v-col cols="12" md="4">
            <div class="text-caption text-medium-emphasis">Conductivity as a fraction of its limit</div>
            <div class="font-weight-medium">c = conductivity / limit</div>
            <div class="text-body-2 text-medium-emphasis">
              = {{ fmt(data.conductivity) }} / {{ thresholds.conductivity }} =
              <strong class="text-high-emphasis">{{ fmt(scoreC) }}</strong>
            </div>
          </v-col>
          <v-col cols="12" md="4">
            <div class="text-caption text-medium-emphasis">Clarity index as a fraction of its limit</div>
            <div class="font-weight-medium">k = clarity index / limit</div>
            <div class="text-body-2 text-medium-emphasis">
              = {{ fmt(data.clarity) }} / {{ thresholds.clarity }} =
              <strong class="text-high-emphasis">{{ fmt(scoreK) }}</strong>
            </div>
          </v-col>
          <v-col cols="12" md="4">
            <div class="text-caption text-medium-emphasis">Combined score</div>
            <div class="font-weight-medium">score = max(c, k) + 0.5 × min(c, k)</div>
            <div class="text-body-2 text-medium-emphasis">
              = {{ fmt(Math.max(scoreC, scoreK)) }} + 0.5 × {{ fmt(Math.min(scoreC, scoreK)) }} =
              <strong class="text-high-emphasis">{{ data.pollution_value ?? '—' }}</strong>
            </div>
          </v-col>
        </v-row>
        <div class="text-caption text-medium-emphasis mt-2">These numbers are the live readings.</div>

        <v-divider class="my-4" />

        <div class="font-weight-bold text-body-2 mb-2">What the score means</div>
        <div class="d-flex flex-wrap ga-3 mb-3">
          <v-chip color="success" variant="tonal">LOW: below 0.5</v-chip>
          <v-chip color="warning" variant="tonal">MEDIUM: 0.5 to 1.0</v-chip>
          <v-chip color="error" variant="tonal">HIGH: 1.0 and above, diverter activates</v-chip>
        </div>
        <ul class="text-body-2 ps-5">
          <li>Either signal alone at its limit gives a score of 1.0, so it activates the diverter on its own.</li>
          <li>Two moderately elevated signals can combine to reach HIGH. For example, 0.7 and 0.7 gives 1.05.</li>
          <li>The score keeps rising past 1.0 the further the water is beyond its limits. It is not capped at 1.0.</li>
          <li>The limits are the conductivity threshold and the high turbidity point, both set on the Settings page.</li>
        </ul>
      </v-card-text>
    </v-card>

    <!-- event log and limits -->
    <v-card color="surface" rounded="lg">
      <v-card-title class="pa-4 text-body-1 font-weight-bold">
        <v-icon class="mr-2" color="primary">mdi-clipboard-text-clock-outline</v-icon>
        Event log and limitations
      </v-card-title>
      <v-divider />
      <v-card-text class="text-body-2">
        <p class="mb-3">
          The event log records only changes in the diverter. An activation entry states the cause and where
          each reading came from, and a cleared entry states how long the diverter was active.
        </p>
        <div class="font-weight-bold mb-1">Current limitations</div>
        <ul class="ps-5">
          <li>The conductivity calibration is pending, so readings are indicative.</li>
          <li>The clarity index measures darkness, not true turbidity, and depends on lighting.</li>
          <li>Debris detection is a rough indicator and does not affect the diverter.</li>
          <li>The score weighting is a first design that has not been tuned against real events.</li>
          <li>If a sensor is not available, a simulated value is shown and labelled as such.</li>
        </ul>
      </v-card-text>
    </v-card>

  </v-container>
</template>

<script>
import axios from 'axios'

// use relative paths so this works whether served from localhost or the pi's ip
const API_BASE = ''

export default {
  name: 'Info',

  data() {
    return {
      data: {},
      thresholds: { clarity: 1, conductivity: 800 },
      interval: null,
    }
  },

  computed: {
    // normalised inputs to the score, 1.0 = at its own limit
    scoreC() {
      return (this.data.conductivity ?? 0) / this.thresholds.conductivity
    },

    scoreK() {
      return (this.data.clarity ?? 0) / this.thresholds.clarity
    }
  },

  mounted() {
    this.refresh()
    this.interval = setInterval(this.refresh, 2000)
  },

  beforeUnmount() {
    clearInterval(this.interval)
  },

  methods: {
    fmt(v) {
      return v == null ? '—' : Number(v).toFixed(2)
    },

    async refresh() {
      try {
        const [status, thresholds] = await Promise.all([
          axios.get(`${API_BASE}/api/status`),
          axios.get(`${API_BASE}/api/thresholds`)
        ])
        this.data = status.data
        this.thresholds = thresholds.data
      } catch (e) {
        console.error('failed to fetch info page data', e)
      }
    }
  }
}
</script>
