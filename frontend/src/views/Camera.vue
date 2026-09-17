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
          <v-card-text class="d-flex align-center justify-center" style="height: 400px;">
            <!-- placeholder until pi camera is connected -->
            <div class="text-center">
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
            <v-icon class="mr-2" color="primary">mdi-eye</v-icon>
            Visual Analysis
          </v-card-title>
          <v-divider />
          <v-card-text>
            <v-list bg-color="transparent">
              <v-list-item
                prepend-icon="mdi-water-opacity"
                title="Turbidity Detection"
                subtitle="OpenCV thresholding on water sample"
              />
              <v-list-item
                prepend-icon="mdi-trash-can-outline"
                title="Debris Detection"
                subtitle="Visible floating solids and litter"
              />
              <v-list-item
                prepend-icon="mdi-oil"
                title="Surface Sheen"
                subtitle="Hydrocarbon film detection"
              />
            </v-list>

            <v-alert type="info" variant="tonal" class="mt-4" density="compact">
              Camera analysis requires Raspberry Pi with CSI camera module attached.
            </v-alert>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

  </v-container>
</template>

<script>
export default {
  name: 'Camera'
}
</script>