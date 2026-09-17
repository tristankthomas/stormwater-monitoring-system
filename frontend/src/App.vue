<template>
  <v-app>
    <!-- top navigation bar -->
    <v-app-bar color="surface" elevation="2">
      <v-app-bar-title>
        <span class="text-primary font-weight-bold">Stormwater Monitoring System</span>
      </v-app-bar-title>

      <!-- live connection status indicator -->
      <template #append>
        <v-chip
          :color="connected ? 'success' : 'error'"
          size="small"
          class="mr-3"
          :prepend-icon="connected ? 'mdi-wifi' : 'mdi-wifi-off'"
        >
          {{ connected ? 'Live' : 'Disconnected' }}
        </v-chip>
      </template>
    </v-app-bar>

    <!-- side navigation -->
    <v-navigation-drawer permanent color="surface">
      <v-list nav>
        <v-list-item
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          :prepend-icon="item.icon"
          :title="item.title"
          rounded="lg"
          active-color="primary"
        />
      </v-list>
    </v-navigation-drawer>

    <!-- main content area -->
    <v-main>
      <router-view />
    </v-main>
  </v-app>
</template>

<script>
export default {
  name: 'App',

  data() {
    return {
      connected: false,
      navItems: [
        { to: '/',         icon: 'mdi-view-dashboard', title: 'Dashboard' },
        { to: '/history',  icon: 'mdi-chart-line',     title: 'History' },
        { to: '/camera',   icon: 'mdi-camera',          title: 'Camera' },
      ]
    }
  },

  mounted() {
    this.connectWebSocket()
  },

  methods: {
    connectWebSocket() {
      // open websocket connection and track status for the indicator
      this.ws = new WebSocket('ws://localhost:8000/ws/live')

      this.ws.onopen = () => {
        this.connected = true
      }

      this.ws.onclose = () => {
        this.connected = false
        // attempt reconnect after 3 seconds
        setTimeout(() => this.connectWebSocket(), 3000)
      }

      this.ws.onerror = () => {
        this.connected = false
      }
    }
  }
}
</script>